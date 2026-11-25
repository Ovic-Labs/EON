# Privacy, Consent, and Data Retention Controls

## Backend Enforcement (`eon_ers.privacy`)
1. **Explicit Consent Gate:** Processing fails closed (`ERSPrivacyConsentError`) unless the caller provides the active `consent_reference` matching the SHA-256 digest stored by `ConsentManager`.
2. **Instant Revocation:** Calling `revoke_consent` or `DELETE /api/v1/consent/{session_id}` (or WS `revoke`) blocks further processing and transitions active live sessions to `REVOKED`.
3. **Zero Disk Retention Default:** Raw webcam frames, microphone audio, video payloads, and text strings reside solely in volatile Python objects/buffers (`zero_disk_retention=True`) and are cleared immediately on completion or exception via `ERSInput.scrub_media_payload()` and `try/finally` blocks.
4. **Limits of Memory Scrubbing:** In standard CPython runtimes without native OS hardware secure-wipe guarantees, `scrub_media_payload()` clears object references (`None`) so Python GC reclaims buffers, rather than claiming hardware-level physical DRAM zeroization.
5. **Log Redaction:** `StructuredJSONFormatter` and `SensitiveDataRedactor` strip base64 blobs, bearer/API keys, consent tokens, and raw media fields from logs and structured errors.
6. **Non-Biometric Design:** `HeuristicFaceDetector` and `SessionFaceTracker` use ephemeral spatial bounding boxes (`face-0`, `track-0`) and never generate facial recognition identity vectors.
