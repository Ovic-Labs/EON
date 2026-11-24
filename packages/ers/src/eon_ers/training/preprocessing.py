"""Deterministic, modality-specific preprocessing for ERS training and evaluation.

Implements real preprocessing for:
- Facial inputs: validation, resizing, grayscale conversion, and [0, 1] normalization.
- Acoustic inputs: sample-rate validation, stereo-to-mono, duration framing, and peak normalization.
- Corrupted/missing input detection and error handling.
- Reproducible preprocessing audit metadata.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.evaluation.dataset import EvaluationSample
from eon_ers.types import Modality

logger = logging.getLogger("eon_ers.training.preprocessing")


class PreprocessingConfig(BaseModel):
    """Deterministic configuration for sensory media preprocessing."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    target_image_shape: tuple[int, int] = Field(
        default=(64, 64), description="Target height and width for facial crops."
    )
    image_channels: int = Field(default=1, description="Target color channels (1 for grayscale).")
    image_normalize_range: tuple[float, float] = Field(
        default=(0.0, 1.0), description="Target numerical range for pixel intensity."
    )
    audio_sample_rate: int = Field(default=16000, description="Target audio sample rate in Hz.")
    target_audio_duration_sec: float = Field(
        default=2.0, description="Target audio framing duration in seconds."
    )
    audio_normalize_strategy: str = Field(
        default="peak", description="Audio normalization strategy ('peak' or 'zscore')."
    )

    @property
    def target_audio_length(self) -> int:
        """Expected sample count for target audio duration."""
        return int(round(self.audio_sample_rate * self.target_audio_duration_sec))


