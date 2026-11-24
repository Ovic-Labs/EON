"""Speech acoustic model adapters for inference execution in ERS."""

from __future__ import annotations

import abc
import os
from typing import Any

import numpy as np

from eon_ers.exceptions import ERSModelUnavailableError
from eon_ers.types import EmotionCategory

SUPPORTED_EMOTIONS = [
    EmotionCategory.NEUTRAL.value,
    EmotionCategory.HAPPINESS.value,
    EmotionCategory.SADNESS.value,
    EmotionCategory.ANGER.value,
    EmotionCategory.FEAR.value,
    EmotionCategory.SURPRISE.value,
    EmotionCategory.DISGUST.value,
]


class BaseSpeechModelAdapter(abc.ABC):
    """Abstract provider-independent model adapter for acoustic speech emotion estimation."""

    @property
    @abc.abstractmethod
    def model_id(self) -> str:
        """Registered unique model identifier."""

    @property
    @abc.abstractmethod
    def model_version(self) -> str:
        """Model or adapter version string."""

    @property
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Whether model weights and runtime dependencies are available."""

    @abc.abstractmethod
    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        """Execute inference and return probability distribution over supported emotions."""


class ONNXSpeechModelAdapter(BaseSpeechModelAdapter):
    """ONNX Runtime CPU execution adapter for local speech emotion models."""

    def __init__(
        self,
        model_path: str | None,
        model_id: str = "speech-onnx-cpu-v1",
        model_version: str = "1.0.0",
        num_threads: int = 4,
    ) -> None:
        self._model_path = model_path
        self._model_id = model_id
        self._model_version = model_version
        self._num_threads = num_threads
        self._session: Any = None
        self._is_loaded = False
        self._init_session()

    def _init_session(self) -> None:
        if not self._model_path or not os.path.isfile(self._model_path):
            self._is_loaded = False
            return

        try:
            import onnxruntime as ort

            so = ort.SessionOptions()
            so.intra_op_num_threads = self._num_threads
            so.inter_op_num_threads = 1
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(
                self._model_path, sess_options=so, providers=["CPUExecutionProvider"]
            )
            self._is_loaded = True
        except Exception:
            self._is_loaded = False

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_available(self) -> bool:
        return self._is_loaded

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        if not self._is_loaded or self._session is None:
            raise ERSModelUnavailableError(
                f"ONNX speech model {self._model_id} is not loaded or weights are unavailable."
            )

        # Convert acoustic feature dictionary into standard 1D input feature vector
        feature_keys = [
            "f0_mean_hz",
            "f0_std_hz",
            "f0_range_hz",
            "energy_rms_mean",
            "energy_std",
            "energy_max",
            "zero_crossing_rate",
            "spectral_centroid_hz",
            "voice_activity_ratio",
            "mfcc_0",
            "mfcc_1",
            "mfcc_2",
        ]
        feat_vec = np.array([[features.get(k, 0.0) for k in feature_keys]], dtype=np.float32)

        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {input_name: feat_vec})
        raw_logits = outputs[0].flatten()

        exp_logits = np.exp(raw_logits - np.max(raw_logits))
        probs = exp_logits / np.sum(exp_logits)

        result: dict[str, float] = {}
        for idx, cat in enumerate(SUPPORTED_EMOTIONS):
            p = float(probs[idx]) if idx < len(probs) else 0.0
            result[cat] = round(p, 4)

        total = sum(result.values())
        if total > 0.0:
            result = {k: round(v / total, 4) for k, v in result.items()}
        return result


class AcousticFeatureProsodyAdapter(BaseSpeechModelAdapter):
    """Scientifically grounded prosody-to-affect classifier mapping acoustic dynamics.

    Evaluates F0 dynamics, RMS intensity, and spectral centroid without requiring
    text transcription or speech-to-text.
    """

    def __init__(
        self, model_id: str = "ers-prosody-acoustic-v1", model_version: str = "1.0.0"
    ) -> None:
        self._model_id = model_id
        self._model_version = model_version

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_available(self) -> bool:
        return True

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        f0_std = features.get("f0_std_hz", 0.0)
        energy_mean = features.get("energy_rms_mean", 0.0)
        energy_std = features.get("energy_std", 0.0)
        centroid = features.get("spectral_centroid_hz", 1000.0)
        zcr = features.get("zero_crossing_rate", 0.05)
        vad = features.get("voice_activity_ratio", 0.5)

        # Normalized feature indicators:
        # High pitch dynamism indicates arousal (Happiness or Anger or Fear)
        pitch_dynamic = float(np.clip(f0_std / 50.0, 0.0, 1.0))
        # High energy indicates vocal intensity
        energy_high = float(np.clip(energy_mean * 12.0, 0.0, 1.0))
        # High centroid indicates vocal sharpness / brightness
        spectral_sharp = float(np.clip((centroid - 800.0) / 2500.0, 0.0, 1.0))
        # Low energy and flat pitch indicate sadness / subdued affect
        low_activation = float(np.clip(1.0 - (energy_high * 0.7 + pitch_dynamic * 0.3), 0.0, 1.0))

        # Logit activations
        scores = {
            EmotionCategory.NEUTRAL.value: 0.20
            + 0.50 * (1.0 - pitch_dynamic) * (1.0 - abs(energy_high - 0.3)),
            EmotionCategory.HAPPINESS.value: 0.10
            + 0.45 * pitch_dynamic
            + 0.35 * energy_high
            + 0.20 * spectral_sharp,
            EmotionCategory.SADNESS.value: 0.10 + 0.65 * low_activation + 0.25 * (1.0 - vad),
            EmotionCategory.ANGER.value: 0.10
            + 0.55 * energy_high
            + 0.35 * spectral_sharp
            + 0.10 * (1.0 - pitch_dynamic),
            EmotionCategory.FEAR.value: 0.05
            + 0.45 * pitch_dynamic
            + 0.35 * zcr * 8.0
            + 0.20 * spectral_sharp,
            EmotionCategory.SURPRISE.value: 0.05 + 0.55 * pitch_dynamic + 0.30 * energy_std * 8.0,
            EmotionCategory.DISGUST.value: 0.05
            + 0.40 * low_activation
            + 0.20 * (1.0 - spectral_sharp),
        }

        vals = np.array(list(scores.values()), dtype=np.float32)
        exp_vals = np.exp(vals * 2.5)
        probs = exp_vals / np.sum(exp_vals)

        result = {cat: round(float(probs[i]), 4) for i, cat in enumerate(scores.keys())}
        return result


class DeterministicTestSpeechAdapter(BaseSpeechModelAdapter):
    """Deterministic adapter for repeatable speech contract and failure testing."""

    def __init__(
        self,
        distribution: dict[str, float] | None = None,
        model_id: str = "test-speech-deterministic-v1",
        model_version: str = "1.0.0",
        simulate_unavailable: bool = False,
    ) -> None:
        self._distribution = distribution or {
            EmotionCategory.NEUTRAL.value: 0.65,
            EmotionCategory.HAPPINESS.value: 0.15,
            EmotionCategory.SADNESS.value: 0.05,
            EmotionCategory.ANGER.value: 0.05,
            EmotionCategory.FEAR.value: 0.04,
            EmotionCategory.SURPRISE.value: 0.04,
            EmotionCategory.DISGUST.value: 0.02,
        }
        self._model_id = model_id
        self._model_version = model_version
        self._simulate_unavailable = simulate_unavailable

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._model_version

    @property
    def is_available(self) -> bool:
        return not self._simulate_unavailable

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        if self._simulate_unavailable:
            raise ERSModelUnavailableError("Deterministic test speech model is flagged unavailable")
        return dict(self._distribution)
