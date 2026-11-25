# Vocal Affect Analysis Guide

## Pipeline Stages (`eon_ers.audio` & `eon_ers.speech`)
1. `AudioDecoder`: decodes RIFF WAV (8/16/24/32-bit PCM, multi-channel average to mono) and raw int16 PCM; explicitly rejects compressed MP3/OGG/FLAC/MP4 containers with `ERSUnsupportedCodecError` when external codecs are absent.
2. `AudioResampler`: polyphase CPU resampling to `ERSConfig.audio_sample_rate` (`16000` Hz).
3. `AudioQualityEvaluator`: validates duration (`0.2s`–`10.0s`), sample rate (`>= 8000 Hz`), clipping ratio, RMS energy (`silence_threshold_db=-45.0`), and noise-percentile SNR (`>= 3.0 dB`).
4. `VoiceActivityDetector`: separates speech segments from silence/background noise (`voice_activity`, `speech_ratio`), returning `INSUFFICIENT_EVIDENCE` for silent clips.
5. `AcousticFeatureExtractor`: F0 autocorrelation pitch statistics, RMS contour, ZCR, spectral centroid, and 13-band MFCC descriptors with NaN/Inf/empty-buffer hardening.
6. `ONNXSpeechModelAdapter` / `ExperimentalAcousticProsodyAdapter`: CPU inference with strict unvalidated suppression and media payload scrubbing.
