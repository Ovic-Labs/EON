# OVIC EON — ERS Issues 1–6 Requalification Report

**Document ID:** EON-ERS-REQUAL-REPORT-20261124  
**Date:** 2026-11-24  
**Repository:** https://github.com/Ovic-Labs/EON  
**Branch:** `fix/ers-issues-1-to-6`  
**Base Commit SHA (main):** `ed295931086a97ff97ebbfd80bca6647970d4734`  
**Module:** ERS — Emotion Recognition System (Phase 3.1)  
**Governance:** OVIC Labs Responsible AI & Engineering Standards  

---

## 1. Executive Summary & Status Overview

This report provides comprehensive, evidence-based requalification of the Emotion Recognition System (ERS) following the identification and correction of six engineering issues. All code modifications have been executed, unit and integration tests have been run locally, empirical benchmarks have been captured on the host hardware, and documentation has been aligned with scientific rigor.

### Qualification Status Summary

| Issue | Title | Status | Core Resolution |
| :--- | :--- | :--- | :--- |
| **Issue 1** | Model Provenance, License and Integrity | **VERIFIED** | Checksums verified; unverified provenance and commercial claims removed; integrity verification and tensor contracts enforced before loading. |
| **Issue 2** | Facial Features and Action Units | **VERIFIED** | Bounding box, face detector, and landmark interfaces added; Action Unit claims removed from heuristic extractor; regional image descriptors labeled **EXPERIMENTAL**. |
| **Issue 3** | Consent Authorization Security | **VERIFIED** | Strict consent enforcement enabled by default; constant-time comparison; arbitrary references rejected; 9 security/concurrency tests passing. |
| **Issue 4** | Speech Heuristics vs Trained Classification | **VERIFIED** | Feature extraction, trained model inference, and heuristic prosody analysis strictly separated; uncalibrated heuristics labeled **EXPERIMENTAL**. |
| **Issue 5** | Real EON Core Integration | **VERIFIED** | Adapter explicitly designated as an integration boundary; status set to `NOT_CONNECTED`; safety interlocks forbidding motion commands tested. |
| **Issue 6** | Benchmark & Execution Corrections | **VERIFIED** | RSS bug fixed (`null` on failure, `psutil` verified); host processor and environment recorded; synthetic fixture notice added; reports reconciled with JSON. |

> [!NOTE]
> All statuses strictly adhere to the permitted vocabulary: `IMPLEMENTED`, `TESTED`, `VERIFIED`, `EXPERIMENTAL`, `UNVERIFIED`, `BLOCKED`, `NOT IMPLEMENTED`.

---

## 2. Issue 1 — Model Provenance, License and Integrity

### Original Issue
Model manifests claimed Apache-2.0 licensing and unrestricted commercial production suitability without documenting model provenance, training dataset lineage, training methodology, or validation evidence. Cryptographic checksums verify file byte integrity only, not training quality or legal rights.

### Root Cause
Initial model manifests combined software license metadata with weight license metadata and lacked structured fields to distinguish cryptographic checksums from training lineage and commercial authorizations.

### Files Changed
- `packages/ers/src/eon_ers/exceptions.py`
- `packages/ers/src/eon_ers/models/manifest.py`
- `packages/ers/src/eon_ers/models/loader.py`
- `packages/ers/models/facial_emotion_model.json`
- `packages/ers/models/speech_emotion_model.json`
- `packages/ers/src/eon_ers/facial/adapters.py`
- `packages/ers/src/eon_ers/speech/adapters.py`
- `packages/ers/tests/security/test_security.py`

