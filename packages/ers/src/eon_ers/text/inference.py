"""Text affect model adapters supporting experimental lexical estimation and ONNX inference."""

from __future__ import annotations

import abc
import json
from pathlib import Path
from typing import Any

import numpy as np

from eon_ers.exceptions import ERSModelIntegrityError, ERSModelUnavailableError
from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.text.normalization import NormalizedText
from eon_ers.types import EmotionCategory, Modality, ModelState, TextSentiment


class BaseTextModelAdapter(abc.ABC):
    """Abstract interface for text affect and sentiment models."""

    @property
    @abc.abstractmethod
    def model_id(self) -> str:
        """Unique model identifier."""

    @property
    @abc.abstractmethod
    def model_version(self) -> str:
        """Semantic model version."""

    @property
    @abc.abstractmethod
    def is_available(self) -> bool:
        """Whether model weights/runtime are ready."""

    @property
    @abc.abstractmethod
    def is_experimental(self) -> bool:
        """Whether model is an uncalibrated lexical heuristic."""

    @property
    @abc.abstractmethod
    def is_validated(self) -> bool:
        """Whether model is empirically validated on external holdout benchmarks."""

    @property
    @abc.abstractmethod
    def model_state(self) -> ModelState:
        """Current qualification state."""

    @property
    def classes(self) -> list[str]:
        return [
            EmotionCategory.NEUTRAL.value,
            EmotionCategory.HAPPINESS.value,
            EmotionCategory.SADNESS.value,
            EmotionCategory.ANGER.value,
            EmotionCategory.FEAR.value,
            EmotionCategory.SURPRISE.value,
            EmotionCategory.DISGUST.value,
        ]

    @abc.abstractmethod
    def predict(
        self,
        normalized: NormalizedText,
        feature_vector: np.ndarray,
        lexical_cues: dict[str, float],
    ) -> tuple[dict[str, float], TextSentiment]:
        """Return (emotion_probabilities, distinct_textual_sentiment)."""


class ExperimentalTextAffectAdapter(BaseTextModelAdapter):
    """Experimental CPU-only lexical cue estimator explicitly marked unvalidated.

    Keeps textual sentiment signals visible for diagnostics without falsely certifying them as
    validated affect classifications.
    """

    def __init__(self, model_id: str = "ers-text-lexical-experimental-v1") -> None:
        self._model_id = model_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return "0.1.0-experimental"

    @property
    def is_available(self) -> bool:
        return True

    @property
    def is_experimental(self) -> bool:
        return True

    @property
    def is_validated(self) -> bool:
        return False

    @property
    def model_state(self) -> ModelState:
        return ModelState.MODEL_EXPERIMENTAL

    def predict(
        self,
        normalized: NormalizedText,
        feature_vector: np.ndarray,
        lexical_cues: dict[str, float],
    ) -> tuple[dict[str, float], TextSentiment]:
        scores = {
            EmotionCategory.NEUTRAL.value: 0.25,
            EmotionCategory.HAPPINESS.value: 0.1
            + 4.0 * lexical_cues.get("cue_happiness_density", 0.0),
            EmotionCategory.SADNESS.value: 0.1 + 4.0 * lexical_cues.get("cue_sadness_density", 0.0),
            EmotionCategory.ANGER.value: 0.1 + 4.0 * lexical_cues.get("cue_anger_density", 0.0),
            EmotionCategory.FEAR.value: 0.1 + 4.0 * lexical_cues.get("cue_fear_density", 0.0),
            EmotionCategory.SURPRISE.value: 0.1
            + 4.0 * lexical_cues.get("cue_surprise_density", 0.0),
            EmotionCategory.DISGUST.value: 0.1 + 4.0 * lexical_cues.get("cue_disgust_density", 0.0),
        }
        total = sum(scores.values())
        probs = {k: round(float(v / total), 4) for k, v in scores.items()}

        pos = lexical_cues.get("cue_happiness_density", 0.0)
        neg = (
            lexical_cues.get("cue_sadness_density", 0.0)
            + lexical_cues.get("cue_anger_density", 0.0)
            + lexical_cues.get("cue_fear_density", 0.0)
            + lexical_cues.get("cue_disgust_density", 0.0)
        )
        if pos > 0.0 and neg > 0.0:
            sentiment = TextSentiment.MIXED
        elif pos > 0.0:
            sentiment = TextSentiment.POSITIVE
        elif neg > 0.0:
            sentiment = TextSentiment.NEGATIVE
        else:
            sentiment = TextSentiment.NEUTRAL
        return probs, sentiment


