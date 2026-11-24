"""Observable regional facial image feature extraction for ERS.

NOTE ON SCIENTIFIC RIGOR:
These descriptors compute raw regional pixel variance, gradients, and contrast.
They are NOT calibrated or empirically validated Facial Action Coding System (FACS) Action Units.
They are explicitly classified as EXPERIMENTAL regional image descriptors.
"""

from __future__ import annotations

import numpy as np
from PIL import Image


class ExperimentalRegionalFeatureExtractor:
    """Extracts non-biometric, experimental regional contrast and gradient descriptors from face crops.

    Computes raw morphological region statistics:
    - regional_brow_gradient: vertical intensity change across the upper forehead/brow
    - regional_central_forehead_contrast: luminance standard deviation in the central forehead
    - regional_mouth_corner_contrast: intensity variance at left/right oral commissures
    - regional_subocular_contrast: contrast variance in the infraorbital region
    - regional_oral_cavity_darkness: inverse mean illumination in the central oral aperture
    - regional_nasal_gradient: horizontal texture variance across the nasal bridge

    These are heuristic descriptors only, not validated Action Units.
    """

    def extract_features(self, pil_img: Image.Image) -> dict[str, float]:
        """Extract regional intensity descriptors from normalized face crop."""
        gray = pil_img.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
        arr = np.array(gray, dtype=np.float32) / 255.0

        # Partition face into spatial anatomical regions:
        # Upper third: Forehead and brow region (rows 0..24)
        # Middle third: Eyes and nasal bridge (rows 20..44)
        # Lower third: Oral region and chin (rows 40..64)
        brow_region = arr[4:22, 12:52]
        eye_region = arr[18:34, 8:56]
        nose_region = arr[28:44, 20:44]
        mouth_region = arr[42:60, 12:52]

        # 1. Brow vertical gradient
        brow_dy = np.abs(np.diff(brow_region, axis=0))
        brow_gradient = float(np.clip(np.mean(brow_dy) * 6.0, 0.0, 1.0))

        # 2. Central forehead contrast
        center_forehead = arr[2:14, 24:40]
        forehead_contrast = float(np.clip(np.std(center_forehead) * 4.0, 0.0, 1.0))

        # 3. Mouth corner contrast
        left_corner = mouth_region[:, :8]
        right_corner = mouth_region[:, -8:]
        center_mouth = mouth_region[:, 14:26]
        corner_contrast = float(np.std(left_corner) + np.std(right_corner))
        mouth_darkness = float(1.0 - np.mean(center_mouth))
        mouth_corner_contrast = float(
            np.clip(corner_contrast * 2.5 + mouth_darkness * 0.3, 0.0, 1.0)
        )

        # 4. Infraorbital (subocular) contrast
        under_eyes = eye_region[10:, :]
        subocular_contrast = float(np.clip(np.std(under_eyes) * 3.5, 0.0, 1.0))

        # 5. Oral aperture darkness
        jaw_cavity = np.mean(arr[46:58, 20:44])
        oral_cavity_darkness = (
            float(np.clip((0.6 - jaw_cavity) * 2.0, 0.0, 1.0)) if jaw_cavity < 0.6 else 0.0
        )

        # 6. Nasal bridge gradient
        nose_dx = np.abs(np.diff(nose_region, axis=1))
        nasal_gradient = float(np.clip(np.mean(nose_dx) * 7.0, 0.0, 1.0))

        return {
            "regional_brow_gradient": round(brow_gradient, 4),
            "regional_central_forehead_contrast": round(forehead_contrast, 4),
            "regional_subocular_contrast": round(subocular_contrast, 4),
            "regional_nasal_gradient": round(nasal_gradient, 4),
            "regional_mouth_corner_contrast": round(mouth_corner_contrast, 4),
            "regional_oral_cavity_darkness": round(oral_cavity_darkness, 4),
        }

    @staticmethod
    def get_descriptor_metadata() -> dict[str, str | bool]:
        """Metadata describing the feature extractor properties and scientific limitations."""
        return {
            "feature_method": "experimental_regional_descriptors",
            "is_validated_facs": False,
            "is_experimental": True,
            "limitations": (
                "Heuristic regional pixel contrast descriptors only. "
                "Not calibrated or validated Facial Action Coding System (FACS) Action Units."
            ),
        }


# Backwards compatibility alias with clear deprecation notice
FacialFeatureExtractor = ExperimentalRegionalFeatureExtractor