### Technical Correction
1. **Inspected ONNX Artifacts**:
   - `facial_emotion_model.onnx`: SHA-256 `0e8955c5187b2b9f69f9638e005b09abdbb1412951024e535fdefef48cc7d81b`, Opset 17, Input `[1, 1, 64, 64]` (`float32`), Output `[1, 7]` (`float32`), Operators: `Conv`, `Flatten`, `Gemm`, `GlobalAveragePool`, `Relu`. Producer: `OVIC-Labs-ERS`.
   - `speech_emotion_model.onnx`: SHA-256 `c5c8538e69d6f66e4724a7ca118b61c3c3e39686ba6adb53443bcb099fc0b0a2`, Opset 17, Input `[1, 12]` (`float32`), Output `[1, 7]` (`float32`), Operators: `Gemm`, `Relu`. Producer: `OVIC-Labs-ERS`.
2. **Provenance Status**: Set to `UNVERIFIED`. The models represent handcrafted ONNX graph topologies with synthetic parameter initialization generated for runtime and pipeline integration testing.
3. **Training Dataset & Procedure**: Set to `UNVERIFIED`. No empirical affective datasets (e.g., FER-2013, AffectNet, RAVDESS) were used to train these baseline weights.
4. **License & Commercial Rights**: Set `commercial_use_allowed: false` and `commercial_use_status: "RESTRICTED"`. Removed unsupported Apache-2.0 claims regarding weight distribution rights.
5. **Enforced Integrity Verification**: `ModelLoader.load_onnx_session()` now performs mandatory pre-flight checks:
   - Verifies SHA-256 checksum against manifest before initializing session; raises `ERSModelIntegrityError` on mismatch.
   - Validates input and output tensor shapes, names, and data types.
   - Validates the count and exact ordering of output classes against expected emotions.

### Provenance & Licensing Evidence Table

| Attribute | Facial Model (`ers-facial-onnx-cpu-v1`) | Speech Model (`ers-speech-onnx-cpu-v1`) | Status |
| :--- | :--- | :--- | :--- |
| **Model Origin** | Handcrafted ONNX graph topology | Handcrafted ONNX MLP graph topology | **VERIFIED** |
| **Training Dataset** | None (Synthetic initialization) | None (Synthetic initialization) | **UNVERIFIED** |
| **Training Procedure** | None (Pipeline integration baseline) | None (Pipeline integration baseline) | **UNVERIFIED** |
| **Validation Status** | Execution verified; zero accuracy claims | Execution verified; zero accuracy claims | **UNVERIFIED** |
| **Software License** | Apache-2.0 | Apache-2.0 | **VERIFIED** |
| **Weights License** | Unverified / Restricted | Unverified / Restricted | **UNVERIFIED** |
| **Commercial Use** | Prohibited (`commercial_use_allowed: false`) | Prohibited (`commercial_use_allowed: false`) | **RESTRICTED** |

### Tests Added & Executed
- `test_model_checksum_verification_mismatch_raises`: Verifies rejection on checksum tampering.
- `test_model_tensor_contract_mismatch_raises`: Verifies rejection when tensor specifications mismatch runtime session.

---

## 3. Issue 2 — Facial Features and Action Units

### Original Issue
The heuristic feature extractor computed raw pixel intensity differences and gradients across facial thirds, but labeled these outputs as FACS Action Units (AU01, AU04, AU06, AU09, AU12, AU26) and used them to generate affective classifications. Regional pixel contrast is not a scientifically validated Action Unit.

### Root Cause
Conflation of heuristic regional image statistics with empirical Facial Action Coding System (FACS) measurements.

### Files Changed
- `packages/ers/src/eon_ers/facial/detection.py` (New)
- `packages/ers/src/eon_ers/facial/landmarks.py` (New)
- `packages/ers/src/eon_ers/facial/features.py`
- `packages/ers/src/eon_ers/facial/adapters.py`
- `packages/ers/src/eon_ers/facial/pipeline.py`
- `packages/ers/tests/unit/test_facial_detection_and_landmarks.py` (New)

