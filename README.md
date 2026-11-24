# OVIC EON — Emotional Intelligence Infrastructure for Robotics

[![ERS CI](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml/badge.svg)](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Architecture: Edge-First CPU](https://img.shields.io/badge/hardware-CPU--first%20Edge-green.svg)]()

**OVIC EON** is an open, modular emotional intelligence infrastructure engineered specifically for social robotics and human-robot interaction (HRI). It provides embodied agents with real-time affective perception, cognitive empathy modeling, and adaptive interaction policies.

---

## ERS — Emotion Recognition System (Phase 3.1)

The **Emotion Recognition System (ERS)** is EON's first operational intelligence engine. ERS transforms raw sensory inputs into mathematically sound, epistemic affective observations with full uncertainty bounds, running strictly local on edge CPUs.

### Key Architectural Tenets

1. **Epistemic Modesty:** ERS outputs represent *observable behavioral cues* rather than definitive claims about internal ground-truth emotional states (`is_definitive_claim = False` strictly enforced and validated).
2. **Zero Raw Media Retention:** All visual frames and audio waveforms are processed exclusively in volatile memory and immediately scrubbed upon feature extraction (`inp.scrub_media_payload()`).
3. **Edge-First CPU Efficiency:** Sub-15ms multimodal inference running on low-power Intel Core Ultra / edge CPUs without requiring discrete GPUs or cloud APIs.
4. **Safety & Subsystem Isolation:** Hard architectural interlocks prevent ERS from directly commanding robot actuators or motion systems (`cmd_vel`, `actuator`, `motor` commands are strictly blocked).
5. **Quality-Aware Reliability Fusion:** Bayesian multimodal fusion discounts modalities with poor signal quality, low contrast, clipping, or high uncertainty, detecting multimodal conflicts via Jensen-Shannon divergence.

---

## Repository Structure

```
.
├── .github/workflows/          # Automated GitHub Actions CI (lint, typecheck, test, build)
├── docs/ers/                   # ERS Engineering Documentation
│   ├── API_REFERENCE.md        # Comprehensive public API documentation
│   ├── DEVELOPER_GUIDE.md      # Architecture, pipeline stages, and developer guide
│   └── ERS_IMPLEMENTATION_REPORT.md # Verification metrics and phase qualification report
├── packages/
│   └── ers/                    # Emotion Recognition System package (`eon-ers`)
│       ├── benchmarks/         # CPU performance benchmark scripts and results
│       ├── examples/           # Executable quickstart and multimodal fusion examples
│       ├── models/             # Validated ONNX model graphs and cryptographic manifests
│       ├── src/eon_ers/        # Production engine source code
│       │   ├── api/            # Public input/output schemas
│       │   ├── core/           # Event bus adapter and safety interlocks
│       │   ├── facial/         # Facial quality, AU extraction, ONNX adapter, pipeline
│       │   ├── fusion/         # Alignment, weighting, uncertainty, Bayesian fusion
│       │   ├── metrics/        # Evaluation framework and performance tracking
│       │   ├── models/         # Model registry, loader, and cryptographic verification
│       │   ├── privacy/        # Consent manager, retention guard, PII redactor
│       │   ├── quality/        # Face resolution/blur, audio SNR/clipping validators
│       │   ├── speech/         # Acoustic framing, pitch/energy/MFCC, ONNX adapter
│       │   └── temporal/       # EMA smoothing and session-bounded state tracking
│       └── tests/              # Pytest test suite (unit, integration, privacy, security)
├── LICENSE                     # Apache 2.0 license
├── pyproject.toml              # Root workspace tool configurations (ruff, mypy, pytest)
└── README.md                   # Repository overview and getting started guide
```

---

## Quickstart

### 1. Installation

Install ERS in editable mode with development and ML dependencies:

```bash
# Clone the repository
git clone https://github.com/Ovic-Labs/EON.git
cd EON

# Install package with optional dependencies
pip install -e "packages/ers[dev,ml]"
```

### 2. Basic Usage

```python
import numpy as np
from eon_ers.contracts import ERSInput, ModalityType
from eon_ers.engine import EmotionRecognitionEngine

# Initialize the engine (local CPU execution)
engine = EmotionRecognitionEngine()

# Process an image input (64x64 RGB synthetic image)
dummy_image = np.ones((64, 64, 3), dtype=np.uint8) * 128
input_data = ERSInput.from_image(
    image_bytes=dummy_image.tobytes(),
    session_id="session-001",
    has_consent=True,
    user_id="user-demo",
)

result = engine.process_sync(input_data)

print(f"Primary Category: {result.primary_category}")
print(f"Confidence:       {result.confidence:.3f}")
print(f"Uncertainty:      {result.uncertainty:.3f}")
print(f"Definitive Claim: {result.is_definitive_claim}")  # Always False
```

### 3. Running Examples

Two complete, standalone examples are included in `packages/ers/examples/`:

```bash
# Run basic quickstart demonstration
python packages/ers/examples/quickstart.py

# Run multimodal fusion demonstration (audio + video)
python packages/ers/examples/multimodal_fusion.py
```

---

## Verification & Quality Assurance

Run the complete verification suite locally:

```bash
# Run full unit and integration test suite
pytest packages/ers/tests -v --cov=eon_ers

# Check code formatting and linting
ruff check .
ruff format --check .

# Run static type checking
mypy packages/ers/src

# Run CPU benchmark
python packages/ers/benchmarks/benchmark_cpu.py
```

### Test Suite Summary

- **Total Tests:** 31 passed (100% pass rate)
- **Unit Tests:** Input contracts, quality validators, fusion weighting, temporal trackers
- **Integration Tests:** End-to-end facial, speech, and multimodal async pipelines
- **Privacy Tests:** Active consent revocation, zero raw media retention in output, PII redactor
- **Security Tests:** Actuator command interlocks, oversized payload rejection, model manifest tampering detection

### Intel Core Ultra 5 225U CPU Benchmark (p50 Latency)

| Pipeline Component | Cold Start | Warm Inference (p50) | Target | Margin |
|---|---|---|---|---|
| Facial Pipeline | 9.08 ms | **2.64 ms** | < 25.0 ms | **89.4% under budget** |
| Speech Pipeline | 5.48 ms | **5.50 ms** | < 25.0 ms | **78.0% under budget** |
| Multimodal Fusion | 10.60 ms | **11.02 ms** | < 30.0 ms | **63.3% under budget** |

---

## Documentation

- [Developer Guide](docs/ers/DEVELOPER_GUIDE.md): Architecture overview, lifecycle states, pipeline diagrams, and extension guidelines.
- [API Reference](docs/ers/API_REFERENCE.md): Detailed schemas, classes, methods, and error codes.
- [Implementation Report](docs/ers/ERS_IMPLEMENTATION_REPORT.md): Full Phase 3.1 qualification report, hardware benchmarks, and verification evidence.

---

## Contributing & License

OVIC EON is licensed under the [Apache License 2.0](LICENSE).  
Copyright &copy; 2026 OVIC Labs. All rights reserved.
