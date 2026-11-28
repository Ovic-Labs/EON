"""Facial model adapters for inference execution in ERS."""

from __future__ import annotations

import abc
import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from eon_ers.exceptions import (
    ERSModelExecutionError,
    ERSModelIntegrityError,
    ERSModelUnavailableError,
)
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.types import EmotionCategory, Modality, ModelState

SUPPORTED_EMOTIONS = [
    EmotionCategory.NEUTRAL.value,
    EmotionCategory.HAPPINESS.value,
    EmotionCategory.SADNESS.value,
    EmotionCategory.ANGER.value,
    EmotionCategory.FEAR.value,
    EmotionCategory.SURPRISE.value,
    EmotionCategory.DISGUST.value,
]


class BaseFacialModelAdapter(abc.ABC):
    """Abstract provider-independent model adapter for facial emotion estimation."""

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
        """Whether the adapter has been empirically validated against affective benchmarks."""
        return False

    @property
    def model_state(self) -> ModelState:
        """Explicit model qualification state."""
        if not self.is_available:
            return ModelState.MODEL_UNAVAILABLE
        if self.is_experimental:
            return ModelState.MODEL_EXPERIMENTAL
        if self.is_validated:
            return ModelState.MODEL_LOADED_VALIDATED
        return ModelState.MODEL_LOADED_UNVERIFIED

    @abc.abstractmethod
    def predict(self, tensor: np.ndarray, evidence_features: dict[str, float]) -> dict[str, float]:
        """Execute inference and return probability distribution over supported emotions."""


