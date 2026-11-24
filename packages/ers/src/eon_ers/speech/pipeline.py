"""Speech acoustic analysis pipeline orchestrator for ERS."""

from __future__ import annotations

import time

import numpy as np

from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.quality.audio_quality import AudioQualityEvaluator
from eon_ers.speech.adapters import (
    BaseSpeechModelAdapter,
    ExperimentalAcousticProsodyAdapter,
    ONNXSpeechModelAdapter,
)
from eon_ers.speech.features import AcousticFeatureExtractor
from eon_ers.types import EmotionCategory, Modality, ObservationStatus, QualityGrade


class SpeechPipeline:
    """Executes the full 12-stage acoustic speech-processing pipeline."""

    def __init__(
        self,
        config: ERSConfig,
        model_adapter: BaseSpeechModelAdapter | None = None,
    ) -> None:
        self.config = config
        self.quality_evaluator = AudioQualityEvaluator(
            expected_sample_rate=config.audio_sample_rate,
            min_duration_seconds=0.2,
            max_duration_seconds=config.max_audio_duration_seconds,
            min_snr_db=config.min_audio_snr_db,
            silence_threshold_db=config.silence_threshold_db,
        )
        self.feature_extractor = AcousticFeatureExtractor(sample_rate=config.audio_sample_rate)

        if model_adapter is not None:
            self.model_adapter = model_adapter
        elif config.speech_model_path:
            self.model_adapter = ONNXSpeechModelAdapter(
                model_path=config.speech_model_path,
                model_id=config.speech_model_id,
                num_threads=config.num_threads,
            )
        else:
            self.model_adapter = ExperimentalAcousticProsodyAdapter(
                model_id="ers-prosody-experimental-v1"
            )

    def process(self, inp: ERSInput) -> EmotionObservation:
        """Execute speech acoustic processing pipeline on sensory input."""
        start_time = time.perf_counter()
        limitations: list[str] = [
            "Epistemic modesty: Acoustic speech cues represent vocal expression and prosody, not verified inner emotional states."
        ]

        # 1. Audio payload validation
        if inp.audio_payload is None:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
                expression_observations={},
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=0.0,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=["No audio payload supplied in input envelope."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        # 2. Quality evaluation & decoding
        quality, samples, sample_rate = self.quality_evaluator.evaluate(
            inp.audio_payload, inp.sample_rate
        )

        if samples is None or quality.grade == QualityGrade.UNUSABLE:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
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

        # 3. Silence / low energy handling
        if any("silence" in r for r in quality.reasons):
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
                expression_observations=quality.metrics,
                emotion_probabilities={EmotionCategory.INSUFFICIENT_EVIDENCE.value: 1.0},
                dominant_estimate=EmotionCategory.INSUFFICIENT_EVIDENCE.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations
                + ["Audio frame classified as silence or background noise."],
                status=ObservationStatus.INSUFFICIENT_EVIDENCE,
                is_definitive_claim=False,
            )

        # 4. Feature extraction
        acoustic_features = self.feature_extractor.extract_features(samples, sample_rate)
        acoustic_features.update(quality.metrics)

        # Check adapter experimental status
        if self.model_adapter.is_experimental:
            limitations.append(
                "Adapter uses experimental uncalibrated acoustic heuristics; not a validated emotion classifier."
            )

        # Check model availability
        if not self.model_adapter.is_available:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
                expression_observations=acoustic_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations
                + ["Configured speech model adapter weights are unavailable."],
                status=ObservationStatus.MODEL_UNAVAILABLE,
                is_definitive_claim=False,
            )

        # 5. Model inference
        try:
            probabilities = self.model_adapter.predict(samples, sample_rate, acoustic_features)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            inp.scrub_media_payload()
            return EmotionObservation(
                observation_id=inp.observation_id,
                timestamp=inp.timestamp,
                modality=Modality.SPEECH,
                expression_observations=acoustic_features,
                emotion_probabilities={EmotionCategory.UNKNOWN.value: 1.0},
                dominant_estimate=EmotionCategory.UNKNOWN.value,
                confidence=0.0,
                uncertainty=1.0,
                quality_score=quality.score,
                model_id=self.model_adapter.model_id,
                model_version=self.model_adapter.model_version,
                processing_latency_ms=latency_ms,
                limitations=limitations + [f"Speech model inference failed: {exc}"],
                status=ObservationStatus.FAILED,
                is_definitive_claim=False,
            )

        # 6. Calculate confidence and uncertainty
        probs_array = np.array(list(probabilities.values()), dtype=np.float64)
        dominant_cat = max(probabilities.items(), key=lambda item: item[1])[0]
        raw_confidence = float(probabilities[dominant_cat])

        # Confidence attenuated by acoustic quality
        confidence = float(np.clip(raw_confidence * quality.score, 0.0, 1.0))

        # Normalized Shannon entropy
        k = len(probabilities)
        clean_probs = probs_array[probs_array > 1e-12]
        entropy = -np.sum(clean_probs * np.log(clean_probs))
        max_entropy = np.log(k) if k > 1 else 1.0
        normalized_entropy = float(np.clip(entropy / max_entropy, 0.0, 1.0))

        # Margin uncertainty
        sorted_probs = np.sort(probs_array)[::-1]
        margin = (
            float(sorted_probs[0] - sorted_probs[1]) if len(sorted_probs) > 1 else sorted_probs[0]
        )
        margin_uncertainty = 1.0 - margin

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
            self.model_adapter.is_experimental
            or confidence < self.config.confidence_threshold
            or uncertainty > self.config.uncertainty_threshold
        ):
            status = ObservationStatus.INSUFFICIENT_EVIDENCE
            if self.model_adapter.is_experimental:
                limitations.append(
                    "Abstaining from classification: unvalidated experimental feature adapter."
                )
            else:
                limitations.append(
                    f"Low confidence ({confidence:.2f} < {self.config.confidence_threshold}) "
                    f"or high uncertainty ({uncertainty:.2f} > {self.config.uncertainty_threshold})."
                )

        if quality.grade == QualityGrade.DEGRADED:
            status = ObservationStatus.DEGRADED

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Ephemeral media scrubbing
        inp.scrub_media_payload()

        return EmotionObservation(
            observation_id=inp.observation_id,
            timestamp=inp.timestamp,
            modality=Modality.SPEECH,
            expression_observations=acoustic_features,
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
