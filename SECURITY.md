# OVIC EON Security Policy & Cryptographic Controls

## 1. Security Posture & Scope

OVIC EON is emotional-perception infrastructure designed for local, edge-first execution in human-robot interaction (HRI). Security, privacy, dataset/model supply-chain integrity, and robot actuation isolation are non-negotiable engineering invariants enforced in code and CI.

---

## 2. Cryptographic Execution Proof & Key Management

### 2.1 Algorithm & Canonicalization
- Scientific qualification proofs (`eon_ers.evaluation.proof.EvaluationExecutionProof`) use asymmetric **Ed25519** digital signatures (`cryptography>=42.0.0`).
- Signatures cover a domain-separated (`EON-ERS-EXECUTION-PROOF-V2\x00`), canonicalized UTF-8 JSON representation (`sort_keys=True`, compact separators) of every bound evaluation parameter: `proof_version`, `signature_algorithm`, `key_id`, `model_id`, `artifact_sha256`, `dataset_archive_sha256`, `dataset_name`, `dataset_provenance`, `subject_count`, `sample_count`, `evaluation_script_version`, `execution_timestamp`, and `inference_hardware`.
- During verification (`verify_detailed()`), schema version `2.0.0` and algorithm `Ed25519` are strictly verified in code even against unvalidated objects constructed outside normal validators, preventing algorithm confusion and signature stripping attacks.

### 2.2 Production Key Provisioning (Zero Hardcoded Secrets)
- Private signing keys (`SigningKeyPair`) **must never** be committed to version control, stored in model JSON manifests, or embedded in Python source files.
- Provision private keys in CI/CD or production signing hosts exclusively via secrets managers mapped to environment variables or restricted PEM key files:
  - `EON_ERS_SIGNING_KEY_ID`: Explicit key identifier (e.g., `ovic-prod-ers-2026-01`).
  - `EON_ERS_SIGNING_PRIVATE_KEY_PEM` or `EON_ERS_SIGNING_PRIVATE_KEY_PATH`: PKCS#8 PEM-encoded Ed25519 private key.
- `SigningKeyPair.__repr__()` redacts key material, and no logging handler prints private key bytes or raw signatures unnecessarily.

### 2.3 Key Rotation & Revocation
- Verifiers resolve `proof.key_id` against `TrustedKeyRegistry`:
  - **Unknown Keys:** Any `key_id` absent from `TrustedKeyRegistry` is rejected fail-closed.
  - **Key Rotation:** Use `TrustedKeyRegistry.rotate_key(old_key_id, new_key_id, new_public_key, revoke_old=True)` to transition trust cleanly.
  - **Key Revocation:** Compromised or decommissioned keys are recorded in `_revoked_keys` via `revoke_key(key_id)`; verification explicitly reports revoked status and prevents re-registration of revoked identifiers.

---

## 3. Dataset Integrity & Safe Archive Extraction

- `DatasetMetadata.is_valid_checksum()` performs syntactic validation only and is **never** accepted as proof of archive integrity.
- Pipeline `STAGE_3_INTEGRITY_CHECK` requires physical archive bytes (`archive_path`) and recomputes SHA-256 against trusted expected digests using constant-time `hmac.compare_digest()`.
- `DatasetMetadata.safe_extract_archive()` verifies the archive SHA-256 *before* reading entries and blocks:
  - Unsupported archive extensions (accepts `.zip`, `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`).
  - Path traversal (`..`), absolute paths, Windows drive prefixes, and root escapes.
  - Symlinks, hardlinks, FIFOs, and device nodes inside ZIP or TAR archives.
  - Archive/uncompressed size bombs and excessive compression ratios (`max_archive_bytes`, `max_extracted_bytes`, `max_files`, `max_compression_ratio`).

---

## 4. Model Weights & ONNX Numerical Parity

- File existence is never accepted as model loading (`ModelLoader.validate_and_load_onnx_weights()`).
- Imported and runtime ONNX artifacts must pass: non-zero size, non-placeholder manifest SHA-256 verification, protobuf structural checks (`onnx.checker`), complete external tensor verification (rejecting partially loaded external data), finite non-empty initializers (no NaN/Inf), framework/modality/major-version compatibility, tensor contract alignment, and finite CPU smoke inference.
- `ONNXModelExporter` rejects input/output shape mismatches (no silent zero-padding or truncation), checks CPU logit/probability parity against NumPy reference inference, and atomically replaces the target file only after all checks pass.

---

## 5. Privacy, Consent & Robot Safety Interlocks

- **Hashed Consent Verification:** `ConsentManager` stores SHA-256 digests of registered session consent tokens (`hmac.compare_digest` verification) rather than plaintext secrets. `LiveSessionManager` requires caller-supplied `consent_reference` on every live call and never substitutes cached tokens.
- **Immediate Media Scrubbing:** Raw image and audio buffers in `ERSInput` are scrubbed (`scrub_media_payload()`) in `finally` blocks across pipelines, engine entrypoints, and live managers, including on consent or decoding errors.
- **Robot Actuation Isolation:** `CoreEventBusAdapter.publish()` inspects payloads and raises `RuntimeError` on any forbidden motion/actuator key (`cmd_vel`, `motion`, `actuator`, `motor`, `joint`, `trajectory`, `velocity`, `move`, `wheel`, `torque`). Physical emergency stops remain hardware-isolated and completely independent of ERS.

---

## 6. Vulnerability Reporting & Auditing

- Run dependency vulnerability checks before releases:
  ```bash
  pip-audit --desc
  ```
- Report suspected security vulnerabilities privately to OVIC Labs Security Engineering (`security@oviclabs.com`) with reproduction steps and affected commit SHA. Do not disclose unpatched vulnerabilities publicly prior to remediation.
