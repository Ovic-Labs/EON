"""Speech acoustic model adapters for inference execution in ERS."""

from __future__ import annotations

import abc
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from eon_ers.exceptions import ERSModelIntegrityError, ERSModelUnavailableError
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
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

    @property
    def is_experimental(self) -> bool:
        """Whether the adapter relies on uncalibrated experimental heuristics."""
        return False

    @property
    def is_validated(self) -> bool:
        """Whether the adapter has been empirically validated against affective speech benchmarks."""
        return False

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
        model_id: str = "ers-speech-onnx-cpu-v1",
        model_version: str = "1.0.0",
        num_threads: int = 4,
    ) -> None:
        self._model_path = model_path
        self._model_id = model_id
        self._model_version = model_version
        self._num_threads = num_threads
        self._session: Any = None
        self._is_loaded = False
        self._manifest: ModelManifest | None = None
        self._init_session()

    def _init_session(self) -> None:
        if not self._model_path or not os.path.isfile(self._model_path):
            self._is_loaded = False
            return

        manifest_path = Path(self._model_path).with_suffix(".json")
        if manifest_path.is_file():
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    data = json.load(f)
                self._manifest = ModelManifest.model_validate(data)
                self._session = ModelLoader.load_onnx_session(
                    self._manifest,
                    num_threads=self._num_threads,
                    expected_classes=SUPPORTED_EMOTIONS,
                )
                self._is_loaded = True
                return
            except (ERSModelIntegrityError, ERSModelUnavailableError):
                self._is_loaded = False
                raise
            except Exception:
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

    @property
    def is_experimental(self) -> bool:
        return False

    @property
    def is_validated(self) -> bool:
        return (
            self._manifest.validation_status.upper() == "VERIFIED"
            if self._manifest is not None
            else False
        )

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        if not self._is_loaded or self._session is None:
            raise ERSModelUnavailableError(
                f"ONNX speech model {self._model_id} is not loaded or weights are unavailable."
            )

        # Convert acoustic feature dictionary into standard 12-dim input vector
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


class ExperimentalAcousticProsodyAdapter(BaseSpeechModelAdapter):
    """Experimental acoustic prosody heuristic adapter.

    SCIENTIFIC RIGOR NOTICE:
    This adapter evaluates acoustic feature heuristics (pitch dynamism, intensity).
    It is NOT calibrated or empirically validated as an acoustic emotion classifier.
    It returns uncalibrated baseline distributions to avoid fabricating emotion classifications
    from unvalidated prosodic equations.
    """

    def __init__(
        self, model_id: str = "ers-prosody-experimental-v1", model_version: str = "1.0.0"
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

    @property
    def is_experimental(self) -> bool:
        return True

    @property
    def is_validated(self) -> bool:
        return False

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        """Compute an uncalibrated baseline distribution reflecting epistemic uncertainty."""
        uniform_p = round(1.0 / len(SUPPORTED_EMOTIONS), 4)
        return {cat: uniform_p for cat in SUPPORTED_EMOTIONS}


# Backwards compatibility alias
AcousticFeatureProsodyAdapter = ExperimentalAcousticProsodyAdapter


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

    @property
    def is_experimental(self) -> bool:
        return False

    @property
    def is_validated(self) -> bool:
        return True

    def predict(
        self, signal: np.ndarray, sample_rate: int, features: dict[str, float]
    ) -> dict[str, float]:
        if self._simulate_unavailable:
            raise ERSModelUnavailableError("Deterministic test speech model is flagged unavailable")
        return dict(self._distribution)
