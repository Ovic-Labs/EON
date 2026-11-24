"""Unit tests for facial detection, landmarks, and regional feature descriptors."""

import io

import numpy as np
import pytest
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.facial.adapters import ExperimentalRegionalFeatureAdapter
from eon_ers.facial.detection import (
    BoundingBox,
    FaceDetectionStatus,
    HeuristicFaceDetector,
)
from eon_ers.facial.features import ExperimentalRegionalFeatureExtractor
from eon_ers.facial.landmarks import HeuristicLandmarkDetector
from eon_ers.facial.pipeline import FacialPipeline
from eon_ers.types import Modality, ObservationStatus
from PIL import Image


def test_bounding_box_geometry_validation() -> None:
    # Valid box
    valid_box = BoundingBox(x_min=0.2, y_min=0.2, x_max=0.8, y_max=0.8, confidence=0.9)
    assert valid_box.validate_geometry() is True
    assert valid_box.width == pytest.approx(0.6)
    assert valid_box.height == pytest.approx(0.6)
    assert valid_box.area == pytest.approx(0.36)

    # Inverted coordinates
    invalid_box = BoundingBox(x_min=0.8, y_min=0.2, x_max=0.2, y_max=0.8, confidence=0.9)
    assert invalid_box.validate_geometry() is False

    # Extreme aspect ratio
    skinny_box = BoundingBox(x_min=0.1, y_min=0.1, x_max=0.12, y_max=0.9, confidence=0.9)
    assert skinny_box.validate_geometry() is False


def test_heuristic_face_detector_no_face_blank_image() -> None:
    detector = HeuristicFaceDetector()
    # Pure black image
    blank = Image.new("RGB", (64, 64), color=(0, 0, 0))
    result = detector.detect(blank)
    assert result.status == FaceDetectionStatus.NO_FACE_DETECTED
    assert len(result.faces) == 0
    assert result.primary_face is None


def test_heuristic_face_detector_valid_image() -> None:
    detector = HeuristicFaceDetector()
    # Image with spatial variation and contrast
    arr = np.ones((128, 128, 3), dtype=np.uint8) * 180
    arr[30:50, 30:50] = 50
    arr[30:50, 78:98] = 50
    arr[75:95, 40:88] = 80
    img = Image.fromarray(arr)

    result = detector.detect(img)
    assert result.status == FaceDetectionStatus.SINGLE_FACE_DETECTED
    assert result.primary_face is not None
    assert result.primary_face.validate_geometry() is True


def test_landmark_detector_canonical_5points() -> None:
    detector = HeuristicLandmarkDetector()
    bbox = BoundingBox(x_min=0.1, y_min=0.1, x_max=0.9, y_max=0.9, confidence=0.85)
    img = Image.new("RGB", (64, 64), color=(128, 128, 128))

    result = detector.detect_landmarks(img, bbox)
    assert result.status == "success"
    assert len(result.landmarks) == 5
    assert result.is_normalized is True

    for pt in result.landmarks:
        assert 0.0 <= pt.x <= 1.0
        assert 0.0 <= pt.y <= 1.0


def test_experimental_regional_descriptors_scientific_honesty() -> None:
    extractor = ExperimentalRegionalFeatureExtractor()
    meta = extractor.get_descriptor_metadata()

    assert meta["is_validated_facs"] is False
    assert meta["is_experimental"] is True
    assert "FACS" in str(meta["limitations"])

    # Feature keys must NOT contain AU claims
    arr = np.random.randint(60, 200, size=(64, 64, 3), dtype=np.uint8)
    feats = extractor.extract_features(Image.fromarray(arr))
    for k in feats.keys():
        assert not k.startswith("AU"), f"AU claim found in heuristic key: {k}"
        assert k.startswith("regional_"), f"Descriptor key does not denote regional feature: {k}"


def test_experimental_adapter_returns_insufficient_evidence_in_pipeline() -> None:
    config = ERSConfig()
    # Explicitly use experimental unvalidated adapter
    adapter = ExperimentalRegionalFeatureAdapter()
    pipeline = FacialPipeline(config, model_adapter=adapter)

    arr = np.random.randint(80, 200, size=(128, 128, 3), dtype=np.uint8)
    # Add face contrast patches so face detector succeeds
    arr[30:50, 30:50] = 50
    arr[30:50, 78:98] = 50
    arr[75:95, 40:88] = 80
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")

    inp = ERSInput(
        session_id="exp-session",
        modality=Modality.FACIAL,
        consent_reference="token",
        image_payload=buf.getvalue(),
    )
    obs = pipeline.process(inp)

    # Must abstain because adapter is experimental
    assert obs.status in (
        ObservationStatus.INSUFFICIENT_EVIDENCE,
        ObservationStatus.MODEL_UNVALIDATED,
    )
    assert any("experimental" in lim.lower() for lim in obs.limitations)
