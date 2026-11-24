"""Universal signal quality coordinator for ERS."""

from __future__ import annotations

from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput, QualityAssessment
from eon_ers.quality.audio_quality import AudioQualityEvaluator
from eon_ers.quality.face_quality import FaceQualityEvaluator
from eon_ers.types import Modality, QualityGrade


class SignalQualityCoordinator:
    """Coordinates visual and acoustic signal quality evaluation."""

    def __init__(self, config: ERSConfig) -> None:
        self.config = config
        self.face_evaluator = FaceQualityEvaluator(
            min_resolution=config.min_face_resolution,
            max_dimension=config.max_image_dimension,
            blur_threshold=config.blur_threshold,
            min_brightness=config.min_brightness,
        )
        self.audio_evaluator = AudioQualityEvaluator(
            expected_sample_rate=config.audio_sample_rate,
            min_duration_seconds=0.2,
            max_duration_seconds=config.max_audio_duration_seconds,
            min_snr_db=config.min_audio_snr_db,
            silence_threshold_db=config.silence_threshold_db,
        )

    def evaluate_input(self, inp: ERSInput) -> QualityAssessment:
        """Evaluate raw observation input and return QualityAssessment."""
        if inp.modality == Modality.FACIAL:
            if inp.image_payload is None:
                return QualityAssessment(
                    modality=Modality.FACIAL,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={},
                    is_acceptable=False,
                    reasons=["Missing image payload"],
                )
            assessment, _ = self.face_evaluator.evaluate(inp.image_payload)
            return assessment

        elif inp.modality == Modality.SPEECH:
            if inp.audio_payload is None:
                return QualityAssessment(
                    modality=Modality.SPEECH,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={},
                    is_acceptable=False,
                    reasons=["Missing audio payload"],
                )
            assessment, _, _ = self.audio_evaluator.evaluate(inp.audio_payload, inp.sample_rate)
            return assessment

        else:
            return QualityAssessment(
                modality=inp.modality,
                grade=QualityGrade.ACCEPTABLE,
                score=1.0,
                metrics={},
                is_acceptable=True,
                reasons=[],
            )