class ONNXFacialModelAdapter(BaseFacialModelAdapter):
    """ONNX Runtime CPU execution adapter for local facial emotion models."""

    def __init__(
        self,
        model_path: str | None,
        model_id: str = "ers-facial-onnx-cpu-v1",
        model_version: str = "1.0.0",
        num_threads: int = 4,
    ) -> None:
        self._model_path = model_path
        self._model_id = model_id
        self._model_version = model_version
        self._num_threads = num_threads
        self._session: Any = None
        self._is_loaded = False
        self._last_inference_failed = False
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
                    expected_modality=Modality.FACIAL,
                    supported_major_versions={1},
                )
                self._is_loaded = True
                return
            except (ERSModelIntegrityError, ERSModelUnavailableError):
                self._is_loaded = False
                raise
            except Exception:
                self._is_loaded = False
                return

        # Fallback if no manifest exists: still enforce weight & smoke validation
        try:
            self._session, _ = ModelLoader.validate_and_load_onnx_weights(
                artifact_path=self._model_path,
                manifest=None,
                num_threads=self._num_threads,
                expected_classes=SUPPORTED_EMOTIONS,
                verify_manifest_checksum=False,
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
        # A manifest claiming VERIFIED is not sufficient alone without an empirical validation record
        if not self._is_loaded or not self._model_path:
            return False
        val_file = Path(self._model_path).with_suffix(".validation.json")
        if val_file.is_file():
            try:
                record = ModelValidationRecord.load_from_file(val_file)
                return record.is_approved_for(self._manifest)
            except Exception:
                return False
        return False

    @property
    def model_state(self) -> ModelState:
        if not self._model_path or not os.path.isfile(self._model_path):
            return ModelState.MODEL_MISSING
        if not self._is_loaded:
            return ModelState.MODEL_UNAVAILABLE
        if self._last_inference_failed:
            return ModelState.MODEL_INFERENCE_FAILED
        if self.is_validated:
            return ModelState.MODEL_LOADED_VALIDATED
        return ModelState.MODEL_LOADED_UNVERIFIED

    def predict(self, tensor: np.ndarray, evidence_features: dict[str, float]) -> dict[str, float]:
        if not self._is_loaded or self._session is None:
            raise ERSModelUnavailableError(
                f"ONNX facial model {self._model_id} is not loaded or weights are unavailable."
            )

        # Finiteness & numeric safety verification
        if not np.isfinite(tensor).all():
            self._last_inference_failed = True
            raise ERSModelExecutionError(
                "Input visual tensor contains non-finite numerical values (NaN or Inf)."
            )

        input_name = self._session.get_inputs()[0].name
        try:
            outputs = self._session.run(None, {input_name: tensor.astype(np.float32)})
        except Exception as exc:
            self._last_inference_failed = True
            raise ERSModelExecutionError(f"ONNX facial model execution failed: {exc}") from exc

        if not outputs or len(outputs) == 0:
            self._last_inference_failed = True
            raise ERSModelExecutionError("ONNX facial model returned empty output tensor list.")

        raw_logits = outputs[0].flatten()

        if not np.isfinite(raw_logits).all():
            self._last_inference_failed = True
            raise ERSModelExecutionError(
                "ONNX facial model output contains non-finite numerical values (NaN or Inf)."
            )

        if len(raw_logits) < len(SUPPORTED_EMOTIONS):
            self._last_inference_failed = True
            raise ERSModelExecutionError(
                f"ONNX output dimension mismatch: expected >= {len(SUPPORTED_EMOTIONS)} classes, got {len(raw_logits)}."
            )

        # Numerically stable softmax
        exp_logits = np.exp(raw_logits - np.max(raw_logits))
        sum_exp = np.sum(exp_logits)
        if sum_exp <= 0.0 or not np.isfinite(sum_exp):
            self._last_inference_failed = True
            raise ERSModelExecutionError("Numerical underflow/overflow during softmax computation.")

        probs = exp_logits / sum_exp

        result: dict[str, float] = {}
        for idx, cat in enumerate(SUPPORTED_EMOTIONS):
            p = float(probs[idx]) if idx < len(probs) else 0.0
            result[cat] = round(p, 4)

        total = sum(result.values())
        if total > 0.0:
            result = {k: round(v / total, 4) for k, v in result.items()}
        return result


class ExperimentalRegionalFeatureAdapter(BaseFacialModelAdapter):
    """Experimental regional contrast and morphology feature adapter.

    SCIENTIFIC RIGOR NOTICE:
    This adapter processes raw regional intensity contrast and gradients.
    It is NOT calibrated or empirically validated as a Facial Action Coding System (FACS)
    Action Unit classifier. It returns high-entropy, high-uncertainty distributions
    to avoid fabricating emotion estimates from unvalidated pixel contrast.
    """

    def __init__(
        self, model_id: str = "ers-regional-heuristic-v1", model_version: str = "1.0.0"
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

    def predict(self, tensor: np.ndarray, evidence_features: dict[str, float]) -> dict[str, float]:
        """Compute an uncalibrated baseline distribution reflecting epistemic uncertainty."""
        # Non-definitive baseline: equal uniform distribution across supported categories
        uniform_p = round(1.0 / len(SUPPORTED_EMOTIONS), 4)
        return {cat: uniform_p for cat in SUPPORTED_EMOTIONS}


# Backwards compatibility alias
HeuristicFacialFeatureAdapter = ExperimentalRegionalFeatureAdapter


class DeterministicTestFacialAdapter(BaseFacialModelAdapter):
    """Deterministic adapter for repeatable contract, unit, and failure testing."""

    def __init__(
        self,
        distribution: dict[str, float] | None = None,
        model_id: str = "test-facial-deterministic-v1",
        model_version: str = "1.0.0",
        simulate_unavailable: bool = False,
    ) -> None:
        self._distribution = distribution or {
            EmotionCategory.NEUTRAL.value: 0.70,
            EmotionCategory.HAPPINESS.value: 0.10,
            EmotionCategory.SADNESS.value: 0.05,
            EmotionCategory.ANGER.value: 0.05,
            EmotionCategory.FEAR.value: 0.03,
            EmotionCategory.SURPRISE.value: 0.05,
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

    def predict(self, tensor: np.ndarray, evidence_features: dict[str, float]) -> dict[str, float]:
        if self._simulate_unavailable:
            raise ERSModelUnavailableError("Deterministic test model is flagged unavailable")
        return dict(self._distribution)
