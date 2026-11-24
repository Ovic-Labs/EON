"""Reproducible feature extraction and zero-leakage feature normalization.

Guarantees:
- Modality-specific feature extraction (facial spatial pooling and acoustic spectral features).
- Feature tensor shape and finiteness validation.
- Zero-leakage feature normalization: normalizer parameters (mean, std) are fitted
  EXCLUSIVELY on the training partition.
- Validation and test partitions are transformed strictly using training parameters.
"""

from __future__ import annotations

import logging
import time

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.evaluation.dataset import EvaluationSample
from eon_ers.types import Modality

logger = logging.getLogger("eon_ers.training.features")


class FeatureConfig(BaseModel):
    """Auditable specification and parameters for feature extraction and normalization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    modality: str = Field(..., description="Target sensory modality.")
    feature_dim: int = Field(..., description="Dimensionality of feature vectors.")
    mean: list[float] = Field(
        default_factory=list, description="Fitted feature means from training set."
    )
    std: list[float] = Field(
        default_factory=list, description="Fitted feature std from training set."
    )
    is_fitted: bool = Field(
        default=False, description="Whether normalization parameters are fitted."
    )
    fitted_sample_count: int = Field(
        default=0, description="Training sample count used for fitting."
    )
    fitted_at: str = Field(default="", description="ISO 8601 timestamp when fitting occurred.")


class ZeroLeakageNormalizer:
    """Feature normalizer fitted strictly on training data with zero leakage into val or test."""

    def __init__(self, config: FeatureConfig | None = None) -> None:
        self.config = config
        self._mean: np.ndarray | None = (
            np.array(config.mean, dtype=np.float32) if config and config.mean else None
        )
        self._std: np.ndarray | None = (
            np.array(config.std, dtype=np.float32) if config and config.std else None
        )
        self.is_fitted: bool = config.is_fitted if config else False

    def fit(self, X_train: np.ndarray, modality: Modality = Modality.FACIAL) -> FeatureConfig:
        """Fit normalization parameters (mean and std) exclusively on the training feature matrix."""
        if X_train.ndim != 2:
            raise ValueError(
                f"Feature matrix must be 2D (samples, features); got shape {X_train.shape}."
            )
        if X_train.shape[0] == 0:
            raise ValueError("Cannot fit normalizer on an empty feature matrix.")
        if not np.isfinite(X_train).all():
            raise ValueError("Training feature matrix contains non-finite values (NaN or Inf).")

        mean = np.mean(X_train, axis=0).astype(np.float32)
        std = np.std(X_train, axis=0).astype(np.float32)

        # Prevent division by zero for invariant constant features
        std[std < 1e-6] = 1.0

        self._mean = mean
        self._std = std
        self.is_fitted = True

        self.config = FeatureConfig(
            modality=modality.value,
            feature_dim=int(X_train.shape[1]),
            mean=[float(x) for x in mean],
            std=[float(x) for x in std],
            is_fitted=True,
            fitted_sample_count=int(X_train.shape[0]),
            fitted_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        return self.config

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Transform feature matrix using parameters fitted strictly on training data."""
        if not self.is_fitted or self._mean is None or self._std is None:
            raise RuntimeError("Normalizer must be fitted on training data before transform.")
        if X.ndim != 2:
            raise ValueError(f"Input feature matrix must be 2D; got shape {X.shape}.")
        if X.shape[1] != len(self._mean):
            raise ValueError(
                f"Feature dimension mismatch: expected {len(self._mean)}, got {X.shape[1]}."
            )
        if not np.isfinite(X).all():
            raise ValueError("Input feature matrix contains non-finite values (NaN or Inf).")

        normalized = (X - self._mean) / self._std
        return normalized.astype(np.float32)

    def fit_transform(
        self, X_train: np.ndarray, modality: Modality = Modality.FACIAL
    ) -> np.ndarray:
        """Fit on training data and return transformed training features."""
        self.fit(X_train, modality=modality)
        return self.transform(X_train)


