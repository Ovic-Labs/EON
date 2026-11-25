# OVIC EON — Emotional Intelligence Infrastructure for Robotics

[![ERS CI](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml/badge.svg)](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Architecture: Edge-First CPU](https://img.shields.io/badge/hardware-CPU--first%20Edge-green.svg)]()

**OVIC EON** is an open, modular emotional intelligence infrastructure engineered specifically for social robotics and human-robot interaction (HRI). It provides embodied agents with real-time affective perception pipelines, privacy-by-design consent controls, and hard robot safety interlocks running locally on edge CPUs.

> **Scientific Qualification & Production Status Notice:**  
> While ERS software pipelines, cryptographic proof verification, ONNX export/parity checks, and privacy/safety controls pass all automated engineering gates, **empirical human affective benchmark qualification (`AffectNet`, `RAF-DB`, `RAVDESS`, `CREMA-D`) is currently `BLOCKED`** because external licensed datasets are not bundled or acquired in this repository. Shipped baseline ONNX models remain explicitly marked **`MODEL_UNVALIDATED`**, discrete classification claims on unvalidated models are suppressed (`ObservationStatus.MODEL_UNVALIDATED`), and synthetic test accuracy must **never** be interpreted as real-world affective recognition accuracy.

---

## ERS — Emotion Recognition System (Phase 3.1.8)

The **Emotion Recognition System (ERS)** is EON's first operational intelligence engine. ERS transforms raw sensory inputs into structured, epistemic affective observations with explicit model qualification state and uncertainty bounds, running strictly local on edge CPUs (validated on Intel Core Ultra 5 225U / x86_64 CPUs across Python 3.11 and 3.12).

### Key Architectural & Security Tenets

1. **Epistemic Modesty:** ERS outputs represent *observable behavioural cues* rather than certified medical, psychiatric, or definitive claims about internal subjective states (`is_definitive_claim = False` strictly enforced and frozen on all `EmotionObservation` and `FusionResult` contracts).
2. **Fail-Closed Model & Dataset Integrity:**
   - Dataset archive verification (`verify_archive`, `safe_extract_archive`) requires physical archive bytes, constant-time SHA-256 verification, decompression-bomb limits, and path-traversal/symlink rejection.
   - Model loading (`ModelLoader.validate_and_load_onnx_weights`) verifies SHA-256 manifests, structural ONNX graphs, complete external initializers, tensor contracts/dtypes, modality/framework/version compatibility, and finite CPU smoke inference.
   - Scientific qualification proofs use domain-separated **Ed25519** asymmetric signatures (`SigningKeyPair`, `TrustedKeyRegistry`) with key rotation, revocation, and algorithm-confusion rejection.
3. **Zero Raw Media Retention & Consent Isolation:** Visual frames and audio waveforms are processed in volatile memory, stored consent tokens are SHA-256 hashed (`ConsentManager`, `LiveSessionManager`), caller-supplied consent is mandatory on every live call, and raw payloads are scrubbed immediately (`scrub_media_payload()`) even on consent rejection or processing failure.
4. **Edge-First CPU Efficiency:** Local CPU execution via NumPy, SciPy, Pillow, and ONNX Runtime `CPUExecutionProvider` with no discrete GPU or cloud API requirements.
5. **Robot Safety Interlocks:** Hard interlocks in `CoreEventBusAdapter` block robot motion or actuator keys (`cmd_vel`, `actuator`, `motor`, `torque`, `wheel`, `joint`, `trajectory`, `velocity`, `move`), preserving physical emergency-stop independence.

---

## Repository Structure

```text
.
├── .github/workflows/
│   └── ers-ci.yml                  # GitHub Actions CI (ruff, mypy, pip-audit, pytest matrix 3.11-3.12, build)
├── docs/ers/                       # ERS Engineering Documentation & Qualification Reports
│   ├── API_REFERENCE.md
│   ├── DEVELOPER_GUIDE.md
│   ├── ERS_DATASET_PROVENANCE_REGISTER.md
│   ├── ERS_REAL_WORLD_EVALUATION_PROTOCOL.md
│   ├── PHASE_3_1_7_FINAL_QUALIFICATION_REPORT.md
│   └── PHASE_3_1_8_FINAL_QUALIFICATION_REPORT.md
├── packages/
│   └── ers/                        # Emotion Recognition System package (`eon-ers`)
│       ├── benchmarks/             # CPU latency & memory benchmarks
│       ├── examples/               # Executable quickstart, fusion, and live demo scripts
│       ├── models/                 # Baseline ONNX graphs, cryptographic manifests, validation records
│       ├── src/eon_ers/            # Production engine source code
│       │   ├── api/                # REST & WebSocket Pydantic schemas
│       │   ├── core/               # Core event bus boundary and actuator safety interlocks
│       │   ├── evaluation/         # Dataset integrity, zero-leakage splits, Ed25519 proofs, metrics, evaluator
│       │   ├── facial/             # Facial quality, landmarks, features, ONNX adapter, pipeline
│       │   ├── fusion/             # Alignment, weighting, divergence, validation-isolated Bayesian fusion
│       │   ├── live/               # LiveSessionManager, FastAPI/WS server, telemetry dashboard UI
│       │   ├── metrics/            # Evaluation framework and latency/memory tracker
│       │   ├── models/             # ModelLoader, ModelManifest, ModelRegistry, ModelValidationRecord
│       │   ├── privacy/            # Hashed ConsentManager, MediaRetentionGuard, SensitiveDataRedactor
│       │   ├── quality/            # Visual contrast/blur/resolution & audio SNR/clipping evaluators
│       │   ├── speech/             # Acoustic framing, prosody features, ONNX adapter, pipeline
│       │   ├── temporal/           # EMA smoothing & session-isolated ring buffers
│       │   └── training/           # Preprocessing, zero-leakage features, CPU MLP trainer, calibration, ONNX parity export, 15-stage pipeline
│       └── tests/                  # Pytest suite (unit, integration, live, privacy, security)
├── LICENSE                         # Apache 2.0 license
├── SECURITY.md                     # Security policy, threat model & Ed25519 key management
├── pyproject.toml                  # Root workspace configuration (ruff, mypy, pytest)
└── README.md                       # Project overview and getting started guide
```

---

## Quickstart

### 1. Installation (CPU-Only, Python 3.11–3.12)

```bash
# Clone the repository
git clone https://github.com/Ovic-Labs/EON.git
cd EON

# Upgrade pip and install ERS with ML, live server, and dev dependencies
python -m pip install --upgrade pip
pip install -e "packages/ers[dev,ml,live]"
```

### 2. Basic Usage

```python
import asyncio
import io
import numpy as np
from PIL import Image
from eon_ers import ERSConfig, ERSEngine, ERSInput, Modality


def sample_jpeg() -> bytes:
    arr = np.full((96, 96, 3), 160, dtype=np.uint8)
    arr[25:40, 25:40] = 40
    arr[25:40, 56:71] = 40
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    return buf.getvalue()


async def main() -> None:
    config = ERSConfig(
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    async with ERSEngine(config) as engine:
        engine.register_consent("session-001", "consent-token-demo")
        inp = ERSInput(
            session_id="session-001",
            modality=Modality.FACIAL,
            consent_reference="consent-token-demo",
            image_payload=sample_jpeg(),
        )
        obs = await engine.process_facial(inp)
        print("Status:            ", obs.status.value)
        print("Model State:       ", obs.model_state.value)
        print("Dominant Estimate: ", obs.dominant_estimate)
        print("Definitive Claim:  ", obs.is_definitive_claim)  # Strictly False


asyncio.run(main())
```

### 3. Running Examples & Live Demonstration

```bash
# 1. Run executable quickstart
python packages/ers/examples/quickstart.py

# 2. Run multimodal fusion example
python packages/ers/examples/multimodal_fusion.py

# 3. Launch local live webcam & microphone dashboard (requires [live] extras)
python packages/ers/examples/live_demo.py --open-browser

# 4. Run CPU latency & memory benchmark
python packages/ers/benchmarks/benchmark_cpu.py
```

See [ERS_LIVE_DEMO_GUIDE.md](docs/ers/ERS_LIVE_DEMO_GUIDE.md) and [ERS_LIVE_INPUT_ARCHITECTURE.md](docs/ers/ERS_LIVE_INPUT_ARCHITECTURE.md) for live input details.

---

## Verification, Testing & Security Gates

Run the complete verification, static analysis, security audit, and build suite locally:

```bash
# Full test suite with line coverage
pytest packages/ers/tests -v --cov=eon_ers --cov-report=term-missing

# Code formatting & linting
ruff check .
ruff format --check .

# Static type checking (strict checks on eon_ers)
mypy packages/ers/src

# Dependency vulnerability audit
pip-audit --desc

# Source and wheel package build
python -m build packages/ers --outdir dist/
```

### Current Verification Baseline (Phase 3.1.8)

- **Automated Test Suite (`pytest packages/ers/tests -v --cov=eon_ers`):** **141 passed**, 0 failed, **85% code coverage** across 4,821 statements.
  - **Unit & Integrity Suites:** Dataset archive/manifest verification & safe extraction, Ed25519 execution proof key rotation/tampering, ONNX weight loading & parity verification, evaluator/metrics analytical verification, status precedence, quality gating, fusion isolation.
  - **Integration, Privacy, Live & Security Suites:** End-to-end CPU ONNX pipelines, FastAPI REST & WebSocket lifecycle, hashed consent registration/revocation/caller-auth enforcement, zero disk retention, PII redaction, robot actuator command prohibition.
- **Linters & Typecheck:** `ruff check .` clean, `ruff format --check .` clean (125 files formatted), `mypy packages/ers/src` clean (0 issues across 65 source files).
- **Dependency Audit (`pip-audit --desc`):** No known vulnerabilities found.
- **Distribution Build:** `eon_ers-0.1.0-py3-none-any.whl` and `eon_ers-0.1.0.tar.gz` verified.

### CPU Latency Reference

Recorded in [cpu_benchmark_results.json](packages/ers/benchmarks/cpu_benchmark_results.json) (synthetic latency/memory fixtures only; not accuracy qualification; 30 measured iterations, 4 threads, Intel64 Family 6 Model 181 Stepping 0, Peak RSS 138.63 MB):

| Pipeline Component | Cold Start | Warm p50 Latency | Target Budget |
|---|---:|---:|---:|
| Facial Pipeline | 17.70 ms | 2.62 ms | < 25.0 ms |
| Speech Pipeline | 12.99 ms | 4.39 ms | < 25.0 ms |
| Multimodal Fusion | 9.03 ms | 11.38 ms | < 30.0 ms |

---

## Documentation & Qualification Reports

- [Security Policy & Key Management](SECURITY.md): Threat model, Ed25519 provisioning/rotation, dataset extraction safety, and privacy/robot safety controls.
- [Phase 3.1.8 Final Qualification Report](docs/ers/PHASE_3_1_8_FINAL_QUALIFICATION_REPORT.md): Complete independent audit inventory, fixes, test evidence, and scientific status.
- [Phase 3.1.7 Final Qualification Report](docs/ers/PHASE_3_1_7_FINAL_QUALIFICATION_REPORT.md): Phase 3.1.7 integrity and security hardening report.
- [Developer Guide](docs/ers/DEVELOPER_GUIDE.md): CPU environment setup, key provisioning, and verification commands.
- [API Reference](docs/ers/API_REFERENCE.md): Engine, security, dataset, model loader, evaluation, and training APIs.
- [Real-World Evaluation Protocol](docs/ers/ERS_REAL_WORLD_EVALUATION_PROTOCOL.md) & [Dataset Provenance Register](docs/ers/ERS_DATASET_PROVENANCE_REGISTER.md): Benchmark licensing constraints (`AffectNet`, `RAF-DB`, `RAVDESS`, `CREMA-D`) and evaluation criteria.

---

## Contributing & License

OVIC EON is licensed under the [Apache License 2.0](LICENSE).  
Copyright &copy; 2026 OVIC Labs. All rights reserved.
