"""High-level segmented audio ingestion pipeline wrapping decoder, resampler, VAD, and SpeechPipeline."""

from __future__ import annotations

import io
import wave
from typing import Any

import numpy as np

from eon_ers.audio.decoder import AudioDecoder
from eon_ers.audio.resampler import AudioResampler
from eon_ers.audio.segmentation import AudioSegmenter
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, ERSInput
from eon_ers.speech.pipeline import SpeechPipeline
from eon_ers.speech.voice_activity import VADResult, VoiceActivityDetector
from eon_ers.types import Modality


class AudioPipeline:
    """Processes audio uploads or continuous segments using bounded CPU pipelines."""

    def __init__(
        self,
        config: ERSConfig | None = None,
        speech_pipeline: SpeechPipeline | None = None,
    ) -> None:
        self.config = config or ERSConfig()
        self.decoder = AudioDecoder(max_payload_bytes=self.config.max_audio_bytes)
        self.resampler = AudioResampler()
        self.vad = VoiceActivityDetector(silence_threshold_db=self.config.silence_threshold_db)
        self.segmenter = AudioSegmenter(
            window_seconds=self.config.audio_window_duration_seconds,
            hop_seconds=max(0.5, self.config.audio_window_duration_seconds / 2.0),
        )
        self.speech_pipeline = speech_pipeline or SpeechPipeline(self.config)

    @staticmethod
    def _to_wav_bytes(samples: np.ndarray, sample_rate: int) -> bytes:
        buf = io.BytesIO()
        pcm = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())
        return buf.getvalue()

    def analyze_audio_upload(
        self,
        session_id: str,
        consent_reference: str,
        audio_bytes: bytes,
        sample_rate: int | None = None,
    ) -> dict[str, Any]:
        """Decode, resample, segment, run VAD, and analyze audio upload under bounded CPU limits."""
        raw_samples, src_sr = self.decoder.decode(audio_bytes, explicit_sample_rate=sample_rate)
        target_sr = self.config.audio_sample_rate
        mono = self.resampler.resample(raw_samples, src_sr, target_sr)
        vad_result: VADResult = self.vad.detect(mono, target_sr)
        segments = self.segmenter.segment(mono, target_sr)

        segment_observations: list[EmotionObservation] = []
        for seg in segments:
            seg_wav = self._to_wav_bytes(seg.samples, target_sr)
            inp = ERSInput(
                session_id=session_id,
                modality=Modality.SPEECH,
                consent_reference=consent_reference,
                audio_payload=seg_wav,
                sample_rate=target_sr,
            )
            obs = self.speech_pipeline.process(inp)
            segment_observations.append(obs)

        primary = segment_observations[-1] if segment_observations else None
        return {
            "session_id": session_id,
            "source_sample_rate": src_sr,
            "target_sample_rate": target_sr,
            "duration_seconds": round(len(mono) / max(1, target_sr), 3),
            "vad": vad_result.model_dump(),
            "segments_processed": len(segment_observations),
            "primary_observation": primary,
            "segment_observations": segment_observations,
        }
