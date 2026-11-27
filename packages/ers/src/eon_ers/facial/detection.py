"""Face detection interfaces, multi-face candidate localization, and boundary validation."""

from __future__ import annotations

import abc
import threading
from enum import Enum
from pathlib import Path

import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field
from scipy import ndimage

from eon_ers.exceptions import ERSConfigurationError


class FaceDetectionStatus(str, Enum):
    """Status outcomes from face detection attempts."""

    NO_FACE_DETECTED = "no_face_detected"
    SINGLE_FACE_DETECTED = "single_face_detected"
    MULTIPLE_FACES_DETECTED = "multiple_faces_detected"


class BoundingBox(BaseModel):
    """Normalized spatial bounding box for a detected face (non-biometric)."""

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
    face_id: str | None = Field(
        default=None,
        description="Ephemeral session-only candidate identifier (not a biometric ID).",
    )
    is_partial_boundary: bool = Field(
        default=False,
        description="True when box touches frame edges indicating partial/clipped face.",
    )

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

    def to_pixel_box(self, image_width: int, image_height: int) -> tuple[int, int, int, int]:
        """Convert normalized coordinates to clamped pixel (x1, y1, x2, y2) tuple."""
        x1 = max(0, min(image_width - 1, int(round(self.x_min * image_width))))
        y1 = max(0, min(image_height - 1, int(round(self.y_min * image_height))))
        x2 = max(x1 + 1, min(image_width, int(round(self.x_max * image_width))))
        y2 = max(y1 + 1, min(image_height, int(round(self.y_max * image_height))))
        return x1, y1, x2, y2

    def validate_geometry(self, min_size: float = 0.05, max_size: float = 1.0) -> bool:
        """Validate that the box geometry conforms to human face proportions."""
        if self.x_max <= self.x_min or self.y_max <= self.y_min:
            return False
        if self.width < min_size or self.height < min_size:
            return False
        if self.width > max_size or self.height > max_size:
            return False
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
        """Detect zero, one, or multiple faces within the given PIL image."""


class OpenCVFaceDetector(BaseFaceDetector):
    """CPU frontal-face localizer with a profile fallback."""

    def __init__(self) -> None:
        try:
            import cv2
        except ImportError as exc:
            raise ERSConfigurationError(
                "The OpenCV detector requires opencv-python-headless. "
                'Install ovic-eon with the "studio" extra.'
            ) from exc
        if not hasattr(cv2, "CascadeClassifier"):
            raise ERSConfigurationError(
                "This OpenCV build lacks CascadeClassifier. Install OpenCV 4 with the studio extra."
            )
        cascade_path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        self._cascade = cv2.CascadeClassifier(str(cascade_path))
        if self._cascade.empty():
            raise ERSConfigurationError("OpenCV's frontal-face cascade could not be loaded.")
        self._profile = cv2.CascadeClassifier(
            str(cascade_path.with_name("haarcascade_profileface.xml"))
        )
        if self._profile.empty():
            raise ERSConfigurationError("OpenCV's profile-face cascade could not be loaded.")
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return "opencv_haar_frontal_profile"

    def detect(self, image: Image.Image) -> FaceDetectionResult:
        gray = image.convert("L")
        gray.thumbnail((640, 640))
        width, height = gray.size
        pixels = np.asarray(gray)
        options = {"scaleFactor": 1.1, "minNeighbors": 5, "minSize": (24, 24)}
        # Require stronger support for profile detections on face-free textures.
        profile_options = {**options, "minNeighbors": 12}
        with self._lock:
            rectangles = self._cascade.detectMultiScale(pixels, **options)
            if len(rectangles) == 0:
                rectangles = self._profile.detectMultiScale(pixels, **profile_options)
            if len(rectangles) == 0:
                mirrored = self._profile.detectMultiScale(pixels[:, ::-1], **profile_options)
                rectangles = [(width - x - w, y, w, h) for x, y, w, h in mirrored]
        candidates = sorted(
            rectangles, key=lambda rect: (-int(rect[2]) * int(rect[3]), int(rect[0]), int(rect[1]))
        )
        faces = [
            BoundingBox(
                x_min=x / width,
                y_min=y / height,
                x_max=(x + w) / width,
                y_max=(y + h) / height,
                # The cascade does not supply a calibrated probability.
                confidence=0.0,
                face_id=f"face-{index}",
                is_partial_boundary=bool(
                    x <= 1 or y <= 1 or x + w >= width - 1 or y + h >= height - 1
                ),
            )
            for index, (x, y, w, h) in enumerate(candidates)
        ]
        if not faces:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED, detector_name=self.name
            )
        return FaceDetectionResult(
            status=(
                FaceDetectionStatus.SINGLE_FACE_DETECTED
                if len(faces) == 1
                else FaceDetectionStatus.MULTIPLE_FACES_DETECTED
            ),
            faces=faces,
            primary_face=faces[0],
            detector_name=self.name,
        )