class ONNXTextModelAdapter(BaseTextModelAdapter):
    """ONNX Runtime CPU inference adapter for trained text-affect feature vectors."""

    def __init__(
        self,
        model_path: str | Path,
        model_id: str = "ers-text-affect-cpu-v1",
        num_threads: int = 2,
        manifest: ModelManifest | None = None,
        validation_record: ModelValidationRecord | None = None,
    ) -> None:
        self._model_path = Path(model_path)
        self._model_id = model_id
        self._num_threads = num_threads
        self._manifest: ModelManifest | None = manifest
        if self._manifest is None:
            manifest_path = self._model_path.with_suffix(".json")
            if manifest_path.is_file():
                with open(manifest_path, encoding="utf-8") as f:
                    self._manifest = ModelManifest.model_validate(json.load(f))
        self._validation_record = validation_record
        if self._validation_record is None:
            val_path = self._model_path.with_suffix(".validation.json")
            if val_path.is_file():
                self._validation_record = ModelValidationRecord.load_from_file(val_path)
        self._session: Any | None = None
        self._state = ModelState.MODEL_MISSING
        self._load()

    def _load(self) -> None:
        if not self._model_path.exists():
            self._state = ModelState.MODEL_MISSING
            return
        self._state = ModelState.MODEL_LOADING
        try:
            if self._manifest is not None:
                self._session = ModelLoader.load_onnx_session(
                    manifest=self._manifest,
                    num_threads=self._num_threads,
                    expected_classes=self.classes,
                    expected_modality=Modality.TEXT,
                    supported_major_versions={1},
                )
            else:
                self._session, _ = ModelLoader.validate_and_load_onnx_weights(
                    artifact_path=self._model_path,
                    manifest=None,
                    num_threads=self._num_threads,
                    expected_classes=self.classes,
                    verify_manifest_checksum=False,
                )
        except (ERSModelIntegrityError, ERSModelUnavailableError):
            self._state = ModelState.MODEL_UNAVAILABLE
            raise
        except Exception:
            self._state = ModelState.MODEL_UNAVAILABLE
            return

        if (
            self._validation_record is not None
            and self._validation_record.is_validated
            and self._validation_record.verify_artifact_binding(str(self._model_path))
        ):
            self._state = ModelState.MODEL_LOADED_VALIDATED
        else:
            self._state = ModelState.MODEL_LOADED_UNVERIFIED

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def model_version(self) -> str:
        return self._manifest.version if self._manifest is not None else "1.0.0"

    @property
    def is_available(self) -> bool:
        return self._session is not None

    @property
    def is_experimental(self) -> bool:
        return False

    @property
    def is_validated(self) -> bool:
        return self._state == ModelState.MODEL_LOADED_VALIDATED

    @property
    def model_state(self) -> ModelState:
        return self._state

    def predict(
        self,
        normalized: NormalizedText,
        feature_vector: np.ndarray,
        lexical_cues: dict[str, float],
    ) -> tuple[dict[str, float], TextSentiment]:
        if self._session is None:
            raise RuntimeError("Text ONNX session is unavailable.")
        input_name = self._session.get_inputs()[0].name
        logits = np.asarray(
            self._session.run(None, {input_name: feature_vector.astype(np.float32)})[0][0],
            dtype=np.float64,
        )
        shifted = logits - np.max(logits)
        exp_scores = np.exp(shifted)
        probs_arr = exp_scores / np.sum(exp_scores)
        probs = {cls: float(probs_arr[i]) for i, cls in enumerate(self.classes)}
        pos_prob = probs.get("happiness", 0.0) + 0.5 * probs.get("surprise", 0.0)
        neg_prob = (
            probs.get("sadness", 0.0)
            + probs.get("anger", 0.0)
            + probs.get("fear", 0.0)
            + probs.get("disgust", 0.0)
        )
        if pos_prob >= 0.45 and pos_prob > neg_prob:
            sentiment = TextSentiment.POSITIVE
        elif neg_prob >= 0.45 and neg_prob > pos_prob:
            sentiment = TextSentiment.NEGATIVE
        else:
            sentiment = TextSentiment.NEUTRAL
        return probs, sentiment
