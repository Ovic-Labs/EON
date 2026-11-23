"""Unit tests for common types, enumerations, and provenance."""

import pytest
from pydantic import BaseModel, ValidationError

from eon.schemas.common import (
    ConfidenceScore,
    DataClassification,
    ModalityType,
    Provenance,
    QualityStatus,
    UncertaintyScore,
)


class DummyScoreModel(BaseModel):
    confidence: ConfidenceScore
    uncertainty: UncertaintyScore


def test_confidence_score_valid_bounds() -> None:
    """AC-1.2-06, AC-1.2-07: Verify confidence and uncertainty bounds within [0.0, 1.0]."""
    m1 = DummyScoreModel(confidence=0.0, uncertainty=1.0)
    assert m1.confidence == 0.0
    assert m1.uncertainty == 1.0

    m2 = DummyScoreModel(confidence=0.75, uncertainty=0.25)
    assert m2.confidence == 0.75
    assert m2.uncertainty == 0.25


def test_confidence_score_out_of_bounds() -> None:
    """Verify scores outside [0.0, 1.0] raise ValidationError."""
    with pytest.raises(ValidationError):
        DummyScoreModel(confidence=-0.01, uncertainty=0.5)

    with pytest.raises(ValidationError):
        DummyScoreModel(confidence=1.01, uncertainty=0.5)

    with pytest.raises(ValidationError):
        DummyScoreModel(confidence=0.5, uncertainty=-0.1)

    with pytest.raises(ValidationError):
        DummyScoreModel(confidence=0.5, uncertainty=1.5)


def test_modality_enum_values() -> None:
    """Verify ModalityType members."""
    expected = {
        "visual",
        "audio",
        "text",
        "behavioural",
        "environmental",
        "physiological",
        "multimodal",
    }
    actual = {m.value for m in ModalityType}
    assert expected == actual


def test_data_classification_enum_values() -> None:
    """Verify DataClassification members."""
    expected = {"public", "internal", "sensitive_behavioural", "restricted_biometric_derived"}
    actual = {c.value for c in DataClassification}
    assert expected == actual


def test_quality_status_enum_values() -> None:
    """Verify QualityStatus members."""
    expected = {"good", "degraded", "stale", "unreliable", "simulated"}
    actual = {q.value for q in QualityStatus}
    assert expected == actual


def test_provenance_valid_construction() -> None:
    """AC-1.2-06: Verify valid Provenance model construction."""
    p = Provenance(
        source_id="eon.ers.visual",
        engine_version="0.1.0",
        model_name="face_mesh_v2",
        model_version="2.1.0",
        capture_device="realsense_d435",
        processing_stage="landmark_extraction",
    )
    assert p.source_id == "eon.ers.visual"
    assert p.model_name == "face_mesh_v2"


def test_provenance_rejects_raw_biometric_data() -> None:
    """Verify raw binary/biometric embedding tokens in provenance are strictly rejected."""
    with pytest.raises(ValidationError):
        Provenance(
            source_id="eon.ers",
            model_name="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
        )

    with pytest.raises(ValidationError):
        Provenance(
            source_id="eon.ers",
            capture_device="A" * 300,  # Exceeds max length limit
        )
