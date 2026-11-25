# ERS Troubleshooting Guide

| Symptom | Cause | Resolution |
|---|---|---|
| `Unsupported model IR version: 14, max supported IR version: 11` | Running Python 3.10 with older `onnxruntime` | Use Python **3.11 or 3.12** with `onnxruntime>=1.23.0`. |
| `HTTP 409 Activation Blocked` on model activate | Model is in `MODEL_LOADED_UNVALIDATED` / `MODEL_REVOKED` | Expected fail-closed safety guard; only empirically validated signed models can be activated. |
| `consent_rejected` or HTTP 403 | Missing, wrong, expired, or revoked `consent_reference` | Register consent (`POST /api/v1/consent`) and pass matching `consent_reference` on every request. |
| `ERSUnsupportedCodecError` on MP3 or MP4 | Pure-CPU host without external FFmpeg/OpenCV codecs | Upload uncompressed WAV PCM / JPEG / PNG / RIFF AVI (MJPEG) / animated GIF or WEBP. |
| `getUserMedia` denied in Live ERS | Browser requires HTTPS (or `localhost` / `127.0.0.1`) & explicit user click | Access dashboard via `https://` or `http://127.0.0.1:8000` and allow browser permissions. |
| `429 Rate Limit Exceeded` | Exceeded `rate_limit_requests_per_minute` | Lower FPS or increase `ERSConfig.rate_limit_requests_per_minute`. |
