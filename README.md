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

## EON module boundaries

| Phase | Module | Responsibility | Integration | Status |
| --- | --- | --- | --- | --- |
| 1 | ERS · Emotion Recognition System | Produce qualified, uncertainty-aware observations | Supplies an optional observation to ERE | SDK available |
| 2 | EMS · Emotional Memory System | Store user-approved summaries and confirmed preferences | Supplies scoped references and preferences to ERE | SDK available |
| 3 | ERE · Empathy Reasoning Engine | Select a response strategy from explicit needs and permitted context | Produces a versioned plan for PSE, SIE and ERG | SDK available |
| 4 | PSE · Personality Simulation Engine | Apply the agent's approved communication style | Produces a versioned delivery plan from ERE for SIE and ERG | SDK available |
| 5 | SIE · Social Interaction Engine | Manage turn-taking and dialogue lifecycle | Uses ERE and PSE plans to authorize delivery or pause for the current session | SDK available |
| 6 | ERG · Emotional Response Generation | Render a response from the plan and approved context | Renders host-approved content only for a current SIE turn | SDK available |
| 7 | HBU · Human Behavior Understanding | Interpret the user's goal and interaction context | Supplies explicit-request proposals for the host to review before ERE | SDK available |

The host remains responsible for user identity, consent, and session binding.
It decides which modules run per turn. For example, it can invoke ERE with
an explicit user goal while ERS and EMS are unavailable.

## Engine packages

| Engine | Source package | Distribution | Python import |
| --- | --- | --- | --- |
| ERS | [packages/ers](packages/ers) | `eon-ers` | `eon_ers` |
| EMS | [packages/ems](packages/ems) | `eon-ems` | `eon_ems` |
| ERE | [packages/ere](packages/ere) | `eon-ere` | `eon_ere` |
| PSE | [packages/pse](packages/pse) | `eon-pse` | `eon_pse` |
| SIE | [packages/sie](packages/sie) | `eon-sie` | `eon_sie` |
| ERG | [packages/erg](packages/erg) | `eon-erg` | `eon_erg` |
| HBU | [packages/hbu](packages/hbu) | `eon-hbu` | `eon_hbu` |

Build the seven local distributions from an EON checkout:

```bash
python -m pip install build
for engine in ers ems ere pse sie erg hbu; do
    python -m build "packages/$engine" --outdir dist
done
```

For an EMS-only installation, run `python -m pip install ./packages/ems`.
Install the full standalone chain from the checkout with:

```bash
python -m pip install ./packages/ers ./packages/ems ./packages/ere ./packages/pse ./packages/sie ./packages/erg ./packages/hbu
```

The repository root still builds the unified `ovic-eon` wheel, including the
same implementation and the `ovic_eon.ers`, `ovic_eon.ems`, `ovic_eon.ere`,
`ovic_eon.pse`, `ovic_eon.sie`, `ovic_eon.erg`, and `ovic_eon.hbu` imports. Use the unified wheel or install the standalone
packages in a separate environment because these distributions share import
names. The standalone packages are buildable from source. This change
does not publish them to an external package registry.

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

SDK distributions exclude the synthetic baseline weights.

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

## Phase 3 · Empathy Reasoning Engine

ERE is a deterministic, offline policy module. It returns structured guidance
for the host or a downstream dialogue module. A live request to give space
bypasses both memory lookup and affect cues. An explicit request for concise
or detailed replies takes precedence over a stored `reply_style` preference.

```python
from ovic_eon.ems import EmotionalMemory
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal, ReportedNeed

# Open the scope authorized by the application. In deployments, use the
# encrypted EMS settings above.
memory = EmotionalMemory("eon-memory.sqlite3", user_id="operator-42")
memory.confirm_preference("reply_style", "concise", confirmed=True)

plan = EmpathyEngine().reason(
    EmpathyRequest(
        user_id="operator-42",
        goal=InteractionGoal.SOLVE,
        reported_need=ReportedNeed.FRUSTRATED,
        use_memory=True,
        memory_query="calibration checklist",
    ),
    memory=memory,
)

assert plan.strategy.value == "offer_next_step"
assert plan.acknowledge_reported_need
print(plan.model_dump_json())
```

- **ERS handoff.** The host can pass its current, session-bound
  `EmotionObservation` as `observation=observation` when the user has opted
  into that input. Set `use_affect_cue=True` for that turn. A fresh, calibrated
  and validated observation with sufficient signal quality may suggest a
  gentle check-in. The plan carries no inferred emotion label and keeps the
  requested action. The engine ignores the current unvalidated baseline.
- **EMS handoff.** Set `use_memory=True` only for authorized retrieval.
  Mismatched user scopes fail closed. Unavailable memory produces a usable
  plan with `memory_status="unavailable"`. Relevant summaries appear as up
  to three reference IDs. The host can resolve an authorized reference
  with `memory.get_memory(id)` and treat the returned text as conversation
  context. ERE performs no writes.
- **Downstream handoff.** Pass the versioned `ResponsePlan` to the host's
  dialogue code. A plan describes response behavior. The host owns
  text generation, tool authorization, and robot control.

## Phase 4 · Personality Simulation Engine

