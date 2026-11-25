# Model Registry & Artifact Security Guide

## Lifecycle States (`eon_ers.models.ModelRegistry`)
- `MODEL_DISCOVERED` — Manifest scanned from repository directory.
- `MODEL_LOADED_UNVALIDATED` — Manifest and SHA-256 valid, but lacks empirical qualification (`is_validated=False`).
- `MODEL_VALIDATED` — Artifact SHA-256 matches `ModelValidationRecord`, compatibility passes (`onnx`, modality, CPU support, semantic major version), empirical qualification holds, and Ed25519 proof verifies cleanly against `TrustedKeyRegistry`.
- `MODEL_REJECTED` — Manifest incompatibility, hash mismatch, or invalid cryptographic signature.
- `MODEL_REVOKED` — Administrator-revoked (`registry.revoke_model(id, reason)`); cannot be activated.

## Fail-Closed Activation Guard
Calling `registry.activate_model(model_id)` or `POST /api/v1/models/{model_id}/activate` raises `ERSSafetyViolationError` (HTTP 409) unless the model is in `MODEL_VALIDATED`.
