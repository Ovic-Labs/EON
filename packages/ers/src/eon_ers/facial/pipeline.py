"""Facial expression analysis pipeline orchestrator for ERS."""

from __future__ import annotations

import time

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.facial.adapters import (
    BaseFacialModelAdapter,
    ExperimentalRegionalFeatureAdapter,
    ONNXFacialModelAdapter,
)
from eon_ers.facial.detection import (
    BaseFaceDetector,
    FaceDetectionStatus,
    HeuristicFaceDetector,
)
from eon_ers.facial.features import ExperimentalRegionalFeatureExtractor
from eon_ers.facial.landmarks import BaseLandmarkDetector, HeuristicLandmarkDetector
from eon_ers.facial.preprocessing import FacialPreprocessor
from eon_ers.quality.face_quality import FaceQualityEvaluator
from eon_ers.types import (
    EmotionCategory,
    InputQualityStatus,
    Modality,
    ModelState,
    ObservationStatus,
    QualityGrade,
)


class FacialPipeline:
    """Executes the full 12-stage facial expression processing pipeline."""

    def __init__(
        self,
        config: ERSConfig,
        model_adapter: BaseFacialModelAdapter | None = None,
        face_detector: BaseFaceDetector | None = None,
        landmark_detector: BaseLandmarkDetector | None = None,
    ) -> None:
        self.config = config
        self.quality_evaluator = FaceQualityEvaluator(
            min_resolution=config.min_face_resolution,
            max_dimension=config.max_image_dimension,
            blur_threshold=config.blur_threshold,
            min_brightness=config.min_brightness,
            max_payload_bytes=config.max_image_bytes,
        )
        self.face_detector = face_detector or HeuristicFaceDetector()
        self.landmark_detector = landmark_detector or HeuristicLandmarkDetector()
        self.preprocessor = FacialPreprocessor(target_size=(64, 64))
        self.feature_extractor = ExperimentalRegionalFeatureExtractor()

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
            self.model_adapter = ExperimentalRegionalFeatureAdapter(
                model_id="ers-regional-heuristic-v1"
            )

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
                input_quality=InputQualityStatus.UNUSABLE,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                is_definitive_claim=False,
            )

        # 2. Quality evaluation & decoding
        quality, pil_img = self.quality_evaluator.evaluate(inp.image_payload)

        if quality.grade in (QualityGrade.EXCELLENT, QualityGrade.ACCEPTABLE):
            input_quality = InputQualityStatus.ACCEPTABLE
        elif quality.grade == QualityGrade.DEGRADED:
            input_quality = InputQualityStatus.DEGRADED
        else:
            input_quality = InputQualityStatus.UNUSABLE

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
                input_quality=InputQualityStatus.UNUSABLE,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                is_definitive_claim=False,
            )

        if not quality.is_acceptable:
            limitations.extend(quality.reasons)

        # 3. Face detection & boundary validation
        detect_res = self.face_detector.detect(pil_img)
        if detect_res.status == FaceDetectionStatus.NO_FACE_DETECTED:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.FACIAL,
                expression_observations={"face_detection_status": detect_res.status.value},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations + ["No face detected in sensory frame."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                input_quality=InputQualityStatus.UNUSABLE,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                is_definitive_claim=False,
            )

        if detect_res.status == FaceDetectionStatus.MULTIPLE_FACES_DETECTED:
            limitations.append("Multiple faces detected in sensory frame; primary face selected.")

        primary_box = detect_res.primary_face
        if primary_box is not None and primary_box.is_partial_boundary:
            limitations.append("Primary face lies near frame boundary (partial/clipped region).")

        # 4. Landmark detection
        landmark_res = None
        if primary_box is not None:
            landmark_res = self.landmark_detector.detect_landmarks(pil_img, primary_box)

        # 5. Feature extraction
        evidence_features = self.feature_extractor.extract_features(pil_img)
        evidence_features.update(quality.metrics)
        evidence_features["face_count"] = float(len(detect_res.faces))
        if primary_box is not None:
            evidence_features["face_box_confidence"] = primary_box.confidence
            evidence_features["face_box_area"] = round(primary_box.area, 4)
        if landmark_res is not None:
            evidence_features["landmarks_count"] = len(landmark_res.landmarks)

        # Check adapter experimental status
        if self.model_adapter.is_experimental:
            limitations.append(
                "Adapter uses experimental uncalibrated regional descriptors; not validated FACS Action Units."
            )

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
                input_quality=input_quality,
                model_state=self.model_adapter.model_state,
                is_validated=False,
                face_id=primary_box.face_id if primary_box else None,
                face_bbox=primary_box.model_dump(
                    include={"x_min", "y_min", "x_max", "y_max", "confidence"}
                )
                if primary_box
                else None,
                face_count=len(detect_res.faces),
                insufficient_evidence_reason="Configured model adapter weights are unavailable.",
                is_definitive_claim=False,
            )

        # 6. Model inference (cropped & aligned around detected primary face)
        pixel_box = (
            primary_box.to_pixel_box(pil_img.size[0], pil_img.size[1])
            if primary_box is not None
            else None
        )
        left_eye = (
            (landmark_res.landmarks[0].x, landmark_res.landmarks[0].y)
            if landmark_res and len(landmark_res.landmarks) >= 2
            else None
        )
        right_eye = (
            (landmark_res.landmarks[1].x, landmark_res.landmarks[1].y)
            if landmark_res and len(landmark_res.landmarks) >= 2
            else None
        )
        tensor = self.preprocessor.preprocess(
            pil_img, face_bbox=pixel_box, left_eye=left_eye, right_eye=right_eye
        )
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
                input_quality=input_quality,
                model_state=ModelState.MODEL_INFERENCE_FAILED,
                is_validated=False,
                is_definitive_claim=False,
            )

        # 7. Calculate confidence and uncertainty
        probs_array = np.array(list(probabilities.values()), dtype=np.float64)
        is_uniform = (
            (float(np.max(probs_array) - np.min(probs_array)) < 0.02)
            if len(probs_array) > 0
            else True
        )
        is_unvalidated = not self.model_adapter.is_validated
        is_experimental = self.model_adapter.is_experimental

        raw_dominant = max(probabilities.items(), key=lambda item: item[1])[0]
        raw_confidence = float(probabilities[raw_dominant])

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

        # Deterministic Status Precedence Policy:
        # Precedence: FAILED > MODEL_UNAVAILABLE > MODEL_UNVALIDATED > INSUFFICIENT_EVIDENCE > DEGRADED > OK
        # Crucial: Unvalidated model state is NEVER overwritten by degraded input quality!
        insufficient_reason: str | None = None
        if is_unvalidated or is_experimental:
            status = ObservationStatus.MODEL_UNVALIDATED
            dominant_cat = EmotionCategory.UNKNOWN.value
            confidence = 0.0
            uncertainty = 1.0
            insufficient_reason = (
                "Model is unvalidated; discrete emotion categorization suppressed."
            )
            limitations.append(
                "Model is unvalidated; discrete emotion categorization suppressed to prevent fabricated predictions."
            )
        elif input_quality == InputQualityStatus.UNUSABLE:
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            confidence = 0.0
            uncertainty = 1.0
            insufficient_reason = "Unusable sensory input quality."
            limitations.append(
                "Unusable sensory input quality; insufficient evidence for emotion classification."
            )
        elif is_uniform:
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            confidence = 0.0
            uncertainty = 1.0
            insufficient_reason = "Uniform probability distribution across categories."
            limitations.append(
                "Uniform probability distribution across categories; insufficient evidence for classification."
            )
        elif (
            confidence < self.config.confidence_threshold
            or uncertainty > self.config.uncertainty_threshold
        ):
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            dominant_cat = EmotionCategory.INSUFFICIENT_EVIDENCE.value
            insufficient_reason = (
                f"Low confidence ({confidence:.2f} < {self.config.confidence_threshold}) "
                f"or high uncertainty ({uncertainty:.2f} > {self.config.uncertainty_threshold})."
            )
            limitations.append(insufficient_reason)
            confidence = 0.0
            uncertainty = 1.0
        elif input_quality == InputQualityStatus.DEGRADED:
            status = ObservationStatus.DEGRADED
            dominant_cat = raw_dominant
        else:
            status = ObservationStatus.OK
            dominant_cat = raw_dominant

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Ephemeral media scrubbing
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
            input_quality=input_quality,
            model_state=self.model_adapter.model_state,
            is_validated=self.model_adapter.is_validated,
            is_calibrated=False,
            raw_confidence=round(raw_confidence, 4),
            face_id=primary_box.face_id if primary_box else None,
            face_bbox=primary_box.model_dump(
                include={"x_min", "y_min", "x_max", "y_max", "confidence"}
            )
            if primary_box
            else None,
            face_count=len(detect_res.faces),
            insufficient_evidence_reason=insufficient_reason,
            is_definitive_claim=False,
        )