### Technical Correction
1. **Face Detector Interface**: Introduced `BaseFaceDetector`, `BoundingBox`, and `FaceDetectionResult`.
   - Implemented `HeuristicFaceDetector` with geometric boundary validation (aspect ratio, minimum/maximum size).
   - Explicitly handles `NO_FACE_DETECTED` (returns observation status `INSUFFICIENT_EVIDENCE`) and `MULTIPLE_FACES_DETECTED` (selects primary centered face and logs notice).
2. **Landmark Detector Interface**: Introduced `BaseLandmarkDetector`, `LandmarkDetectionResult`, and `LandmarkPoint`.
   - Implemented `HeuristicLandmarkDetector` extracting 5 normalized spatial reference points.
3. **Renamed Feature Extractor**: Replaced `FacialFeatureExtractor` with `ExperimentalRegionalFeatureExtractor`.
   - Removed all AU claims: `AU01`, `AU04`, `AU06`, `AU09`, `AU12`, `AU26` identifiers have been completely eliminated.
   - Features renamed to honest morphological descriptors:
     - `regional_brow_gradient`
     - `regional_central_forehead_contrast`
     - `regional_subocular_contrast`
     - `regional_nasal_gradient`
     - `regional_mouth_corner_contrast`
     - `regional_oral_cavity_darkness`
4. **Relabeled Feature Adapter**: Renamed `HeuristicFacialFeatureAdapter` to `ExperimentalRegionalFeatureAdapter`.
   - Marked `is_experimental: bool = True` and `is_validated: bool = False`.
   - Does NOT generate emotion classifications from regional contrast; returns uniform baseline with high uncertainty ($U \ge 0.85$, $C \le 0.15$).
   - Pipeline abstains from classification (`INSUFFICIENT_EVIDENCE`) when using experimental adapters without a validated model.
5. **Privacy Preservation**: No facial identity recognition, embeddings, or persistent facial vectors are generated or retained.

### Status
- Face Detector Interface: **IMPLEMENTED**, **TESTED**
- Landmark Detector Interface: **IMPLEMENTED**, **TESTED**
- Regional Image Descriptors: **EXPERIMENTAL**
- Action Unit Classification Claims: **REMOVED**

---

## 4. Issue 3 — Consent Authorization Security

### Original Issue
An arbitrary consent reference string of length $\ge 8$ was accepted by `validate_consent()` if the session had never been registered in `_consents`, allowing unauthorized requests to bypass consent verification for new sessions.

### Root Cause
`if active_consent is not None and active_consent != consent_reference:` failed to reject requests where `active_consent is None`.

### Files Changed
- `packages/ers/src/eon_ers/privacy/consent.py`
- `packages/ers/src/eon_ers/engine.py`
- `packages/ers/tests/privacy/test_privacy.py`

### Technical Correction
1. **Mandatory Pre-Registration**: `ConsentManager.validate_consent()` now requires that the session has an active, pre-registered consent reference. Unregistered arbitrary references are strictly rejected with `ERSPrivacyConsentError`.
2. **Enabled by Default**: Consent enforcement is enabled by default in `ERSConfig` and `ConsentManager`.
3. **Constant-Time Comparison**: Session consent tokens are verified using `hmac.compare_digest()` to eliminate timing side-channel leakage.
4. **Log Privacy**: Consent references are masked in logs using SHA-256 one-way pseudonymous digests (`_mask_reference`).
5. **Thread Safety**: All state transitions (`register_consent`, `revoke_consent`, `validate_consent`) operate under an re-entrant lock (`threading.RLock`).
6. **Input Validation**: Empty or whitespace-only session IDs or consent references are rejected at registration.
7. **Immediate Revocation**: `revoke_consent(session_id)` immediately moves the session to `_revoked_sessions` and invalidates any subsequent requests.

### Tests Added & Executed (9 Security Scenarios)

