"""Visual face image quality assessment for ERS."""

from __future__ import annotations

import io
from typing import Tuple

import numpy as np
from PIL import Image
from scipy.signal import convolve2d

from eon_ers.contracts import QualityAssessment
from eon_ers.types import Modality, QualityGrade

# Discrete 3x3 Laplacian kernel for sharpness / blur estimation
LAPLACIAN_KERNEL = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)


class FaceQualityEvaluator:
    """Evaluates resolution, lighting, sharpness, and integrity of facial image inputs."""

    def __init__(
        self,
        min_resolution: Tuple[int, int] = (48, 48),
        max_dimension: int = 1920,
        blur_threshold: float = 30.0,
        min_brightness: float = 15.0,
        max_brightness: float = 245.0,
    ) -> None:
        self.min_resolution = min_resolution
        self.max_dimension = max_dimension
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness

    def evaluate(self, image_bytes: bytes) -> tuple[QualityAssessment, Image.Image | None]:
        """Assess image data and return quality report along with decoded PIL Image if valid."""
        reasons: list[str] = []
        metrics: dict[str, float] = {}

        if not image_bytes:
            return (
                QualityAssessment(
                    modality=Modality.FACIAL,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={"size_bytes": 0.0},
                    is_acceptable=False,
                    reasons=["Empty image payload buffer"],
                ),
                None,
            )

        try:
            pil_img = Image.open(io.BytesIO(image_bytes))
            pil_img.load()
        except Exception as exc:
            return (
                QualityAssessment(
                    modality=Modality.FACIAL,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={"size_bytes": float(len(image_bytes))},
                    is_acceptable=False,
                    reasons=[f"Image decode failed: {exc}"],
                ),
                None,
            )

        width, height = pil_img.size
        metrics["width"] = float(width)
        metrics["height"] = float(height)

        # 1. Resolution check
        min_w, min_h = self.min_resolution
        if width < min_w or height < min_h:
            reasons.append(f"Resolution {width}x{height} is below minimum required {min_w}x{min_h}")

        if width > self.max_dimension or height > self.max_dimension:
            reasons.append(
                f"Resolution {width}x{height} exceeds maximum dimension {self.max_dimension}"
            )

        # Convert to grayscale for illumination & blur checks
        gray_img = pil_img.convert("L")
        gray_arr = np.array(gray_img, dtype=np.float32)

        # 2. Brightness / Contrast check
        mean_brightness = float(np.mean(gray_arr))
        metrics["mean_brightness"] = mean_brightness
        contrast_std = float(np.std(gray_arr))
        metrics["contrast_std"] = contrast_std

        if mean_brightness < self.min_brightness:
            reasons.append(
                f"Image is severely underexposed (mean brightness {mean_brightness:.1f})"
            )
        elif mean_brightness > self.max_brightness:
            reasons.append(f"Image is severely overexposed (mean brightness {mean_brightness:.1f})")

        if contrast_std < 5.0:
            reasons.append(f"Image has insufficient contrast (std dev {contrast_std:.1f})")

        # 3. Motion blur / sharpness evaluation (Laplacian variance)
        # Downscale large images before convolution to keep CPU cost minimal
        h, w = gray_arr.shape
        if max(h, w) > 256:
            scale = 256.0 / max(h, w)
            small_img = gray_img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
            conv_arr = np.array(small_img, dtype=np.float32)
        else:
            conv_arr = gray_arr

        lap = convolve2d(conv_arr, LAPLACIAN_KERNEL, mode="valid")
        blur_variance = float(np.var(lap))
        metrics["blur_variance"] = blur_variance

        if blur_variance < self.blur_threshold:
            reasons.append(
                f"Image is degraded by motion blur (Laplacian variance {blur_variance:.1f} < {self.blur_threshold})"
            )

        # Determine composite score & grade
        score = 1.0
        if reasons:
            # Degrade score according to defects
            score = max(0.1, 1.0 - 0.25 * len(reasons))
            if any("Resolution" in r and "below minimum" in r for r in reasons):
                score = 0.0
            if any("decode failed" in r for r in reasons):
                score = 0.0

        if score >= 0.75:
            grade = QualityGrade.EXCELLENT
            is_acceptable = True
        elif score >= 0.45:
            grade = QualityGrade.ACCEPTABLE
            is_acceptable = True
        elif score > 0.0:
            grade = QualityGrade.DEGRADED
            is_acceptable = False
        else:
            grade = QualityGrade.UNUSABLE
            is_acceptable = False

        return (
            QualityAssessment(
                modality=Modality.FACIAL,
                grade=grade,
                score=score,
                metrics=metrics,
                is_acceptable=is_acceptable,
                reasons=reasons,
            ),
            pil_img,
        )