class HeuristicFaceDetector(BaseFaceDetector):
    """Lightweight CPU multi-candidate face localizer using local gradient variance segmentation.

    Non-biometric: identifies spatial candidate face regions (0, 1, or N) without generating
    facial embeddings or permanent identity descriptors.
    """

    @property
    def name(self) -> str:
        return "heuristic_face_detector_v2"

    def detect(self, image: Image.Image) -> FaceDetectionResult:
        """Detect zero, one, or multiple candidate face regions on CPU."""
        w, h = image.size
        if w < 16 or h < 16:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        rgb = image.convert("RGB")
        arr = np.array(rgb, dtype=np.float32) / 255.0
        if arr.ndim != 3 or arr.shape[2] < 3 or not np.isfinite(arr).all():
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        std_lum = float(np.std(lum))
        mean_lum = float(np.mean(lum))

        if std_lum < 0.03 or mean_lum < 0.04 or mean_lum > 0.96:
            return FaceDetectionResult(
                status=FaceDetectionStatus.NO_FACE_DETECTED,
                faces=[],
                primary_face=None,
                detector_name=self.name,
            )

        # Compute local energy map on downscaled grid for fast O(HW) segmentation
        work_h, work_w = min(h, 64), min(w, 64)
        small_lum = (
            np.array(
                Image.fromarray((lum * 255.0).astype(np.uint8)).resize(
                    (work_w, work_h), Image.Resampling.BILINEAR
                ),
                dtype=np.float32,
            )
            / 255.0
        )
        gx = np.abs(np.diff(small_lum, axis=1, prepend=small_lum[:, :1]))
        gy = np.abs(np.diff(small_lum, axis=0, prepend=small_lum[:1, :]))
        edge_map = gx + gy
        smoothed = ndimage.uniform_filter(edge_map, size=5)
        threshold = max(0.02, float(np.mean(smoothed)) + 0.75 * float(np.std(smoothed)))
        active_mask = smoothed > threshold

        # Merge nearby intra-face features (eyes, brows, nose, mouth) using anisotropic dilation
        # so one face becomes a single coherent cluster while widely separated faces remain distinct.
        struct = np.ones((max(5, work_h // 8), max(5, work_w // 8)), dtype=bool)
        merged_mask = ndimage.binary_dilation(active_mask, structure=struct, iterations=1)
        labeled, num_features = ndimage.label(merged_mask)

        raw_boxes: list[BoundingBox] = []
        if num_features > 0:
            slices = ndimage.find_objects(labeled)
            for slc in slices:
                if slc is None:
                    continue
                ys, xs = slc
                x1 = max(0.0, (xs.start - 1) / work_w)
                x2 = min(1.0, (xs.stop + 1) / work_w)
                y1 = max(0.0, (ys.start - 1) / work_h)
                y2 = min(1.0, (ys.stop + 1) / work_h)
                patch = small_lum[ys, xs]
                patch_std = float(np.std(patch)) if patch.size else 0.0
                if patch_std < 0.03:
                    continue
                is_edge = x1 <= 0.02 or y1 <= 0.02 or x2 >= 0.98 or y2 >= 0.98
                box = BoundingBox(
                    x_min=round(x1, 4),
                    y_min=round(y1, 4),
                    x_max=round(x2, 4),
                    y_max=round(y2, 4),
                    confidence=round(min(1.0, patch_std * 3.5), 3),
                    face_id=f"face-{len(raw_boxes)}",
                    is_partial_boundary=is_edge,
                )
                if box.validate_geometry(min_size=0.08, max_size=0.98):
                    raw_boxes.append(box)

        # Merge overlapping or tight intra-face sub-boxes (<0.12 normalized center-edge gap)
        candidates: list[BoundingBox] = []
        for box in sorted(raw_boxes, key=lambda b: (b.x_min, b.y_min)):
            merged = False
            for idx, existing in enumerate(candidates):
                h_gap = max(0.0, max(box.x_min - existing.x_max, existing.x_min - box.x_max))
                v_gap = max(0.0, max(box.y_min - existing.y_max, existing.y_min - box.y_max))
                if h_gap < 0.14 and v_gap < 0.20:
                    nx1 = min(existing.x_min, box.x_min)
                    ny1 = min(existing.y_min, box.y_min)
                    nx2 = max(existing.x_max, box.x_max)
                    ny2 = max(existing.y_max, box.y_max)
                    if (nx2 - nx1) <= 0.85 and (ny2 - ny1) <= 0.92:
                        combined = BoundingBox(
                            x_min=round(nx1, 4),
                            y_min=round(ny1, 4),
                            x_max=round(nx2, 4),
                            y_max=round(ny2, 4),
                            confidence=max(existing.confidence, box.confidence),
                            face_id=existing.face_id,
                            is_partial_boundary=(
                                existing.is_partial_boundary or box.is_partial_boundary
                            ),
                        )
                        if combined.validate_geometry(min_size=0.08, max_size=0.98):
                            candidates[idx] = combined
                            merged = True
                            break
            if not merged:
                candidates.append(box)

        # Fallback to frontal candidate if globally textured frame has diffuse contrast
        if not candidates:
            c_y1, c_y2 = int(h * 0.15), int(h * 0.85)
            c_x1, c_x2 = int(w * 0.15), int(w * 0.85)
            central_region = lum[c_y1:c_y2, c_x1:c_x2]
            if central_region.size == 0 or float(np.std(central_region)) < 0.03:
                return FaceDetectionResult(
                    status=FaceDetectionStatus.NO_FACE_DETECTED,
                    faces=[],
                    primary_face=None,
                    detector_name=self.name,
                )
            fallback_box = BoundingBox(
                x_min=0.15,
                y_min=0.15,
                x_max=0.85,
                y_max=0.85,
                confidence=round(min(1.0, std_lum * 3.5), 3),
                face_id="face-0",
                is_partial_boundary=False,
            )
            candidates = [fallback_box]

        # Deterministic ordering by descending area * confidence; reassign clean face-0..k IDs
        candidates.sort(key=lambda b: b.area * b.confidence, reverse=True)
        numbered = [
            BoundingBox(
                x_min=b.x_min,
                y_min=b.y_min,
                x_max=b.x_max,
                y_max=b.y_max,
                confidence=b.confidence,
                face_id=f"face-{i}",
                is_partial_boundary=b.is_partial_boundary,
            )
            for i, b in enumerate(candidates)
        ]

        status = (
            FaceDetectionStatus.MULTIPLE_FACES_DETECTED
            if len(numbered) > 1
            else FaceDetectionStatus.SINGLE_FACE_DETECTED
        )
        return FaceDetectionResult(
            status=status,
            faces=numbered,
            primary_face=numbered[0],
            detector_name=self.name,
        )