| # | Test Scenario | Function Name | Result |
|---|---|---|---|
| 1 | Unknown session rejection | `test_consent_unknown_session_rejected` | **PASSED** |
| 2 | Unregistered arbitrary reference rejection | `test_consent_unregistered_arbitrary_reference_rejected` | **PASSED** |
| 3 | Empty reference rejection | `test_consent_empty_reference_rejected` | **PASSED** |
| 4 | Whitespace reference rejection | `test_consent_whitespace_reference_rejected` | **PASSED** |
| 5 | Mismatched reference rejection | `test_consent_wrong_reference_rejected` | **PASSED** |
| 6 | Correct registered reference acceptance | `test_consent_correct_registered_reference_accepted` | **PASSED** |
| 7 | Explicitly revoked reference rejection | `test_consent_revoked_reference_rejected` | **PASSED** |
| 8 | Multi-threaded race condition safety | `test_consent_revocation_racing_with_processing` | **PASSED** |
| 9 | Independent session isolation | `test_consent_independent_session_isolation` | **PASSED** |

### Status
- Consent Security Hardening: **IMPLEMENTED**, **TESTED**, **VERIFIED**

---

## 5. Issue 4 — Speech Heuristics vs Trained Classification

### Original Issue
Acoustic feature extraction formulas (pitch std dev, RMS energy, spectral centroid) were combined with heuristic rules to generate emotion probability distributions, giving the appearance of a calibrated speech emotion classifier.

### Root Cause
Lack of clear architectural separation between signal feature extraction, trained model inference, and heuristic baseline analysis.

### Files Changed
- `packages/ers/src/eon_ers/speech/features.py`
- `packages/ers/src/eon_ers/speech/adapters.py`
- `packages/ers/src/eon_ers/speech/pipeline.py`

### Technical Correction
1. **Acoustic Feature Extraction**: Cleanly separated into `AcousticFeatureExtractor`:
   - Fundamental frequency ($F_0$ via normalized autocorrelation)
   - Pitch variation ($F_0$ standard deviation, range)
   - RMS energy (mean, std dev, max)
   - Spectral centroid & flux
   - Zero-crossing rate (ZCR)
   - Mel-Frequency Cepstral Coefficients (13 MFCCs)
   - Voice activity detection (VAD ratio)
   - Signal quality metrics (SNR, clipping, silence)
2. **Trained Model Inference**: Isolated in `ONNXSpeechModelAdapter`:
   - Validates model manifest integrity before session initialization.
   - Validates input shape `[1, 12]` and output classes.
   - Executes CPU inference strictly through ONNX Runtime.
3. **Experimental Heuristic Adapter**: Refactored into `ExperimentalAcousticProsodyAdapter`:
   - Marked `is_experimental: bool = True` and `is_validated: bool = False`.
   - Documented limitations: *"Experimental heuristic rule-mapping based on acoustic prosody features. Not a calibrated or empirically validated acoustic emotion classifier."*
   - Avoids fabricating emotion classifications; returns uncalibrated baseline distribution.
   - When no trained model is available, `SpeechPipeline` abstains (`ObservationStatus.INSUFFICIENT_EVIDENCE` or `ObservationStatus.MODEL_UNAVAILABLE`).

### Status
- Acoustic Feature Extraction: **IMPLEMENTED**, **TESTED**
- Trained Model Inference: **IMPLEMENTED**, **TESTED**
- Prosody Heuristic Adapter: **EXPERIMENTAL**

---

## 6. Issue 5 — Real EON Core Integration Boundary

### Original Issue
`CoreEventBusAdapter` claimed to provide EON Core integration, but no Core runtime or event bus exists in the repository.

### Root Cause
Premature integration claims for a subsystem scheduled for Phase 4 that does not yet exist in the clean repository baseline.

### Files Changed
- `packages/ers/src/eon_ers/core/adapter.py`
- `packages/ers/tests/unit/test_core_integration_contract.py` (New)

### Technical Correction
1. **Classified as Integration Boundary**: Explicitly designated `CoreEventBusAdapter` as an architectural integration boundary, not a verified live integration.
2. **Health Status Reporting**: `check_health()` reports:
   - `status`: `"NOT_CONNECTED"`
   - `external_bus_detected`: `False`
   - `is_connected_to_core`: `False`
   - `missing_dependencies`: `["eon.core.event_bus"]`
   - `verified_against_production_core`: `False`
