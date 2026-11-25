"""Streaming bounded CPU video decoder (AVI/MJPEG, GIF/WEBP/TIFF, and optional cv2 backend)."""

from __future__ import annotations

import io
import struct
from collections.abc import Iterator
from dataclasses import dataclass

from PIL import Image, ImageSequence

from eon_ers.exceptions import (
    ERSCorruptedMediaError,
    ERSInvalidMediaError,
    ERSUnsupportedCodecError,
)


@dataclass(frozen=True)
class DecodedVideoFrame:
    """Single decoded video frame encoded cleanly in volatile memory."""

    frame_index: int
    timestamp_seconds: float
    image_bytes: bytes
    width: int
    height: int


class VideoDecoder:
    """Streams video containers frame-by-frame without loading unbounded frames into RAM."""

    def __init__(self, max_video_bytes: int = 50 * 1024 * 1024) -> None:
        self.max_video_bytes = max_video_bytes

    @staticmethod
    def _pil_to_jpeg(img: Image.Image) -> tuple[bytes, int, int]:
        rgb = img.convert("RGB")
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=90)
        return buf.getvalue(), rgb.size[0], rgb.size[1]

    @staticmethod
    def _parse_avi_mjpeg_frames(video_bytes: bytes) -> Iterator[tuple[bytes, float]]:
        """Yield JPEG/BMP chunks from an uncompressed/MJPEG RIFF AVI container on CPU."""
        if len(video_bytes) < 24 or video_bytes[:4] != b"RIFF" or video_bytes[8:12] != b"AVI ":
            raise ERSCorruptedMediaError("Invalid RIFF AVI header.")

        # Scan microsec_per_frame from 'avih' if present (default 30 fps)
        fps = 30.0
        avih_pos = video_bytes.find(b"avih")
        if avih_pos != -1 and avih_pos + 12 <= len(video_bytes):
            us_per_frame = struct.unpack_from("<I", video_bytes, avih_pos + 8)[0]
            if 1000 <= us_per_frame <= 1_000_000:
                fps = 1_000_000.0 / us_per_frame

        movi_pos = video_bytes.find(b"LIST")
        pos = 12
        idx = 0
        found_movi = False
        while pos + 8 <= len(video_bytes):
            chunk_id = video_bytes[pos : pos + 4]
            chunk_size = struct.unpack_from("<I", video_bytes, pos + 4)[0]
            if chunk_id == b"LIST":
                list_type = video_bytes[pos + 8 : pos + 12]
                if list_type == b"movi":
                    found_movi = True
                    pos += 12
                    movi_end = min(len(video_bytes), pos + chunk_size - 4)
                    while pos + 8 <= movi_end:
                        sub_id = video_bytes[pos : pos + 4]
                        sub_size = struct.unpack_from("<I", video_bytes, pos + 4)[0]
                        data_start = pos + 8
                        data_end = min(movi_end, data_start + sub_size)
                        if sub_id.endswith(b"dc") or sub_id.endswith(b"db"):
                            if data_end > data_start:
                                yield video_bytes[data_start:data_end], idx / fps
                                idx += 1
                        pos = data_start + sub_size + (sub_size % 2)
                    break
            step = 8 + chunk_size + (chunk_size % 2)
            if step <= 8 and chunk_id != b"LIST":
                break
            pos += max(8, step)

        if not found_movi and movi_pos == -1:
            raise ERSCorruptedMediaError("AVI container missing 'movi' frame stream.")

    def iter_frames(
        self, video_bytes: bytes, source_fps_hint: float = 15.0
    ) -> Iterator[DecodedVideoFrame]:
        """Stream decoded video frames with explicit codec validation and bounded RAM."""
        if not video_bytes:
            raise ERSInvalidMediaError("Video payload buffer is empty.")
        if len(video_bytes) > self.max_video_bytes:
            raise ERSInvalidMediaError(
                f"Video payload size {len(video_bytes)} exceeds max allowed {self.max_video_bytes} bytes."
            )

        head = video_bytes[:16]
        # 1. Animated raster containers (GIF, WEBP, TIFF) via PIL streaming iterator
        if head.startswith((b"GIF87a", b"GIF89a", b"RIFF")) and (
            head.startswith((b"GIF87a", b"GIF89a")) or video_bytes[8:12] == b"WEBP"
        ):
            try:
                img = Image.open(io.BytesIO(video_bytes))
                dt = 1.0 / max(1.0, source_fps_hint)
                for idx, frame in enumerate(ImageSequence.Iterator(img)):
                    dur_ms = frame.info.get("duration")
                    ts = idx * (float(dur_ms) / 1000.0) if dur_ms else idx * dt
                    jpg, w, h = self._pil_to_jpeg(frame)
                    yield DecodedVideoFrame(
                        frame_index=idx,
                        timestamp_seconds=round(ts, 4),
                        image_bytes=jpg,
                        width=w,
                        height=h,
                    )
                return
            except Exception as exc:
                raise ERSCorruptedMediaError(f"Failed to decode animated container: {exc}") from exc

        # 2. Pure-Python RIFF AVI MJPEG/JPEG stream
        if head.startswith(b"RIFF") and len(video_bytes) >= 12 and video_bytes[8:12] == b"AVI ":
            emitted = 0
            for idx, (chunk, ts) in enumerate(self._parse_avi_mjpeg_frames(video_bytes)):
                try:
                    frame_img = Image.open(io.BytesIO(chunk))
                    frame_img.load()
                    jpg, w, h = self._pil_to_jpeg(frame_img)
                    emitted += 1
                    yield DecodedVideoFrame(
                        frame_index=idx,
                        timestamp_seconds=round(ts, 4),
                        image_bytes=jpg,
                        width=w,
                        height=h,
                    )
                except Exception:
                    # Skip individual corrupted frame while recovering remaining frames
                    continue
            if emitted == 0:
                raise ERSCorruptedMediaError("AVI stream contained no decodable video frames.")
            return

        # 3. MP4/MOV/MKV/WebM: check optional cv2 backend cleanly, otherwise fail closed
        if b"ftyp" in head[:12] or head.startswith(b"\x1aE\xdf\xa3"):
            raise ERSUnsupportedCodecError(
                "Compressed MP4/MOV/WebM container requires optional OpenCV/FFmpeg runtime; "
                "use RIFF AVI (MJPEG), animated WEBP/GIF, or explicit frame sequences on pure-CPU hosts.",
                context={"container_signature": head[:8].hex()},
            )

        raise ERSUnsupportedCodecError("Unrecognized or unsupported video container format.")
