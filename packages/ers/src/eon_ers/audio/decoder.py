"""Bounded CPU audio container decoder supporting WAV and headerless PCM."""

from __future__ import annotations

import io
import wave

import numpy as np

from eon_ers.exceptions import (
    ERSCorruptedMediaError,
    ERSInvalidMediaError,
    ERSUnsupportedCodecError,
)


class AudioDecoder:
    """Decodes WAV (8/16/24/32-bit PCM) or raw signed 16-bit PCM into mono float32 waveforms."""

    def __init__(self, max_payload_bytes: int = 20 * 1024 * 1024) -> None:
        self.max_payload_bytes = max_payload_bytes

    @staticmethod
    def _detect_compressed_container(audio_bytes: bytes) -> str | None:
        head = audio_bytes[:16]
        if head.startswith(b"ID3") or (
            len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0
        ):
            return "MP3"
        if head.startswith(b"OggS"):
            return "OGG/Opus/Vorbis"
        if head.startswith(b"fLaC"):
            return "FLAC"
        if b"ftyp" in head[:12]:
            return "MP4/M4A"
        if head.startswith(b"\x1aE\xdf\xa3"):
            return "WebM/Matroska"
        return None

    def decode(
        self, audio_bytes: bytes, explicit_sample_rate: int | None = None
    ) -> tuple[np.ndarray, int]:
        """Decode raw audio bytes to normalized mono float32 samples in [-1.0, 1.0]."""
        if not audio_bytes:
            raise ERSInvalidMediaError("Audio payload buffer is empty.")
        if len(audio_bytes) > self.max_payload_bytes:
            raise ERSInvalidMediaError(
                f"Audio payload size {len(audio_bytes)} exceeds max allowed {self.max_payload_bytes} bytes."
            )

        compressed = self._detect_compressed_container(audio_bytes)
        if compressed is not None:
            raise ERSUnsupportedCodecError(
                f"Compressed audio container '{compressed}' requires uncompressed RIFF/WAV or PCM encoding "
                "when optional external codec backends are unavailable.",
                context={"detected_format": compressed},
            )

        if audio_bytes.startswith(b"RIFF"):
            try:
                with io.BytesIO(audio_bytes) as bio:
                    with wave.open(bio, "rb") as wf:
                        sr = wf.getframerate()
                        n_channels = wf.getnchannels()
                        sampwidth = wf.getsampwidth()
                        n_frames = wf.getnframes()
                        raw_frames = wf.readframes(n_frames)
            except Exception as exc:
                raise ERSCorruptedMediaError(f"Invalid or corrupted WAV container: {exc}") from exc

            if n_channels < 1 or sr < 1000:
                raise ERSCorruptedMediaError(
                    f"Invalid WAV metadata (channels={n_channels}, sample_rate={sr})."
                )

            if sampwidth == 2:
                samples = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 4:
                samples = (
                    np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32) / 2147483648.0
                )
            elif sampwidth == 3:
                # Decode packed 24-bit signed little-endian PCM
                raw_u8 = np.frombuffer(raw_frames, dtype=np.uint8)
                usable = (len(raw_u8) // 3) * 3
                triplets = raw_u8[:usable].reshape(-1, 3).astype(np.int32)
                vals = triplets[:, 0] | (triplets[:, 1] << 8) | (triplets[:, 2] << 16)
                vals = np.where(vals >= 0x800000, vals - 0x1000000, vals)
                samples = vals.astype(np.float32) / 8388608.0
            elif sampwidth == 1:
                samples = (
                    np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0
                ) / 128.0
            else:
                raise ERSUnsupportedCodecError(f"Unsupported WAV sample width: {sampwidth} bytes")

            if n_channels > 1:
                usable_len = (len(samples) // n_channels) * n_channels
                samples = samples[:usable_len].reshape(-1, n_channels).mean(axis=1)
            return np.nan_to_num(samples, nan=0.0, posinf=1.0, neginf=-1.0), sr

        sr = explicit_sample_rate or 16000
        if sr < 1000:
            raise ERSInvalidMediaError(f"Invalid sample rate: {sr} Hz.")
        usable_bytes = (len(audio_bytes) // 2) * 2
        if usable_bytes == 0:
            raise ERSCorruptedMediaError("Raw PCM payload contains fewer than 2 bytes.")
        samples = (
            np.frombuffer(audio_bytes[:usable_bytes], dtype=np.int16).astype(np.float32) / 32768.0
        )
        return np.nan_to_num(samples, nan=0.0, posinf=1.0, neginf=-1.0), sr
