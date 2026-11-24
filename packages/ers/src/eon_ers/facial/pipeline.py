"""Facial expression analysis pipeline orchestrator for ERS."""

from __future__ import annotations

import time

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.facial.adapters import (
    BaseFacialModelAdapter,
    HeuristicFacialFeatureAdapter,
    ONNXFacialModelAdapter,
)
from eon_ers.facial.features import FacialFeatureExtractor
from eon_ers.facial.preprocessing import FacialPreprocessor
from eon_ers.quality.face_quality import FaceQualityEvaluator
from eon_ers.types import EmotionCategory, Modality, ObservationStatus, QualityGrade


class FacialPipeline:
    """Executes the full 12-stage facial expression processing pipeline."""

    def __init__(
        self,
        config: ERSConfig,
        model_adapter: BaseFacialModelAdapter | None = None,
    ) -> None:
        self.config = config
        self.quality_evaluator = FaceQualityEvaluator(
            min_resolution=config.min_face_resolution,
            max_dimension=config.max_image_dimension,
            blur_threshold=config.blur_threshold,
            min_brightness=config.min_brightness,
        )
        self.preprocessor = FacialPreprocessor(target_size=(64, 64))
        self.feature_extractor = FacialFeatureExtractor()

        # Initialize configured model adapter
        if model_adapter is not None:
            self.model_adapter = model_adapter
        elif config.facial_model_path:
            self.model_adapter = ONNXFacialModelAdapter(
                model_path=config.facial_model_path,
                model_id=config.facial_model_id,
                num_threads=config.num_threads,
            )
        else:
            # High-fidelity FACS Action Unit feature adapter
            self.model_adapter = HeuristicFacialFeatureAdapter(model_id="ers-facs-heuristic-v1")

    def process(self, inp: ERSInput) -> EmotionObservation:
        """Execute facial expression processing pipeline on sensory input."""
        start_time = time.perf_counter()
        limitations: list[str] = [
            "Epistemic modesty: Facial signals represent observable expressions, not verified internal subjective feelings."
        ]

        # 1. Image payload validation
        if inp.image_payload is None:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations={},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=["No image payload supplied in input envelope."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        # 2. Quality evaluation & decoding
        quality, pil_img = self.quality_evaluator.evaluate(inp.image_payload)

        # If image cannot be decoded or is unusable
        if pil_img is None or quality.grade == QualityGrade.UNUSABLE:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations={"quality_reasons": quality.reasons},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations + quality.reasons,
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        if not quality.is_acceptable:
            limitations.extend(quality.reasons)

        # 3. Face presence & features
        # Compute features from image
        evidence_features = self.feature_extractor.extract_features(pil_img)
        evidence_features.update(quality.metrics)

        # Check model availability
        if not self.model_adapter.is_available:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations=evidence_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations + ["Configured model adapter weights are unavailable."],
                status=ObservationStatus.MODEL_UNAVAILABLE,
                is_definitive_claim=False,
            )

        # 4. Model inference
        tensor = self.preprocessor.preprocess(pil_img)
        try:
            probabilities = self.model_adapter.predict(tensor, evidence_features)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations=evidence_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations + [f"Model inference failed: {exc}"],
                status=ObservationStatus.FAILED,
                is_definitive_claim=False,
            )

        # 5. Calculate confidence and uncertainty
        probs_array = np.array(list(probabilities.values()), dtype=np.float64)
        dominant_cat = max(probabilities.items(), key=lambda item: item[1])[0]
        raw_confidence = float(probabilities[dominant_cat])

        # Confidence attenuated by signal quality
        confidence = float(np.clip(raw_confidence * quality.score, 0.0, 1.0))

        # Normalized Shannon entropy for uncertainty: H = -sum(p * log(p)) / log(K)
        k = len(probabilities)
        clean_probs = probs_array[probs_array > 1e-12]
        entropy = -np.sum(clean_probs * np.log(clean_probs))
        max_entropy = np.log(k) if k > 1 else 1.0
        normalized_entropy = float(np.clip(entropy / max_entropy, 0.0, 1.0))

        # Margin uncertainty: 1 - (top1 - top2)
        sorted_probs = np.sort(probs_array)[::-1]
        margin = (
            float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else sorted_probs[0]
        )
        margin_uncertainty = 1.0 - margin

        # Composite uncertainty: blend of entropy, margin, and quality deficit
        uncertainty = float(
            np.clip(
                0.5 * normalized_entropy + 0.3 * margin_uncertainty + 0.2 * (1.0 - quality.score),
                0.0,
                1.0,
            )
        )

        # Abstention evaluation
        status = ObservationStatus.OK
        if (
            confidence < self.config.confidence_threshold
            or uncertainty > self.config.uncertainty_threshold
        ):
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            limitations.append(
                f"Low confidence ({confidence:.2f} < {self.config.confidence_threshold}) or high uncertainty ({uncertainty:.2f} > {self.config.uncertainty_threshold})."
            )

        if quality.grade == QualityGrade.DEGRADED:
            status = ObservationStatus.DEGRADED

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # 6. Ephemeral media scrubbing
        inp.scrub_media_payload()

        return EmotionObservation(
            observation_id=inp.observation_id,
            timestamp=inp.timestamp,
            modality=Modality.FACIAL,
            expression_observations=evidence_features,
            emotion_probabilities=probabilities,
            dominant_estimate=dominant_cat,
            confidence=round(confidence, 4),
            uncertainty=round(uncertainty, 4),
            quality_score=round(quality.score, 4),
            model_id=self.model_adapter.model_id,
            model_version=self.model_adapter.model_version,
            processing_latency_ms=round(latency_ms, 2),
            limitations=limitations,
            status=status,
            is_definitive_claim=False,
        )