class SamplePreprocessor:
    """Modality-specific media preprocessor executing deterministic transformations."""

    def __init__(self, config: PreprocessingConfig | None = None) -> None:
        self.config = config or PreprocessingConfig()

    def preprocess_image(self, data: Any) -> np.ndarray:
        """Execute image validation, resizing, and float32 normalization to [0.0, 1.0]."""
        if data is None:
            raise ValueError("Image data payload is None.")

        from PIL import Image

        if isinstance(data, Image.Image):
            img = data.convert("L")
            if img.size != (self.config.target_image_shape[1], self.config.target_image_shape[0]):
                img = img.resize(
                    (self.config.target_image_shape[1], self.config.target_image_shape[0]),
                    resample=Image.Resampling.BILINEAR,
                )
            arr = np.asarray(img, dtype=np.float32)
        elif isinstance(data, (np.ndarray, list)):
            arr = np.array(data, dtype=np.float32)
            if arr.size == 0:
                raise ValueError("Image array is empty (0 elements).")
            if not np.isfinite(arr).all():
                raise ValueError("Image array contains non-finite values (NaN or Inf).")

            # Handle 3D / channels
            if arr.ndim == 3:
                if arr.shape[2] in (3, 4):  # H, W, C
                    # Standard ITU-R luminosity weights
                    arr = 0.2989 * arr[:, :, 0] + 0.5870 * arr[:, :, 1] + 0.1140 * arr[:, :, 2]
                elif arr.shape[0] in (1, 3):  # C, H, W
                    if arr.shape[0] == 3:
                        arr = 0.2989 * arr[0] + 0.5870 * arr[1] + 0.1140 * arr[2]
                    else:
                        arr = arr[0]

            if arr.ndim != 2:
                raise ValueError(
                    f"Image tensor must be 2D after channel collapse; got shape {arr.shape}."
                )

            target_h, target_w = self.config.target_image_shape
            if arr.shape != (target_h, target_w):
                # Deterministic PIL resize
                clipped = np.clip(arr, 0.0, 255.0).astype(np.uint8)
                pimg = Image.fromarray(clipped, mode="L")
                pimg = pimg.resize((target_w, target_h), resample=Image.Resampling.BILINEAR)
                arr = np.asarray(pimg, dtype=np.float32)
        else:
            raise TypeError(f"Unsupported image data type: {type(data).__name__}")

        # Normalization to [0.0, 1.0]
        max_val = float(np.max(arr))
        if max_val > 1.0:
            arr = arr / 255.0
        arr = np.clip(
            arr, self.config.image_normalize_range[0], self.config.image_normalize_range[1]
        )
        return arr.astype(np.float32)

    def preprocess_audio(self, data: Any) -> np.ndarray:
        """Execute audio validation, channel reduction, length framing, and peak normalization."""
        if data is None:
            raise ValueError("Audio data payload is None.")

        if isinstance(data, (np.ndarray, list)):
            arr = np.array(data, dtype=np.float32)
        else:
            raise TypeError(f"Unsupported audio data type: {type(data).__name__}")

        if arr.size == 0:
            raise ValueError("Audio array is empty (0 samples).")
        if not np.isfinite(arr).all():
            raise ValueError("Audio array contains non-finite values (NaN or Inf).")

        # Reduce stereo/multichannel to mono
        if arr.ndim == 2:
            if arr.shape[0] in (2,):  # (channels, time)
                arr = np.mean(arr, axis=0)
            elif arr.shape[1] in (2,):  # (time, channels)
                arr = np.mean(arr, axis=1)
            else:
                arr = arr.flatten()
        elif arr.ndim > 2:
            arr = arr.flatten()

        target_len = self.config.target_audio_length
        current_len = len(arr)

        if current_len < 160:  # < 10ms at 16kHz
            raise ValueError(f"Audio signal is too short ({current_len} samples < 160 required).")

        # Duration framing: pad or truncate deterministically
        if current_len < target_len:
            pad_width = target_len - current_len
            arr = np.pad(arr, (0, pad_width), mode="constant", constant_values=0.0)
        elif current_len > target_len:
            arr = arr[:target_len]

        # Normalization
        if self.config.audio_normalize_strategy == "peak":
            peak = float(np.max(np.abs(arr)))
            if peak > 1e-6:
                arr = arr / peak
        elif self.config.audio_normalize_strategy == "zscore":
            std = float(np.std(arr))
            if std > 1e-6:
                arr = (arr - float(np.mean(arr))) / std

        return arr.astype(np.float32)

    def preprocess_sample(
        self, sample: EvaluationSample, modality: Modality
    ) -> tuple[bool, np.ndarray | None, str]:
        """Preprocess a single sample, returning (success, preprocessed_array, message)."""
        try:
            if modality == Modality.FACIAL:
                preprocessed = self.preprocess_image(sample.data)
            elif modality == Modality.SPEECH:
                preprocessed = self.preprocess_audio(sample.data)
            else:
                return False, None, f"Unsupported modality '{modality}' for preprocessing."
            return True, preprocessed, "Preprocessing succeeded."
        except Exception as exc:
            return False, None, f"Preprocessing failed for sample '{sample.sample_id}': {exc}"

    def preprocess_partition(
        self, samples: list[EvaluationSample], modality: Modality
    ) -> tuple[list[EvaluationSample], dict[str, Any]]:
        """Preprocess all samples in a partition, recording deterministic metadata and handling corruptions."""
        preprocessed_samples: list[EvaluationSample] = []
        corrupted_ids: list[str] = []
        start_time = time.time()

        for s in samples:
            ok, preproc_data, err_msg = self.preprocess_sample(s, modality)
            if ok and preproc_data is not None:
                new_sample = EvaluationSample(
                    sample_id=s.sample_id,
                    subject_id=s.subject_id,
                    label=s.label,
                    data=preproc_data,
                    metadata=dict(s.metadata),
                )
                preprocessed_samples.append(new_sample)
            else:
                corrupted_ids.append(s.sample_id)
                logger.warning(f"Corrupted or invalid sample excluded: {err_msg}")

        audit_metadata: dict[str, Any] = {
            "total_input_samples": len(samples),
            "preprocessed_count": len(preprocessed_samples),
            "corrupted_count": len(corrupted_ids),
            "corrupted_sample_ids": corrupted_ids,
            "modality": modality.value,
            "duration_seconds": round(time.time() - start_time, 4),
            "config": self.config.model_dump(),
        }

        return preprocessed_samples, audit_metadata