class FeatureExtractor:
    """Extracts fixed-length, deterministic feature vectors from preprocessed media."""

    def extract_facial_features(self, img: np.ndarray) -> np.ndarray:
        """Extract multi-scale spatial grid pooling features from a preprocessed image."""
        if img.ndim != 2:
            raise ValueError(f"Preprocessed facial image must be 2D; got {img.shape}.")
        h, w = img.shape
        grid_rows, grid_cols = 8, 8
        cell_h = h // grid_rows
        cell_w = w // grid_cols

        features: list[float] = []
        for r in range(grid_rows):
            for c in range(grid_cols):
                patch = img[r * cell_h : (r + 1) * cell_h, c * cell_w : (c + 1) * cell_w]
                features.append(float(np.mean(patch)))
                features.append(float(np.std(patch)))

        # 64 mean + 64 std = 128 dimensions
        vec = np.array(features, dtype=np.float32)
        if not np.isfinite(vec).all():
            raise ValueError("Extracted facial feature vector contains non-finite values.")
        return vec

    def extract_acoustic_features(self, audio: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """Extract spectral energy, envelope, and statistical features from preprocessed audio."""
        if audio.ndim != 1:
            raise ValueError(f"Preprocessed audio must be 1D; got {audio.shape}.")

        frame_len = 512
        hop_len = 256
        num_frames = (len(audio) - frame_len) // hop_len + 1
        if num_frames <= 0:
            frame_len = len(audio)
            hop_len = frame_len
            num_frames = 1

        energies: list[float] = []
        zcr_list: list[float] = []
        spectral_means: list[float] = []

        window = np.hanning(frame_len)
        for i in range(min(num_frames, 64)):
            start = i * hop_len
            frame = audio[start : start + frame_len]
            if len(frame) < frame_len:
                frame = np.pad(frame, (0, frame_len - len(frame)), mode="constant")
            frame = frame * window

            # Energy
            rms = float(np.sqrt(np.mean(frame**2) + 1e-8))
            energies.append(rms)

            # Zero crossing rate
            zcr = float(np.mean(np.abs(np.diff(np.sign(frame + 1e-8)))) / 2.0)
            zcr_list.append(zcr)

            # FFT magnitude spectrum
            fft_mag = np.abs(np.fft.rfft(frame))
            spec_mean = float(np.mean(fft_mag))
            spectral_means.append(spec_mean)

        # Pad features to fixed length
        target_frames = 32
        for flist in (energies, zcr_list, spectral_means):
            if len(flist) < target_frames:
                flist.extend([0.0] * (target_frames - len(flist)))
            elif len(flist) > target_frames:
                del flist[target_frames:]

        combined = energies + zcr_list + spectral_means
        # 32 + 32 + 32 = 96 dimensions; pad with global statistics to 128
        global_stats = [
            float(np.mean(audio)),
            float(np.std(audio)),
            float(np.max(audio)),
            float(np.min(audio)),
        ]
        # Pad up to 128 dimensions
        needed = 128 - len(combined) - len(global_stats)
        vec = np.array(combined + global_stats + [0.0] * max(0, needed), dtype=np.float32)
        if not np.isfinite(vec).all():
            raise ValueError("Extracted acoustic feature vector contains non-finite values.")
        return vec[:128]

    def extract_sample_features(self, sample: EvaluationSample, modality: Modality) -> np.ndarray:
        """Extract a 128-dimensional feature vector for a single sample."""
        if sample.data is None:
            raise ValueError(f"Sample '{sample.sample_id}' data payload is None.")

        if modality == Modality.FACIAL:
            return self.extract_facial_features(sample.data)
        elif modality == Modality.SPEECH:
            return self.extract_acoustic_features(sample.data)
        else:
            raise ValueError(f"Unsupported modality '{modality}'.")

    def extract_partition_matrix(
        self, samples: list[EvaluationSample], modality: Modality
    ) -> tuple[np.ndarray, list[str], list[str]]:
        """Extract 2D feature matrix X, ground-truth label list y, and sample ID list."""
        if not samples:
            raise ValueError("Cannot extract features from empty sample list.")

        X_rows: list[np.ndarray] = []
        labels: list[str] = []
        ids: list[str] = []

        for s in samples:
            feat = self.extract_sample_features(s, modality)
            X_rows.append(feat)
            labels.append(s.label)
            ids.append(s.sample_id)

        X = np.vstack(X_rows).astype(np.float32)
        return X, labels, ids
