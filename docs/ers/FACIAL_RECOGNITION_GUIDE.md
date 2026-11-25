# Facial Expression Recognition Guide

## Pipeline Stages (`eon_ers.facial.FacialPipeline`)
1. Payload size check (`max_image_bytes`, default 10 MB) & decoding (`JPEG`, `PNG`, `WEBP`, `BMP`, `TIFF`, `GIF`).
2. `FaceQualityEvaluator`: checks resolution (`min_face_resolution=(48, 48)`), `max_image_dimension`, mean brightness, contrast std, Laplacian blur variance.
3. `HeuristicFaceDetector`: pure-CPU spatial gradient variance segmentation detecting `0`, `1`, or `N` faces (`NO_FACE_DETECTED`, `SINGLE_FACE_DETECTED`, `MULTIPLE_FACES_DETECTED`), boundary partial flags (`is_partial_boundary`), and ephemeral session `face-0..k` IDs (no biometric facial identification).
4. `HeuristicLandmarkDetector`: 5-point canonical facial reference landmarks for eye-level alignment.
5. `FacialPreprocessor`: crops to primary bounding box, aligns horizontally by eye angle, resizes to `(64, 64)`, normalizes `[0, 1]` float32 NCHW, and checks tensor finiteness.
6. `ONNXFacialModelAdapter` / `ExperimentalRegionalFeatureAdapter`: runs local CPU inference and enforces status precedence (`FAILED > MODEL_UNAVAILABLE > MODEL_UNVALIDATED > INSUFFICIENT_EVIDENCE > DEGRADED > OK`).
7. Immediate `inp.scrub_media_payload()` buffer clearing.
