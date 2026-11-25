# Security Policy — OVIC EON

## Threat Model & Implemented Controls

- **Model Supply Chain:** `ModelLoader` verifies SHA-256 checksums, ONNX graph validity, completeness of external initializers, modality/framework/version constraints, tensor contracts, and CPU smoke tests before inference. `ModelRegistry` prevents activating unvalidated or revoked models (`MODEL_REVOKED`).
- **Cryptographic Proof Verification:** Holdout evaluation proofs require domain-separated **Ed25519** signatures (`EvaluationExecutionProof` + `TrustedKeyRegistry`) rejecting RSA/algorithm confusion and supporting `rotate_key()` and `is_revoked()`.
- **Authentication & RBAC:** `APIKeyAuthManager` hashes API keys with SHA-256 (`hmac.compare_digest` verification), supports key TTL & revocation, RBAC (`admin`, `developer`, `operator`, `viewer`), and cross-user session isolation; `SlidingWindowRateLimiter` protects REST and WebSocket endpoints.
- **Archive Safety:** `DatasetMetadata.safe_extract_archive()` verifies archive digests before reading and rejects path traversal, drive/absolute paths, symlinks, hardlinks, unsupported formats, and decompression bombs.
- **Privacy & Redaction:** Consent tokens (`ConsentManager`) are SHA-256 hashed; caller consent is required on every live operation; raw media buffers are scrubbed (`scrub_media_payload()`) in `finally` and consent-error handlers; `SensitiveDataRedactor` strips tokens/base64/payloads from JSON logs.
- **Robot Actuator Safety:** `eon_ers.safety.actuator_isolation` blocks forbidden motion/actuator keys (`cmd_vel`, `motor`, `wheel`, `torque`, etc.) recursively across all event payloads.
- **CI Security:** `.github/workflows/ers-ci.yml` and CodeQL enforce `ruff`, `mypy`, `pip-audit --desc`, Python 3.11–3.12 test matrices, and non-root CPU container builds.

## Vulnerability Reporting

Do not open public issues with exploit details or private signing keys. Contact OVIC Labs security maintainers privately (`security@oviclabs.com`).