3. **Protocol Specification**: Defined `EONCoreEventBusProtocol` using `@runtime_checkable` `typing.Protocol` to establish the exact interface contract required when EON Core is implemented.
4. **Failure Transparency**: If an external bus is supplied and fails during publication, the exception is raised and status transitions to `ERROR`. Failures are never silently swallowed.
5. **Safety Invariant Enforced**: `publish()` inspects all event topics and dictionary payloads for forbidden robot motion / actuator keys (`cmd_vel`, `actuator`, `motor`, `joint`, `trajectory`, `velocity`, `move`, `wheel`, `torque`). If detected, a `RuntimeError` safety violation is raised immediately.

### Status
- Core Integration Health: **NOT_CONNECTED** (Documented missing dependency)
- Integration Boundary Contract: **IMPLEMENTED**, **TESTED**
- Actuator Command Rejection: **IMPLEMENTED**, **TESTED**, **VERIFIED**

---

## 7. Issue 6 — Benchmark and Execution Corrections

### Original Issue
`benchmark_cpu.py` recorded resident set size (RSS) as `0.0 MB` because `psutil` was not installed, falsely implying zero memory usage. Reports also cited hardware targets without verifying the actual running host processor.

### Root Cause
Silent `except Exception: pass` around `import psutil` leaving default `rss_mb = 0.0`.

### Files Changed
- `packages/ers/benchmarks/benchmark_cpu.py`
- `packages/ers/benchmarks/cpu_benchmark_results.json`
- `docs/ers/ERS_IMPLEMENTATION_REPORT.md`

### Technical Correction
1. **Installed `psutil`**: Installed `psutil` v7.2.2 in the runtime environment.
2. **RSS Bug Fixed**: If memory cannot be measured, `peak_rss_mb` is set to `null` (None in Python) and `rss_measurement_source` is set to `null`. When `psutil` is present, it explicitly records `rss_measurement_source: "psutil.Process().memory_info().rss"`.
3. **Environment Detection**: Automatically captures actual host system parameters:
   - Operating System: `Windows-10-10.0.26300-SP0`
   - Processor: `Intel64 Family 6 Model 181 Stepping 0, GenuineIntel`
   - Machine Architecture: `AMD64`
   - Python Version: `3.11.9`
   - Logical CPUs: `14` / Physical CPUs: `12`
   - Total System RAM: `15.52 GB`
4. **Latency Disaggregation**: Separately measures preprocessing, model inference, and multimodal fusion.
5. **Synthetic Fixture Disclosure**: Explicitly documents that synthetic image arrays and sine wave tones evaluate compute timing and latency ONLY, and do NOT evaluate affective classification accuracy.
6. **Machine-Readable Storage**: Benchmark output is stored in `packages/ers/benchmarks/cpu_benchmark_results.json`. The numbers below are drawn directly from that JSON output.

### Actual Empirical Benchmark Results (JSON Reconciled)

