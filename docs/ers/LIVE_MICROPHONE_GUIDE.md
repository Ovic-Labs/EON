# Live Microphone Integration Guide

## Capture Architecture
Browser audio capture activates exclusively upon user click ("Start Microphone") via `navigator.mediaDevices.getUserMedia({ audio: ... })` and `AudioContext` (`sampleRate: 16000`).

## Processing Flow
1. Real-time PCM int16 frames (`4096` samples batched over 4 buffers) compute client RMS level meter and silence indicator.
2. Encoded PCM chunks transmit via WebSocket `audio` messages carrying `sample_rate` and `consent_reference`.
3. Server `AudioDecoder` + `VoiceActivityDetector` + `AudioQualityEvaluator` reject silent/noise-only frames (`INSUFFICIENT_EVIDENCE`) without fabricating emotions.
4. Transcription is disabled (`voice/speech affect` uses acoustic prosody features only, never ASR speech-to-text unless separately consented).

## Manual Hardware Qualification Checklist
1. Verify microphone selection dropdown and real-time RMS meter deflection while speaking.
2. Verify silence detection displays `(Silence)` when muted and backend returns `insufficient_evidence` on silent audio.
3. Verify simultaneous webcam + microphone mode emits multimodal telemetry updates.
4. Verify consent revocation immediately closes `AudioContext` tracks and stops server audio processing.
