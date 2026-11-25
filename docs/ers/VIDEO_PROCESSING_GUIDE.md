# Bounded Video Processing Guide

## Streaming Architecture (`eon_ers.video`)
Video uploads never decode entire streams into unbounded RAM:
1. `VideoDecoder`: validates byte limit (`video_max_bytes`, default 50 MB), yields individual frames from pure-CPU supported containers (RIFF AVI MJPEG, animated GIF, animated WEBP), skips individually corrupted chunks while recovering valid frames, and fails closed (`ERSUnsupportedCodecError`) on proprietary compressed MP4/WebM streams when external FFmpeg/OpenCV backends are absent.
2. `FrameSampler`: enforces `video_sample_fps` (`2.0`), skips near-duplicate frames (`duplicate_mae_threshold`), and halts at `video_max_frames` (`120`).
3. `SessionFaceTracker`: assigns ephemeral IoU tracks (`track-0..k`) without facial recognition embeddings.
4. `VideoPipeline`: supports `threading.Event` cancellation, progress callbacks, async job storage (`POST /api/v1/analyze/video`, `GET /api/v1/analyze/video/{job_id}`, `DELETE /api/v1/analyze/video/{job_id}`), and strict unvalidated aggregation (`INSUFFICIENT_EVIDENCE` / `MODEL_UNVALIDATED` when frames lack empirically validated models).
