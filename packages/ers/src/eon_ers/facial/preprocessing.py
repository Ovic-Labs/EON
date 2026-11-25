"""Facial image preprocessing, crop validation, alignment, and tensor normalization."""

from __future__ import annotations

import numpy as np
from PIL import Image

from eon_ers.exceptions import ERSInvalidMediaError


class FacialPreprocessor:
    """Preprocesses and normalizes decoded facial images into validated ONNX input tensors."""

    def __init__(
        self,
        target_size: tuple[int, int] = (64, 64),
        mean: float = 0.0,
        std: float = 1.0,
        channels: int = 1,
    ) -> None:
        if target_size[0] < 8 or target_size[1] < 8:
            raise ValueError("Target face preprocessing size must be at least (8, 8).")
        if std <= 0.0:
            raise ValueError("Normalization std must be strictly positive.")
        if channels not in (1, 3):
            raise ValueError("Supported channels are 1 (grayscale) or 3 (RGB).")
        self.target_size = target_size
        self.mean = float(mean)
        self.std = float(std)
        self.channels = channels

    @staticmethod
    def align_crop(
        pil_img: Image.Image,
        left_eye: tuple[float, float] | None = None,
        right_eye: tuple[float, float] | None = None,
    ) -> Image.Image:
        """Rotate crop to level eye landmarks horizontally when eye coordinates are available."""
        if left_eye is None or right_eye is None:
            return pil_img
        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        if abs(dx) < 1e-6:
            return pil_img
        angle_deg = float(np.degrees(np.arctan2(dy, dx)))
        if abs(angle_deg) < 1.5 or abs(angle_deg) > 45.0:
            return pil_img
        return pil_img.rotate(angle_deg, resample=Image.Resampling.BILINEAR)

    def preprocess(
        self,
        pil_img: Image.Image,
        face_bbox: tuple[int, int, int, int] | None = None,
        *,
        left_eye: tuple[float, float] | None = None,
        right_eye: tuple[float, float] | None = None,
    ) -> np.ndarray:
        """Crop, optionally align, resize, and normalize image into a validated float32 NCHW tensor."""
        w, h = pil_img.size
        if w < 1 or h < 1:
            raise ERSInvalidMediaError("Cannot preprocess zero-sized image.")

        if face_bbox is not None:
            x_min, y_min, x_max, y_max = face_bbox
            x_min = max(0, min(x_min, w - 1))
            y_min = max(0, min(y_min, h - 1))
            x_max = max(x_min + 1, min(x_max, w))
            y_max = max(y_min + 1, min(y_max, h))
            if x_max <= x_min or y_max <= y_min:
                raise ERSInvalidMediaError(f"Invalid facial crop coordinates: {face_bbox}.")
            cropped = pil_img.crop((x_min, y_min, x_max, y_max))
        else:
            cropped = pil_img

        aligned = self.align_crop(cropped, left_eye=left_eye, right_eye=right_eye)
        resized = aligned.resize(self.target_size, Image.Resampling.BILINEAR)

        if self.channels == 1:
            converted = resized.convert("L")
            arr = np.array(converted, dtype=np.float32) / 255.0
            arr = (arr - self.mean) / self.std
            tensor = np.expand_dims(np.expand_dims(arr, axis=0), axis=0)
        else:
            converted = resized.convert("RGB")
            arr = np.array(converted, dtype=np.float32) / 255.0
            arr = (arr - self.mean) / self.std
            tensor = np.expand_dims(np.transpose(arr, (2, 0, 1)), axis=0)

        if not np.isfinite(tensor).all():
            raise ERSInvalidMediaError("Preprocessed facial input tensor contains NaN or Inf.")
        return tensor.astype(np.float32, copy=False)
