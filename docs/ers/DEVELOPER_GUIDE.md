# ERS Developer and Installation Guide

## 1. Overview

The Emotion Recognition System (ERS) is OVIC EON's first intelligence engine. It runs CPU-first on modern hardware (such as Intel Core Ultra 5 225U) without requiring dedicated discrete GPUs or cloud AI APIs.

### Key Architectural Invariants

- **Responsible AI Epistemic Modesty**: All emotion outputs are probabilistic algorithmic estimates (`is_definitive_claim = False`), never certified medical diagnoses, psychiatric evaluations, or emotional ground truth claims.
- **Zero Raw Media Persistence**: Image and audio payloads are processed in volatile memory and immediately scrubbed; zero persistent disk writes by default.
- **Privacy By Design**: Strict consent verification before processing; no biometric facial identification, no persistent face embeddings, no cross-session user tracking.
- **Safety Invariant**: ERS never emits physical robot actuator or motion commands (`cmd_vel`, `actuator`, `motor`).

---

## 2. Environment Setup

### Prerequisites

- Python 3.10, 3.11, or 3.12
- Pip package installer
- Git

### Installation from Source

Clone the repository and install `packages/ers`:

```bash
git clone https://github.com/Ovic-Labs/EON.git
cd EON
python -m pip install --upgrade pip
pip install -e packages/ers[dev,ml]
```

To install CPU-first with minimal dependencies:

```bash
pip install -e packages/ers
```

---

## 3. Quickstart Example

```python
import asyncio
from eon_ers import ERSEngine, ERSConfig, ERSInput, Modality


async def run():
    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )

    async with ERSEngine(config) as engine:
        with open("sample_face.jpg", "rb") as f:
            image_bytes = f.read()

        inp = ERSInput(
            session_id="session-user-1",
            modality=Modality.FACIAL,
            consent_reference="consent-ref-uuid4",
            image_payload=image_bytes,
        )

        observation = await engine.process_facial(inp)
        print("Dominant Estimate:", observation.dominant_estimate)
        print("Confidence:", observation.confidence)
        print("Uncertainty:", observation.uncertainty)
        print("Is Definitive Claim:", observation.is_definitive_claim)


if __name__ == "__main__":
    asyncio.run(run())
```

---

## 4. Running Benchmarks

Execute the reproducible CPU benchmark on Intel Core Ultra 5 / edge hardware:

```bash
python packages/ers/benchmarks/benchmark_cpu.py
```

Results are saved to `packages/ers/benchmarks/cpu_benchmark_results.json`.

---

## 5. Testing and Validation

Run the complete test suite:

```bash
pytest packages/ers/tests -v
```

Run code formatting and type checking:

```bash
ruff check .
ruff format --check .
mypy packages/ers/src
```
