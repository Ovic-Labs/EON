"""Textual sentiment & affect analysis pipeline orchestrator for ERS."""

from __future__ import annotations

import time
from typing import Any

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.text.inference import (
    BaseTextModelAdapter,
    ExperimentalTextAffectAdapter,
    ONNXTextModelAdapter,
)
from eon_ers.text.normalization import TextNormalizer
from eon_ers.text.tokenization import TextTokenizer
from eon_ers.types import (
    EmotionCategory,
    InputQualityStatus,
    Modality,
    ModelState,
    ObservationStatus,
    TextSentiment,
)


class TextPipeline:
    """Executes UTF-8 validation, normalization, tokenization, and text affect inference."""

    def __init__(
        self,
        config: ERSConfig,
        model_adapter: BaseTextModelAdapter | None = None,
    ) -> None:
        self.config = config
        self.normalizer = TextNormalizer(max_length=config.max_text_length)
        self.tokenizer = TextTokenizer(feature_dim=64)
        if model_adapter is not None:
            self.model_adapter = model_adapter
        elif config.text_model_path:
            self.model_adapter = ONNXTextModelAdapter(
                model_path=config.text_model_path,
                model_id=config.text_model_id,
                num_threads=config.num_threads,
            )
        else:
            self.model_adapter = ExperimentalTextAffectAdapter(
                model_id="ers-text-lexical-experimental-v1"
            )

    def process(self, inp: ERSInput) -> EmotionObservation:
        """Analyze text payload and return uncertainty-aware `EmotionObservation`."""
        start_time = time.perf_counter()
        limitations: list[str] = [
            "Epistemic modesty: Textual sentiment reflects linguistic surface cues, not verified speaker feelings or facial/vocal expression."
        ]

        normalized = self.normalizer.normalize(inp.text_payload)
        if not normalized.is_valid:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            reason = normalized.rejection_reason or "Invalid or empty text payload."
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.TEXT,
                expression_observations={
                    "text_sentiment": TextSentiment.UNKNOWN.value,
                    "rejection_reason": reason,
                },
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=round(latency_ms, 2),
                limitations=limitations + [reason],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                input_quality=InputQualityStatus.UNUSABLE,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                insufficient_evidence_reason=reason,
                is_definitive_claim=False,
            )

        tok_meta, feat_vec = self.tokenizer.tokenize(normalized.text)
        # Do NOT store raw text inside expression_observations to uphold zero plaintext PII retention
        obs_features: dict[str, Any] = {
            **tok_meta.lexical_cues,
            "char_length": float(normalized.char_length),
            "word_count": float(normalized.word_count),
            "has_non_ascii": bool(normalized.has_non_ascii),
            "exclamation_count": float(normalized.exclamation_count),
            "question_count": float(normalized.question_count),
            "uppercase_ratio": normalized.uppercase_ratio,
        }
        quality_score = round(min(1.0, 0.4 + 0.15 * min(4, normalized.word_count)), 4)

        if self.model_adapter.is_experimental:
            limitations.append(
                "Adapter uses uncalibrated lexical heuristics; not empirically validated for emotion classification."
            )

        if not self.model_adapter.is_available:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.TEXT,
                expression_observations=obs_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality_score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=round(latency_ms, 2),
                limitations=limitations + ["Configured text affect model adapter is unavailable."],
                status=ObservationStatus.MODEL_UNAVAILABLE,
                input_quality=InputQualityStatus.ACCEPTABLE,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                insufficient_evidence_reason="Configured text affect model adapter is unavailable.",
                is_definitive_claim=False,
            )

        try:
            probabilities, sentiment = self.model_adapter.predict(
                normalized, feat_vec, tok_meta.lexical_cues
            )
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.TEXT,
                expression_observations=obs_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality_score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=round(latency_ms, 2),
                limitations=limitations + [f"Text model inference failed: {exc}"],
                status=ObservationStatus.FAILED,
                input_quality=InputQualityStatus.ACCEPTABLE,
                model_state=ModelState.MODEL_INFERENCE_FAILED,
                is_validated=False,
                insufficient_evidence_reason=f"Text model inference failed: {exc}",
                is_definitive_claim=False,
            )

        obs_features["text_sentiment"] = sentiment.value
        probs_array = np.array(list(probabilities.values()), dtype=np.float64)
        raw_dominant = max(probabilities.items(), key=lambda it: it[1])[0]
        raw_confidence = float(probabilities[raw_dominant])
        confidence = float(np.clip(raw_confidence * quality_score, 0.0, 1.0))

        k = len(probabilities)
        clean_probs = probs_array[probs_array > 1e-12]
        entropy = -np.sum(clean_probs * np.log(clean_probs))
        norm_entropy = float(np.clip(entropy / (np.log(k) if k > 1 else 1.0), 0.0, 1.0))
        sorted_probs = np.sort(probs_array)[::-1]
        margin = (
            float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else sorted_probs[0]
        )
        uncertainty = float(
            np.clip(
                0.5 * norm_entropy + 0.3 * (1.0 - margin) + 0.2 * (1.0 - quality_score), 0.0, 1.0
            )
        )

        insufficient_reason: str | None = None
        if not self.model_adapter.is_validated or self.model_adapter.is_experimental:
            status = ObservationStatus.MODEL_UNVALIDATED
            dominant_cat = EmotionCategory.UNKNOWN.value
            confidence = 0.0
            uncertainty = 1.0
            insufficient_reason = "Text model is unvalidated; discrete emotion claims suppressed."
            limitations.append(insufficient_reason)
        elif (
            confidence < self.config.confidence_threshold
            or uncertainty > self.config.uncertainty_threshold
        ):
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            insufficient_reason = (
                f"Low text confidence ({confidence:.2f}) or high uncertainty ({uncertainty:.2f})."
            )
            limitations.append(insufficient_reason)
            confidence = 0.0
            uncertainty = 1.0
        else:
            status = ObservationStatus.OK
            dominant_cat = raw_dominant

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        inp.scrub_media_payload()

        return EmotionObservation(
            observation_id=inp.observation_id,
            timestamp=inp.timestamp,
            modality=Modality.TEXT,
            expression_observations=obs_features,
            emotion_probabilities=probabilities,
            dominant_estimate=dominant_cat,
            confidence=round(confidence, 4),
            uncertainty=round(uncertainty, 4),
            quality_score=quality_score,
            model_id=self.model_adapter.model_id,
            model_version=self.model_adapter.model_version,
            processing_latency_ms=round(latency_ms, 2),
            limitations=limitations,
            status=status,
            input_quality=InputQualityStatus.ACCEPTABLE,
            model_state=self.model_adapter.model_state,
            is_validated=self.model_adapter.is_validated,
            raw_confidence=round(raw_confidence, 4),
            insufficient_evidence_reason=insufficient_reason,
            is_definitive_claim=False,
        )
