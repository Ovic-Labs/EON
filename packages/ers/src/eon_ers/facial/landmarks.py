"""Facial landmark detection and geometric normalization interfaces for ERS."""

from __future__ import annotations

import abc
from typing import Any

from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.facial.detection import BoundingBox


class LandmarkPoint(BaseModel):
    """Normalized 2D coordinate of a facial landmark."""

    model_config = ConfigDict(frozen=True)

    x: float = Field(..., ge=0.0, le=1.0, description="Normalized X coordinate [0.0, 1.0].")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized Y coordinate [0.0, 1.0].")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Landmark confidence score.")


class LandmarkDetectionResult(BaseModel):
    """Normalized landmarks extracted from a detected face bounding box."""

    model_config = ConfigDict(frozen=True)

    status: str = Field(
        ..., description="Detection status ('success', 'failed', 'insufficient_evidence')."
    )
    landmarks: list[LandmarkPoint] = Field(
        default_factory=list, description="Ordered landmark points."
    )
    is_normalized: bool = Field(
        default=True, description="Whether coordinates are normalized to [0, 1]."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Diagnostic detector metadata."
    )


class BaseLandmarkDetector(abc.ABC):
    """Abstract interface for local facial landmark detectors."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Detector identifier."""

    @abc.abstractmethod
    def detect_landmarks(self, image: Image.Image, bbox: BoundingBox) -> LandmarkDetectionResult:
        """Detect normalized facial landmarks within the bounded region."""


class BaseGeometricFeatureExtractor(abc.ABC):
    """Abstract interface for extracting scale-invariant geometric descriptors from landmarks."""

    @abc.abstractmethod
    def extract_features(self, landmarks: LandmarkDetectionResult) -> dict[str, float]:
        """Compute non-biometric geometric distance ratios and angles from landmarks."""


class HeuristicLandmarkDetector(BaseLandmarkDetector):
    """Reference 5-point landmark estimator for standardized frontal crops.

    Points:
    0: Left eye center
    1: Right eye center
    2: Nose tip
    3: Mouth corner left
    4: Mouth corner right
    """

    @property
    def name(self) -> str:
        return "heuristic_5point_landmark_detector"

    def detect_landmarks(self, image: Image.Image, bbox: BoundingBox) -> LandmarkDetectionResult:
        """Estimate 5 canonical facial reference points relative to bounding box."""
        if not bbox.validate_geometry():
            return LandmarkDetectionResult(
                status="failed",
                landmarks=[],
                is_normalized=True,
                metadata={"reason": "Invalid bounding box geometry"},
            )

        # Canonical relative landmark offsets within normalized face box
        # Box coordinates: x_min, y_min to x_max, y_max
        bx = bbox.x_min
        by = bbox.y_min
        bw = bbox.width
        bh = bbox.height

        # Relative canonical positions
        # Left eye: ~30% width, ~35% height
        # Right eye: ~70% width, ~35% height
        # Nose tip: ~50% width, ~55% height
        # Mouth left: ~35% width, ~75% height
        # Mouth right: ~65% width, ~75% height
        canonical_rel = [
            (0.30, 0.35),  # Left eye
            (0.70, 0.35),  # Right eye
            (0.50, 0.55),  # Nose tip
            (0.35, 0.75),  # Mouth left
            (0.65, 0.75),  # Mouth right
        ]

        pts: list[LandmarkPoint] = []
        for rx, ry in canonical_rel:
            abs_x = min(1.0, max(0.0, bx + rx * bw))
            abs_y = min(1.0, max(0.0, by + ry * bh))
            pts.append(
                LandmarkPoint(x=round(abs_x, 4), y=round(abs_y, 4), confidence=bbox.confidence)
            )

        return LandmarkDetectionResult(
            status="success",
            landmarks=pts,
            is_normalized=True,
            metadata={"detector": self.name, "points_count": len(pts)},
        )
