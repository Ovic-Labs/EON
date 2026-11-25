# ERS Developer and Installation Guide

## 1. Overview

The Emotion Recognition System (ERS) is OVIC EON's first intelligence engine. It runs CPU-first on edge hardware (such as Intel Core Ultra 5 225U / x86_64 CPUs) across Python 3.10, 3.11, and 3.12 without requiring discrete GPUs or cloud AI APIs.

### Key Architectural & Security Invariants

- **Responsible AI Epistemic Modesty**: All emotion outputs are probabilistic algorithmic estimates (`is_definitive_claim = False`), never certified medical diagnoses, psychiatric evaluations, or emotional ground-truth claims. Unvalidated models remain marked `MODEL_UNVALIDATED` and suppress discrete classifications.
- **Zero Raw Media Persistence**: Image and audio payloads are processed in volatile memory and immediately scrubbed on all paths (including errors and consent rejections); zero persistent disk writes by default.
- **Privacy By Design**: Strict consent registration and caller-supplied verification before processing (`ConsentManager` hashes tokens via SHA-256); no biometric facial identification or cross-session profiling.
- **Cryptographic & ONNX Integrity**: Physical archive SHA-256 verification, safe extraction limits, Ed25519 asymmetric execution proofs (`SigningKeyPair` / `TrustedKeyRegistry`), full ONNX weight validation, and numerical parity verification.
- **Safety Invariant**: ERS never emits physical robot actuator or motion commands (`cmd_vel`, `actuator`, `motor`, `torque`).

---

## 2. Environment Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12 (CPU-only compatible)
- Pip package installer
- Git

### Installation from Source

Clone the repository and install `packages/ers` with ML, live streaming, and development dependencies:

```bash
git clone https://github.com/Ovic-Labs/EON.git
cd EON
python -m pip install --upgrade pip
pip install -e "packages/ers[dev,ml,live]"
```

To install minimal core dependencies (runtime without live dashboard server or ML extras):

```bash
pip install -e packages/ers
```

---

## 3. Quickstart Example

```python
import asyncio
from eon_ers import ERSEngine, ERSConfig, ERSInput, Modality


async def run() -> None:
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )

    async with ERSEngine(config) as engine:
        engine.register_consent("session-user-1", "consent-ref-uuid4")

        with open("sample_face.jpg", "rb") as f:
            image_bytes = f.read()

        inp = ERSInput(
            session_id="session-user-1",
            modality=Modality.FACIAL,
            consent_reference="consent-ref-uuid4",
            image_payload=image_bytes,
        )

        observation = await engine.process_facial(inp)
        print("Status:", observation.status.value)
        print("Dominant Estimate:", observation.dominant_estimate)
        print("Confidence:", observation.confidence)
        print("Uncertainty:", observation.uncertainty)
        print("Is Definitive Claim:", observation.is_definitive_claim)


if __name__ == "__main__":
    asyncio.run(run())
```

---

## 4. Signing Keys & Reproducible Pipeline Execution

Scientific qualification proofs require an **Ed25519** private signing key and a `TrustedKeyRegistry` holding trusted public keys:

- **Provision via environment variables (recommended for CI/production):**
  ```bash
  export EON_ERS_SIGNING_KEY_ID="ovic-eval-ed25519-v1"
  export EON_ERS_SIGNING_PRIVATE_KEY_PATH="/run/secrets/ers_signing_key.pem"
  ```
- **Generate ephemeral development keys (testing only):**
  ```python
  from eon_ers.evaluation import SigningKeyPair, TrustedKeyRegistry

  key = SigningKeyPair.generate(key_id="dev-key-01")
  registry = TrustedKeyRegistry()
  registry.register_keypair(key)
  ```

Never store private keys inside source control, `.json` manifests, or Docker build layers.

---

## 5. Running Benchmarks

Execute the reproducible CPU benchmark on Intel Core Ultra 5 / edge hardware:

```bash
python packages/ers/benchmarks/benchmark_cpu.py
```

Results are saved to `packages/ers/benchmarks/cpu_benchmark_results.json`.

---

## 6. Testing, Security Audit & Packaging Gates

Run the complete test suite with coverage:

```bash
pytest packages/ers/tests -v --cov=eon_ers --cov-report=term-missing
```

Run code formatting, linting, static type checking, dependency vulnerability audit, and wheel build:

```bash
ruff check .
ruff format --check .
mypy packages/ers/src
pip-audit --desc
python -m build packages/ers --outdir dist/
```
