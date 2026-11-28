# OVIC EON — Emotional Intelligence Infrastructure for Robotics

[![ERS CI](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml/badge.svg)](https://github.com/Ovic-Labs/EON/actions/workflows/ers-ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Architecture: Edge-First CPU](https://img.shields.io/badge/hardware-CPU--first%20Edge-green.svg)]()

**OVIC EON** is an open, modular, CPU-first emotional intelligence infrastructure engineered for social robotics and human-robot interaction (HRI). Its first engine, **ERS (Emotion Recognition System)**, delivers real-time facial, vocal, textual, video, and multimodal affective observation pipelines with explicit model qualification tracking, strict privacy controls, and robot actuator safety interlocks.

> **Scientific Qualification & Production Status Notice:**  
> All ERS software pipelines, REST/WebSocket APIs, enterprise dashboard, RBAC auth, cryptographic proof verification, ONNX parity export, and non-root Docker deployment pass automated engineering verification. However, **empirical human affective benchmark qualification (`AffectNet`, `RAF-DB`, `FER2013`, `RAVDESS`, `CREMA-D`) remains `BLOCKED`** because external licensed datasets are unacquired in this repository. Shipped baseline ONNX models remain marked **`MODEL_UNVALIDATED`** (`MODEL_LOADED_UNVALIDATED`), suppressing discrete affective classifications.

---

## Core Capabilities (Phase 3.2)

- **Facial Expression Engine (`eon_ers.facial`):** Pure-CPU multi-candidate face detection (`0`, `1`, `N` faces), boundary validation, 5-point landmark eye alignment, quality gating, and `ONNXFacialModelAdapter`.
- **Vocal Affect & Audio Engine (`eon_ers.audio`, `eon_ers.speech`):** RIFF WAV (8/16/24/32-bit PCM) & raw PCM decoding, CPU polyphase resampling, adaptive `VoiceActivityDetector` separating speech from silence, acoustic prosody/MFCC extraction, and `ONNXSpeechModelAdapter`.
- **Text Affect Engine (`eon_ers.text`):** UTF-8/Unicode NFC normalization, zero-plaintext PII feature retention, distinct `TextSentiment` classification (`ExperimentalTextAffectAdapter` / `ONNXTextModelAdapter`).
- **Bounded Video Pipeline (`eon_ers.video`):** Streaming RIFF AVI (MJPEG) & animated GIF/WEBP decoding, configurable FPS & duplicate-frame sampling, corrupted-frame recovery, ephemeral IoU `SessionFaceTracker`, cancellation, and async job endpoints.
- **Quality-Aware 3-Modality Fusion (`eon_ers.fusion`):** Temporal alignment, 1-, 2-, and 3-modality Bayesian fusion, Jensen-Shannon conflict detection, correlated-agreement confidence dampening, and strict unvalidated diagnostic isolation.
- **Live Server, WebSocket & 15-View Console (`eon_ers.live`, `eon_ers.api`):** Full FastAPI `/api/v1/*` + legacy `/api/*`, versioned WebSocket protocol with bounded queue backpressure & heartbeats, PBKDF2 `APIKeyAuthManager` (RBAC + cross-user session isolation), `SlidingWindowRateLimiter`, and a responsive 15-view dark/light dashboard (`/`).
- **Training, Registry, Privacy & SDK (`eon_ers.training`, `eon_ers.models`, `eon_ers.privacy`, `eon_ers.sdk`):** `ModelRegistry` activation guard, `CheckpointManager`, Ed25519 `EvaluationExecutionProof`, `ConsentManager`, `assert_no_actuator_commands`, and `ERSClient` SDK.
- **CPU-First Deployment:** Hardened non-root `Dockerfile`, `docker-compose.yml`, and Nginx TLS proxy (`deploy/nginx.conf`).

---

## EON ERS for robotics and AI teams

OVIC Labs offers EON ERS for integration evaluation in human-facing robotics.
The on-device SDK and desktop viewer expose affective observations, face boxes,
signal quality, and abstention status. See the
[enterprise product brief and 1,000-case qualification report](docs/ers/ENTERPRISE_PRODUCT_BRIEF.md)
for current evaluation results and production acceptance criteria.

## Physical AI SDK

Install the Python SDK from a checkout. The `studio` extra includes the
OpenCV frontal-face detector and camera support.

```bash
python -m pip install ".[studio]"
```

### Analyze a photo and a transcript locally

Save this as `example.py` and run `python example.py portrait.jpg`.
The consent registration represents consent already collected from the
participant. Generate a new session for each independent sample.

```python
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

from ovic_eon.ers import ERSClient, ERSConfig


async def main() -> None:
    session_id, consent_reference = uuid4().hex, uuid4().hex
    async with ERSClient(config=ERSConfig(face_detector="opencv")) as ers:
        await ers.register_consent(session_id, consent_reference)
        try:
            image_bytes = Path(sys.argv[1]).read_bytes()
            face = await ers.analyze_image(session_id, consent_reference, image_bytes)
            print("Face box:", face.face_bbox)
            print("Facial status:", face.status.value)
            print("Validated:", face.is_validated)
            utterance = await ers.analyze_text(
                session_id, consent_reference, "I'm glad that worked."
            )
            print("Text status:", utterance.status.value)
        finally:
            await ers.revoke_consent(session_id)


asyncio.run(main())
```

### Analyze microphone PCM

Inside a registered local SDK session, pass mono signed 16-bit
little-endian PCM bytes and the capture sample rate.

```python
audio = await ers.analyze_audio(session_id, consent_reference, pcm_bytes, sample_rate=16000)
print(audio.status.value, audio.is_validated)
```

An integration can consume abstention, quality, and model status when
deciding how to respond. The same client also supports remote deployments
through `ERSClient(base_url="https://your-ers-server", api_key=...)`.
Local calls return Python observation objects. Remote calls return response
dictionaries. The base SDK retains the heuristic detector for compatibility.
Select `ERSConfig(face_detector="opencv")` to enable the OpenCV detector
explicitly. ERS Studio selects it for you.

SDK distributions exclude the synthetic baseline weights. The existing
standalone `eon-ers` distribution remains available. Choose one distribution
per environment because both provide the `eon_ers` implementation.

## Phase 2 · Emotional Memory System

EMS stores application-selected interaction summaries and user-confirmed preferences
in a local SQLite file. It runs offline through the same Python SDK.

```python
from ovic_eon.ems import EmotionalMemory

memory = EmotionalMemory("eon-memory.sqlite3", user_id="operator-42")
memory.remember_interaction("The operator asked to resume the calibration checklist.")
memory.confirm_preference("reply_style", "One short step at a time.", confirmed=True)

for item in memory.recall("calibration checklist", limit=3):
    print(item.kind, item.text)

preference = memory.get_preference("reply_style")
if preference is not None:
    print(preference.text)
    # Use memory.forget(preference.id) if the user asks to remove it.
```

### Production deployment

Use a stable user ID assigned by the host application. Authorize access to that
ID before opening EMS and only submit summaries the user has agreed to retain.
Set `confirmed=True` after the user confirms a preference. ERS observations
remain transient unless the host explicitly saves text.

```python
import os
from datetime import timedelta

from ovic_eon.ems import EmotionalMemory

memory = EmotionalMemory(
    "private/eon-memory.sqlite3",
    user_id="operator-42",
    encryption_key=bytes.fromhex(os.environ["EON_EMS_KEY_HEX"]),
    interaction_ttl=timedelta(days=90),
    max_interactions=1000,
    max_preferences=100,
)
```

Create the private directory first. Provision a random 32-byte key through
your application's secret manager and keep it separate from the database.
Use the same key when reopening this database. Losing the key leaves encrypted
contents unreadable. The numbers above are example deployment limits.

- **Storage.** Encrypted mode uses AES-256-GCM for summaries, preference keys,
  and values. It uses keyed tokens for recall. User IDs, timestamps, record
  types, ciphertext sizes, and token repetition within a user remain visible
  to someone with file access. Keep the database in a private directory.
- **Recall.** Results rank whole-word overlap before recency. Omit the query
  for recent results or use `kind="preference"` to filter.
- **Retention.** Expired interactions are excluded from recall and export.
  Interaction writes purge expired rows and evict the oldest interactions
  over the cap. Schedule `purge_expired()` for inactive users. Use consistent
  retention and cap settings across processes. New preferences at capacity
  raise `EMSError`. Existing preferences can still be updated.
- **User data requests.** `export_memories()` returns the caller's unexpired
  records. Exports contain readable text. Use `forget(id)` or `clear()` for
  deletion and apply the same policy to backups and exported copies.
- **Upgrade and recovery.** Existing plaintext databases open with the existing
  constructor and receive the retention schema upgrade. TTL applies to new
  writes. For encrypted operation, provision a new database and explicitly
  re-save only records authorized for migration. Use SQLite's online backup
  API for live databases and verify restoration with the corresponding key.
  Deployments should retain the key separately from backups.

## Run ERS Studio on your desktop

```bash
python -m pip install ".[studio]"
eon-ers-studio
```

Use **Start camera** for live observations or **Open image** to test a local
photo. The desktop app calls the SDK within its own process. It needs no web
server, account, API key, or password. **Stop** releases the camera. The
viewer displays the SDK's detected face box, evidence status, confidence,
and processing time. With an unvalidated model, the viewer withholds the
emotion estimate.

Use a desktop Python installation with Tkinter. On some Linux distributions
Tkinter is installed separately as `python3-tk`. For an authorized local
ONNX model, install `".[studio,ml]"` and pass
`eon-ers-studio --facial-model path/to/model.onnx`.
Models remain subject to the SDK's qualification checks.

## Run the browser dashboard locally

Install the browser dashboard extra from the SDK checkout, then start the server
in a terminal on the same computer as your browser.

```bash
python -m pip install ".[live]"
eon-ers-live --host 127.0.0.1 --port 8000 --open-browser
```

Leave the terminal running and open `http://127.0.0.1:8000/`. The launcher
can start without ONNX weights and will report unvalidated observations.
To load a local model, install `".[live,ml]"` and pass
`--facial-model /path/to/model.onnx` or `--speech-model /path/to/model.onnx`.

If the connection is refused, check the first error in the terminal and
make sure the browser uses the same port printed by the launcher. If port
8000 is occupied, use `--port 8001` and open `http://127.0.0.1:8001/`.
Loopback addresses refer to the computer running the browser. For the
desktop SDK viewer, use `eon-ers-studio` to open its own window.

---

## Documentation Index

- [Architecture Overview](docs/ers/ARCHITECTURE.md)
- [Installation Guide](docs/ers/INSTALLATION.md) | [Developer Guide](docs/ers/DEVELOPER_GUIDE.md) | [API Reference](docs/ers/API_REFERENCE.md)
- [Facial](docs/ers/FACIAL_RECOGNITION_GUIDE.md) | [Vocal](docs/ers/VOCAL_AFFECT_GUIDE.md) | [Text](docs/ers/TEXT_AFFECT_GUIDE.md) | [Video](docs/ers/VIDEO_PROCESSING_GUIDE.md) | [Fusion](docs/ers/MULTIMODAL_FUSION_GUIDE.md)
- [Live Webcam](docs/ers/LIVE_WEBCAM_GUIDE.md) | [Live Microphone](docs/ers/LIVE_MICROPHONE_GUIDE.md) | [Live Dashboard](docs/ers/LIVE_DASHBOARD_GUIDE.md)
- [Model Training](docs/ers/MODEL_TRAINING_GUIDE.md) | [Model Registry](docs/ers/MODEL_REGISTRY_GUIDE.md) | [Dataset Acquisition](docs/ers/DATASET_ACQUISITION_GUIDE.md) | [Model Evaluation](docs/ers/MODEL_EVALUATION_GUIDE.md)
- [Privacy & Consent](docs/ers/PRIVACY_AND_CONSENT.md) | [Security Policy](SECURITY.md) | [Contributing](CONTRIBUTING.md)
- [Deployment Guide](docs/ers/DEPLOYMENT_GUIDE.md) | [Production Operations](docs/ers/PRODUCTION_OPERATIONS.md) | [CPU Benchmarks](docs/ers/PERFORMANCE_BENCHMARKS.md) | [Troubleshooting](docs/ers/TROUBLESHOOTING.md)
- **[Phase 3.2 Final Qualification Report](docs/ers/PHASE_3_2_FINAL_QUALIFICATION_REPORT.md)**

## License

Apache License 2.0 ([LICENSE](LICENSE)). External affective datasets remain subject to their respective academic licenses.