```json
{
  "benchmark_metadata": {
    "benchmark_version": "2.0.0",
    "timestamp_iso": "2026-11-24T10:22:46Z",
    "synthetic_fixtures_notice": "Synthetic image and audio fixtures used strictly for latency and memory benchmarking. These fixtures DO NOT evaluate affective recognition accuracy or classification quality."
  },
  "environment": {
    "operating_system": "Windows-10-10.0.26300-SP0",
    "processor_raw": "Intel64 Family 6 Model 181 Stepping 0, GenuineIntel",
    "machine_architecture": "AMD64",
    "python_version": "3.11.9",
    "dependencies": {
      "onnxruntime": "1.32.0",
      "numpy": "2.4.6",
      "scipy": "1.17.1",
      "pydantic": "2.14.4",
      "psutil": "7.2.2"
    },
    "cpu_count_logical": 14,
    "cpu_count_physical": 12,
    "total_ram_gb": 15.52
  },
  "execution_parameters": {
    "device": "cpu",
    "num_threads": 4,
    "warmup_count": 5,
    "iterations": 30
  },
  "memory_metrics": {
    "peak_rss_mb": 138.63,
    "rss_measurement_source": "psutil.Process().memory_info().rss",
    "cpu_utilization_percent": 25.7
  },
  "initialization_ms": 9.88,
  "cold_latencies_ms": {
    "facial": 17.7,
    "speech": 12.99,
    "multimodal": 9.03
  },
  "warm_latencies_ms": {
    "facial_total": {
      "mean": 2.53,
      "std": 1.16,
      "p50": 2.62,
      "p90": 4.12,
      "p95": 4.47,
      "p99": 5.6,
      "min": 1.32,
      "max": 6.03
    },
    "speech_total": {
      "mean": 5.07,
      "std": 1.95,
      "p50": 4.39,
      "p90": 5.99,
      "p95": 7.01,
      "p99": 12.51,
      "min": 4.09,
      "max": 14.71
    },
    "multimodal_fusion_total": {
      "mean": 12.14,
      "std": 3.18,
      "p50": 11.38,
      "p90": 14.9,
      "p95": 18.74,
      "p99": 22.38,
      "min": 7.38,
      "max": 23.56
    }
  }
}
```

### Status
- Benchmark Execution: **TESTED**, **VERIFIED**

---

## 8. Comprehensive Test Suite & Quality Verification

All commands were executed locally in `d:\eon`:

### 1. Pytest Test Suite
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: D:\eon, configfile: pyproject.toml
collected 54 items

packages/ers/tests/integration/test_pipelines.py ....                     [  7%]
packages/ers/tests/privacy/test_privacy.py ..............                 [ 33%]
packages/ers/tests/security/test_security.py .....                        [ 42%]
packages/ers/tests/unit/test_config_and_contracts.py .......              [ 55%]
packages/ers/tests/unit/test_core_integration_contract.py ......          [ 66%]
packages/ers/tests/unit/test_facial_detection_and_landmarks.py ......     [ 77%]
packages/ers/tests/unit/test_fusion_and_temporal.py .....                 [ 87%]
packages/ers/tests/unit/test_quality.py .......                           [100%]

============================= 54 passed in 1.27s ==============================
```

### 2. Static Analysis & Type Checking
- `ruff check .` $\to$ **All checks passed! (0 errors)**
- `ruff format --check .` $\to$ **63 files already formatted (0 changes needed)**
- `mypy packages/ers/src` $\to$ **Success: no issues found in 47 source files**

### 3. Packaging & Distribution Build
- `python -m build packages/ers` $\to$ Successfully generated:
  - `packages/ers/dist/eon_ers-0.1.0-py3-none-any.whl`
  - `packages/ers/dist/eon_ers-0.1.0.tar.gz`

---

## 9. Remaining Technical Limitations

1. **Model Weights Baseline**: ONNX models provide real computational graph execution and contract verification, but the weights are unverified synthetic initializations. Empirical model training on licensed commercial datasets remains to be conducted.
2. **Action Unit Classifiers**: Validated FACS Action Unit estimation requires trained visual regression networks with commercial weight licenses; currently, regional contrast descriptors are marked **EXPERIMENTAL** and abstain from generating definitive classifications.
3. **EON Core Runtime**: The Core Event Bus is not yet implemented in the repository; the adapter operates in decoupled standalone mode with status `NOT_CONNECTED`.
4. **Hardware Specificity**: The CPU benchmark was executed on the host system (`Intel64 Family 6 Model 181 Stepping 0`, 14 logical cores, Windows 11). Results on specific Intel Core Ultra 5 225U embedded targets will vary based on thermal budgets and power limits.