PSE applies a host-approved communication profile to an ERE response plan.
It runs locally and returns a versioned `DeliveryPlan` for the host's
dialogue code. The plan controls formality, pace, warmth and a sentence
limit. ERE continues to own the interaction strategy and the current
concise or detailed request.

```python
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal, ReportedNeed
from ovic_eon.pse import PersonalityEngine, PersonalityProfile

response = EmpathyEngine().reason(
    EmpathyRequest(
        user_id="operator-42",
        goal=InteractionGoal.SOLVE,
        reported_need=ReportedNeed.FRUSTRATED,
    )
)
profile = PersonalityProfile(
    profile_id="operator-console",
    revision=2,
    pace="measured",
    concise_sentence_limit=2,
    detailed_sentence_limit=5,
)
engine = PersonalityEngine(profiles=(profile,), default_profile=profile.profile_id)
delivery = engine.style(response)

assert delivery.strategy == response.strategy
assert delivery.sentence_limit == 2
print(delivery.model_dump_json())
```

Built-in profiles are `professional`, `friendly`, and `formal`. Load any
custom profiles from trusted deployment configuration. You can review the
available profiles with `list_profiles()` and select one per turn with
`style(response, profile_id="formal")`. Unknown and duplicate profile IDs
raise an error. A neutral ERE tone caps warmth to reserved. A request to
give space produces a pause with zero sentences and no check-in. SIE can
use the delivery mode when scheduling turns, and ERG can use the style
controls when rendering a response. The host enforces the output limits
and retains responsibility for text generation, tools and hardware.

## Phase 5 · Social Interaction Engine

SIE coordinates one local interaction session. It accepts a matching ERE
response plan and PSE delivery plan, and issues at most one active turn ID.

```python
from ovic_eon.ere import EmpathyEngine, EmpathyRequest, InteractionGoal
from ovic_eon.pse import PersonalityEngine
from ovic_eon.sie import SocialInteractionEngine, TurnAction

session = SocialInteractionEngine(session_id="robot-session-42", turn_timeout_seconds=30)
response = EmpathyEngine().reason(
    EmpathyRequest(user_id="operator-42", goal=InteractionGoal.EXPLAIN)
)
delivery = PersonalityEngine().style(response)
turn = session.submit(response, delivery)
assert turn.action == TurnAction.RESPOND and turn.turn_id is not None
# The host starts rendering here and completes the turn after delivery ends.
assert session.complete(turn.turn_id)
```

- **Busy turns.** `BUSY` means no new turn was accepted. The host decides
  whether to retry with fresh context. SIE keeps no backlog of plans.
- **Interruptions.** Call `interrupt()` to cancel live output. Call `pause()`
  when the user requests space, or submit an ERE/PSE give-space plan. Stop
  output for the cancelled ID and call `resume()` only when appropriate for
  the user. A late completion cannot release a different turn.
- **Timeout and teardown.** Poll `expire_overdue()` from the host scheduler.
  Cancel output for any ID it returns. Call `close()` at session teardown.
  A closed session requires a new engine instance.
- **Deployment boundary.** Bind each engine to one authenticated application
  session and serialize delivery and cancellation in the host renderer.
  Use `snapshot()` to check the current turn before delivery. The host owns
  speech or display output, hardware controls, and timers. SIE uses
  process-local state. ERG checks that the accepted decision is still current
  before rendering.

## Phase 6 · Emotional Response Generation

ERG renders bounded, plain-text responses from a current SIE decision.
It applies the response strategy, personality, and sentence budget. A pause,
cancellation, expired turn, or mismatched session yields no rendered response.
For explanations and next steps, supply plain answer clauses approved by the
host. ERG uses deterministic templates and does not call a language model.

## Phase 7 · Human Behavior Understanding

HBU proposes interaction goals and self-reported needs from a bounded
English command grammar. Unsupported phrasing and conflicting requests
return an abstention status. The host reviews the proposal before converting
it to an ERE request. HBU returns no raw utterance and writes nothing to EMS.

### Run the complete interaction pipeline

```python
from ovic_eon.ere import EmpathyEngine
from ovic_eon.erg import EmotionalResponseGenerator, ResponseContent
from ovic_eon.hbu import HumanBehaviorEngine, ProposalStatus
from ovic_eon.pse import PersonalityEngine
from ovic_eon.sie import SocialInteractionEngine

proposal = HumanBehaviorEngine().interpret("I feel frustrated. Help me restart this.")
assert proposal.status == ProposalStatus.RECOGNIZED

# The host has checked the interpretation and authorized this user and session.
request = proposal.to_empathy_request(user_id="operator-42", confirmed=True)
response = EmpathyEngine().reason(request)
delivery = PersonalityEngine().style(response, profile_id="friendly")
session = SocialInteractionEngine(session_id="robot-session-42")
turn = session.submit(response, delivery)
rendered = EmotionalResponseGenerator().render(
    session,
    turn,
    content=ResponseContent(clauses=("Open the settings menu",)),
)
if rendered is not None:
    print(rendered.text)
    session.complete(rendered.turn_id)
```

The host can supply an authorized EMS store and a current ERS observation to
ERE when the relevant opt-ins are set. Treat ERG output as plain text and
coordinate delivery and cancellation by turn ID. The host owns identity,
live media capture, playback, timers, and any robot action. The current
ERS baseline continues to abstain without a qualified emotion model.

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
