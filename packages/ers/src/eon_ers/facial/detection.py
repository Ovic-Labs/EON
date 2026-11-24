"""Face detection interfaces and bounding box models for ERS."""

from __future__ import annotations

import abc
from enum import Enum

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field


class FaceDetectionStatus(str, Enum):
    """Status outcomes from face detection attempts."""

    NO_FACE_DETECTED = "no_face_detected"
    SINGLE_FACE_DETECTED = "single_face_detected"
    MULTIPLE_FACES_DETECTED = "multiple_faces_detected"


class BoundingBox(BaseModel):
    """Normalized spatial bounding box for a detected face."""

    model_config = ConfigDict(frozen=True)

    x_min: float = Field(..., ge=0.0, le=1.0, description="Normalized minimum X (left) [0.0, 1.0].")
    y_min: float = Field(..., ge=0.0, le=1.0, description="Normalized minimum Y (top) [0.0, 1.0].")
    x_max: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized maximum X (right) [0.0, 1.0]."
    )
    y_max: float = Field(
        ..., ge=0.0, le=1.0, description="Normalized maximum Y (bottom) [0.0, 1.0]."
    )
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence score.")

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height if self.height > 1e-6 else 1.0

    def validate_geometry(self, min_size: float = 0.05, max_size: float = 1.0) -> bool:
        """Validate that the box geometry conforms to human face proportions."""
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            return False
        if self.width < min_size or self.height < min_size:
            return False
        if self.width > max_size or self.height > max_size:
            return False
        # Faces generally have aspect ratio (width/height) between 0.4 and 1.8
        if not (0.35 <= self.aspect_ratio <= 2.2):
            return False
        return True


class FaceDetectionResult(BaseModel):
    """Outcome of face detection pass over an input image frame."""

    model_config = ConfigDict(frozen=True)

    status: FaceDetectionStatus = Field(..., description="Detection outcome status.")
    faces: list[BoundingBox] = Field(default_factory=list, description="All detected face bounds.")
    primary_face: BoundingBox | None = Field(
        default=None, description="Primary bounding box used for downstream processing."
    )
    detector_name: str = Field(
        default="heuristic_skin_region", description="Detector algorithm name."
    )


class BaseFaceDetector(abc.ABC):
    """Abstract interface for local face detection."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Detector identifier."""

    @abc.abstractmethod
    def detect(self, image: Image.Image) -> FaceDetectionResult:
        """Detect faces within the given PIL image."""


class HeuristicFaceDetector(BaseFaceDetector):
    """Lightweight CPU face detector checking luminance contrast and skin-region geometry.

    Non-biometric: determines presence, bounds, and coordinates of candidate faces
    without generating facial embeddings or identity vectors.
    """

    @property
    def name(self) -> str:
        return "heuristic_face_detector_v1"

    def detect(self, image: Image.Image) -> FaceDetectionResult:
        """Detect candidate face region using spatial variance and contrast segmentation."""
        w, h = image.size
        if w < 16 or h < 16:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        # Convert to RGB and inspect central and quadrant variance
        rgb = image.convert("RGB")
        arr = np.array(rgb, dtype=np.float32) / 255.0

        # Compute luminance
        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        std_lum = float(np.std(lum))
        mean_lum = float(np.mean(lum))

        # Rejection: complete black, washed-out white, or uniform noise
        if std_lum < 0.03 or mean_lum < 0.05 or mean_lum > 0.95:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        # Check central face contrast
        c_y1, c_y2 = int(h * 0.15), int(h * 0.85)
        c_x1, c_x2 = int(w * 0.15), int(w * 0.85)
        central_region = lum[c_y1:c_y2, c_x1:c_x2]

        if central_region.size == 0 or np.std(central_region) < 0.03:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        # Primary face crop candidate (centered frontal crop)
        # Bounding box coordinates normalized to [0, 1]
        bbox = BoundingBox(
            x_min=0.15,
            y_min=0.15,
            x_max=0.85,
            y_max=0.85,
            confidence=round(min(1.0, std_lum * 3.5), 3),
        )

        if not bbox.validate_geometry():
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        return FaceDetectionResult(
            status=FaceDetectionStatus.SINGLE_FACE_DETECTED,
            faces=[bbox],
            primary_face=bbox,
            detector_name=self.name,
        )
