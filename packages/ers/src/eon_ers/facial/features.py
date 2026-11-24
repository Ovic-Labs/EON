"""Observable facial expression feature extraction for ERS."""

from __future__ import annotations

import numpy as np
from PIL import Image


class FacialFeatureExtractor:
    """Extracts observable physical Action Units and geometric indicators from face crops.

    Computes non-biometric, observable geometric signals:
    - AU06 (Cheek raiser / squint)
    - AU12 (Lip corner puller / smile)
    - AU04 (Brow lowerer / furrow)
    - AU01 (Inner brow raiser)
    - AU26 (Jaw drop)
    - AU09 (Nose wrinkler)
    """

    def extract_features(self, pil_img: Image.Image) -> dict[str, float]:
        """Extract observable Action Unit indicators from the normalized face image."""
        gray = pil_img.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
        arr = np.array(gray, dtype=np.float32) / 255.0

        # Partition face into morphological regions:
        # Upper third: Forehead and eyebrows (rows 0..24)
        # Middle third: Eyes and nose bridge (rows 20..44)
        # Lower third: Mouth and jaw (rows 40..64)
        brow_region = arr[4:22, 12:52]
        eye_region = arr[18:34, 8:56]
        nose_region = arr[28:44, 20:44]
        mouth_region = arr[42:60, 12:52]

        # 1. Brow furrow / variance (AU04)
        # Vertical gradient in inner brow indicates vertical furrowing
        brow_dy = np.abs(np.diff(brow_region, axis=0))
        au04_score = float(np.clip(np.mean(brow_dy) * 6.0, 0.0, 1.0))

        # 2. Inner brow raise (AU01): elevated brightness / contrast in central upper forehead
        center_forehead = arr[2:14, 24:40]
        au01_score = float(np.clip(np.std(center_forehead) * 4.0, 0.0, 1.0))

        # 3. Smile curvature / lip corner elevation (AU12)
        # Ratio of mouth corner illumination and horizontal gradient
        left_corner = mouth_region[:, :8]
        right_corner = mouth_region[:, -8:]
        center_mouth = mouth_region[:, 14:26]
        corner_contrast = float(np.std(left_corner) + np.std(right_corner))
        mouth_darkness = float(1.0 - np.mean(center_mouth))
        au12_score = float(np.clip(corner_contrast * 2.5 + mouth_darkness * 0.3, 0.0, 1.0))

        # 4. Cheek raiser (AU06): lateral contrast under eyes
        under_eyes = eye_region[10:, :]
        au06_score = float(np.clip(np.std(under_eyes) * 3.5, 0.0, 1.0))

        # 5. Jaw drop / open mouth (AU26): dark cavity in center mouth
        jaw_cavity = np.mean(arr[46:58, 20:44])
        au26_score = float(np.clip((0.6 - jaw_cavity) * 2.0, 0.0, 1.0)) if jaw_cavity < 0.6 else 0.0

        # 6. Nose wrinkler (AU09): high frequency texture around nasal bridge
        nose_dx = np.abs(np.diff(nose_region, axis=1))
        au09_score = float(np.clip(np.mean(nose_dx) * 7.0, 0.0, 1.0))

        return {
            "AU01_inner_brow_raiser": round(au01_score, 4),
            "AU04_brow_lowerer": round(au04_score, 4),
            "AU06_cheek_raiser": round(au06_score, 4),
            "AU09_nose_wrinkler": round(au09_score, 4),
            "AU12_lip_corner_puller": round(au12_score, 4),
            "AU26_jaw_drop": round(au26_score, 4),
        }
