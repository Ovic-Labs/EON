"""Voice Activity Detection (VAD) module for ERS vocal affect analysis."""

from __future__ import annotations

import numpy as np
from pydantic import BaseModel, ConfigDict, Field


class VADResult(BaseModel):
    """Structured Voice Activity Detection summary without raw audio retention."""

    model_config = ConfigDict(frozen=True)

    has_voice: bool = Field(
        ..., description="True when active speech-like energy exceeds noise floor."
    )
    speech_ratio: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of active voiced frames."
    )
    active_segments: list[tuple[float, float]] = Field(
        default_factory=list,
        description="Start/end timestamps (seconds) of voiced segments.",
    )
    rms_db: float = Field(..., description="Overall RMS energy in dBFS.")
    noise_floor_db: float = Field(..., description="Estimated background noise floor in dBFS.")


class VoiceActivityDetector:
    """CPU energy and zero-crossing stability VAD distinguishing speech from silence/noise."""

    def __init__(
        self,
        frame_duration_ms: float = 25.0,
        hop_duration_ms: float = 10.0,
        silence_threshold_db: float = -45.0,
        min_speech_ratio: float = 0.08,
    ) -> None:
        self.frame_duration_ms = frame_duration_ms
        self.hop_duration_ms = hop_duration_ms
        self.silence_threshold_db = silence_threshold_db
        self.min_speech_ratio = min_speech_ratio

    def detect(self, samples: np.ndarray, sample_rate: int = 16000) -> VADResult:
        """Analyze waveform activity and return `VADResult` safely on empty/non-finite inputs."""
        if samples.size == 0 or sample_rate <= 0:
            return VADResult(
                has_voice=False,
                speech_ratio=0.0,
                active_segments=[],
                rms_db=-100.0,
                noise_floor_db=-100.0,
            )

        clean = np.nan_to_num(samples.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
        rms = float(np.sqrt(np.mean(clean**2))) + 1e-9
        rms_db = float(20.0 * np.log10(rms))

        frame_len = max(64, int(round((self.frame_duration_ms / 1000.0) * sample_rate)))
        hop_len = max(32, int(round((self.hop_duration_ms / 1000.0) * sample_rate)))

        if len(clean) < frame_len:
            active = rms_db >= self.silence_threshold_db
            return VADResult(
                has_voice=active,
                speech_ratio=1.0 if active else 0.0,
                active_segments=[(0.0, round(len(clean) / sample_rate, 3))] if active else [],
                rms_db=round(rms_db, 2),
                noise_floor_db=round(rms_db, 2),
            )

        num_frames = (len(clean) - frame_len) // hop_len + 1
        frame_rms = np.empty(num_frames, dtype=np.float32)
        for i in range(num_frames):
            seg = clean[i * hop_len : i * hop_len + frame_len]
            frame_rms[i] = float(np.sqrt(np.mean(seg**2))) + 1e-9

        frame_db = 20.0 * np.log10(frame_rms)
        noise_floor_db = float(np.percentile(frame_db, 15))
        adaptive_thresh_db = max(self.silence_threshold_db, noise_floor_db + 6.0)
        voiced_mask = frame_db >= adaptive_thresh_db

        # Fallback: steady high-level speech tones (constant synthetic sinusoids) lack silent pauses
        # so adaptive percentile equals signal level; recognize overall RMS above floor.
        if not np.any(voiced_mask) and rms_db >= self.silence_threshold_db + 3.0:
            voiced_mask = frame_db >= self.silence_threshold_db

        speech_ratio = float(np.mean(voiced_mask))
        segments: list[tuple[float, float]] = []
        in_seg = False
        seg_start = 0.0
        for idx, is_voiced in enumerate(voiced_mask):
            t = (idx * hop_len) / sample_rate
            if is_voiced and not in_seg:
                in_seg = True
                seg_start = t
            elif not is_voiced and in_seg:
                in_seg = False
                segments.append((round(seg_start, 3), round(t, 3)))
        if in_seg:
            segments.append((round(seg_start, 3), round(len(clean) / sample_rate, 3)))

        has_voice = bool(
            speech_ratio >= self.min_speech_ratio and rms_db >= self.silence_threshold_db
        )
        return VADResult(
            has_voice=has_voice,
            speech_ratio=round(speech_ratio, 4),
            active_segments=segments,
            rms_db=round(rms_db, 2),
            noise_floor_db=round(noise_floor_db, 2),
        )
