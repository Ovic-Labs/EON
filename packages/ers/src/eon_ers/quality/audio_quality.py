"""Acoustic speech signal quality assessment for ERS."""

from __future__ import annotations

import io
import wave

import numpy as np

from eon_ers.contracts import QualityAssessment
from eon_ers.types import Modality, QualityGrade


class AudioQualityEvaluator:
    """Evaluates sample rate, SNR, clipping, duration, and silence in audio inputs."""

    def __init__(
        self,
        expected_sample_rate: int = 16000,
        min_duration_seconds: float = 0.2,
        max_duration_seconds: float = 10.0,
        min_snr_db: float = 3.0,
        silence_threshold_db: float = -45.0,
        clipping_threshold: float = 0.05,
    ) -> None:
        self.expected_sample_rate = expected_sample_rate
        self.min_duration_seconds = min_duration_seconds
        self.max_duration_seconds = max_duration_seconds
        self.min_snr_db = min_snr_db
        self.silence_threshold_db = silence_threshold_db
        self.clipping_threshold = clipping_threshold

    def decode_audio_bytes(
        self, audio_bytes: bytes, explicit_sample_rate: int | None = None
    ) -> tuple[np.ndarray, int]:
        """Decode raw WAV container bytes or headerless int16 PCM bytes to float32 numpy array."""
        if not audio_bytes:
            raise ValueError("Audio payload buffer is empty")

        # Check for RIFF WAV header
        if audio_bytes.startswith(b"RIFF"):
            with io.BytesIO(audio_bytes) as bio:
                with wave.open(bio, "rb") as wf:
                    sr = wf.getframerate()
                    n_channels = wf.getnchannels()
                    sampwidth = wf.getsampwidth()
                    n_frames = wf.getnframes()
                    raw_frames = wf.readframes(n_frames)

                    if sampwidth == 2:
                        samples = (
                            np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32) / 32768.0
                        )
                    elif sampwidth == 4:
                        samples = (
                            np.frombuffer(raw_frames, dtype=np.int32).astype(np.float32)
                            / 2147483648.0
                        )
                    elif sampwidth == 1:
                        samples = (
                            np.frombuffer(raw_frames, dtype=np.uint8).astype(np.float32) - 128.0
                        ) / 128.0
                    else:
                        raise ValueError(f"Unsupported WAV sample width: {sampwidth} bytes")

                    if n_channels > 1:
                        samples = samples.reshape(-1, n_channels).mean(axis=1)

                    return samples, sr

        # Headerless raw PCM signed 16-bit
        sr = explicit_sample_rate or self.expected_sample_rate
        samples = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        return samples, sr

    def evaluate(
        self, audio_bytes: bytes, explicit_sample_rate: int | None = None
    ) -> tuple[QualityAssessment, np.ndarray | None, int]:
        """Assess audio data quality, returning QualityAssessment and decoded normalized float32 waveform."""
        reasons: list[str] = []
        metrics: dict[str, float] = {}

        if not audio_bytes:
            return (
                QualityAssessment(
                    modality=Modality.SPEECH,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={"size_bytes": 0.0},
                    is_acceptable=False,
                    reasons=["Empty audio payload buffer"],
                ),
                None,
                0,
            )

        try:
            samples, sample_rate = self.decode_audio_bytes(audio_bytes, explicit_sample_rate)
        except Exception as exc:
            return (
                QualityAssessment(
                    modality=Modality.SPEECH,
                    grade=QualityGrade.UNUSABLE,
                    score=0.0,
                    metrics={"size_bytes": float(len(audio_bytes))},
                    is_acceptable=False,
                    reasons=[f"Audio decode failed: {exc}"],
                ),
                None,
                0,
            )

        n_samples = len(samples)
        duration = n_samples / max(1, sample_rate)
        metrics["sample_rate"] = float(sample_rate)
        metrics["duration_seconds"] = float(duration)
        metrics["num_samples"] = float(n_samples)

        # 1. Sample rate check
        if sample_rate < 8000:
            reasons.append(f"Sample rate {sample_rate} Hz is too low for acoustic analysis")

        # 2. Duration check
        if duration < self.min_duration_seconds:
            reasons.append(
                f"Audio duration {duration:.2f}s is shorter than minimum {self.min_duration_seconds:.2f}s"
            )
        elif duration > self.max_duration_seconds:
            reasons.append(
                f"Audio duration {duration:.2f}s exceeds maximum {self.max_duration_seconds:.2f}s"
            )

        # 3. Energy & Silence check
        rms = float(np.sqrt(np.mean(samples**2))) + 1e-9
        rms_db = float(20.0 * np.log10(rms))
        metrics["rms_db"] = rms_db

        if rms_db < self.silence_threshold_db:
            reasons.append(
                f"Audio frame contains silence or insufficient acoustic energy ({rms_db:.1f} dB)"
            )

        # 4. Clipping check
        clipping_fraction = float(np.mean(np.abs(samples) > 0.98))
        metrics["clipping_ratio"] = clipping_fraction
        if clipping_fraction > self.clipping_threshold:
            reasons.append(
                f"Audio is clipped or distorted ({clipping_fraction * 100:.1f}% samples clipped)"
            )

        # 5. Signal-to-Noise Ratio (SNR) estimation via frame energy percentiles
        frame_len = max(128, int(0.025 * sample_rate))  # 25ms
        hop_len = max(64, int(0.010 * sample_rate))  # 10ms
        num_frames = max(1, (n_samples - frame_len) // hop_len + 1)
        if num_frames > 2:
            frame_energies = [
                np.sum(samples[i * hop_len : i * hop_len + frame_len] ** 2)
                for i in range(num_frames)
            ]
            p10 = float(np.percentile(frame_energies, 10)) + 1e-9
            p90 = float(np.percentile(frame_energies, 90)) + 1e-9
            snr_db = float(10.0 * np.log10(p90 / p10))
        else:
            snr_db = 10.0
        metrics["snr_db"] = snr_db

        if snr_db < self.min_snr_db and rms_db >= self.silence_threshold_db:
            reasons.append(
                f"Signal-to-noise ratio is too low for reliable prosody analysis ({snr_db:.1f} dB < {self.min_snr_db} dB)"
            )

        # Compute composite quality score
        score = 1.0
        if reasons:
            score = max(0.1, 1.0 - 0.25 * len(reasons))
            if any("decode failed" in r for r in reasons):
                score = 0.0
            if any("shorter than minimum" in r for r in reasons):
                score = 0.0
            if any("silence" in r for r in reasons):
                score = 0.2

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
                modality=Modality.SPEECH,
                grade=grade,
                score=score,
                metrics=metrics,
                is_acceptable=is_acceptable,
                reasons=reasons,
            ),
            samples,
            sample_rate,
        )
