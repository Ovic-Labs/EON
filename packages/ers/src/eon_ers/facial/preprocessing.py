"""Facial image preprocessing for ERS."""

from __future__ import annotations

import numpy as np
from PIL import Image


class FacialPreprocessor:
    """Preprocesses and normalizes decoded facial images for inference."""

    def __init__(self, target_size: tuple[int, int] = (64, 64)) -> None:
        self.target_size = target_size

    def preprocess(
        self, pil_img: Image.Image, face_bbox: tuple[int, int, int, int] | None = None
    ) -> np.ndarray:
        """Crop face region if provided, resize to target size, and normalize to [0, 1].

        Returns:
            np.ndarray: Float32 array of shape (1, 1, H, W) for grayscale models or (1, 3, H, W).
        """
        if face_bbox is not None:
            x_min, y_min, x_max, y_max = face_bbox
            # Clamp to bounds
            w, h = pil_img.size
            x_min = max(0, min(x_min, w - 1))
            y_min = max(0, min(y_min, h - 1))
            x_max = max(x_min + 1, min(x_max, w))
            y_max = max(y_min + 1, min(y_max, h))
            cropped = pil_img.crop((x_min, y_min, x_max, y_max))
        else:
            cropped = pil_img

        # Resize to target input dimensions
        resized = cropped.resize(self.target_size, Image.Resampling.BILINEAR)
        gray = resized.convert("L")
        arr = np.array(gray, dtype=np.float32) / 255.0

        # Reshape to NCHW: (1, 1, H, W)
        tensor = np.expand_dims(np.expand_dims(arr, axis=0), axis=0)
        return tensor
