# OVIC EON — Inter-Layer Interface Specifications

**Document ID:** `EON-ARCH-INT-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.1 — System Layered Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SYSTEM_LAYERED_ARCHITECTURE.md` (`EON-ARCH-LAYERS-001`)
- `docs/architecture/ARCHITECTURE_CONSTRAINTS.md` (`EON-ARCH-CONST-001`)
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)
- `docs/architecture/DATA_SCHEMA_ARCHITECTURE.md` (`EON-ARCH-SCHEMA-001`)

---

## 1. Executive Summary

This specification defines the explicit, strongly typed programmatic interfaces, Service Provider Interfaces (SPI), and event contract boundaries across all adjacent layers in the OVIC EON architecture.

To guarantee that components can be implemented, tested, and upgraded independently, no cross-layer communication may take place via undocumented private functions or informal conventions. Every boundary is governed by an explicit interface contract defined in this document.

---

## 2. Inter-Layer Boundary Matrix

```text
+===================================================================================+
| Boundary      | Interaction Pattern          | Contract Mechanism                 |
+===================================================================================+
| L1 <-> L2     | Hardware I/O Polling/Stream  | Kernel Device Protocols / Mock SPI |
| L2 <-> L3     | Normalized In-Memory Streams | Async Stream Generators (RAM Buff) |
| L3 <-> L5/L4  | Asynchronous Pub/Sub         | EventEnvelope[ObservationPayload]  |
| L5 <-> L4     | Lifecycle SPI & Event Routing| EonEngineInterface & EventBus      |
| L4 <-> L6     | Async Context & Storage SPI  | SessionContext & MemoryProvider    |
| L3/L4 <-> L7  | Bounded Local Execution      | InferenceAdapter & ModelRegistry   |
| L5 <-> L8     | In-Process / IPC Client API  | EonClient & ROS 2 Lifecycle Node   |
| L8 <-> L9     | Network API Protocols        | ASGI / HTTP REST / WebSockets      |
| All <-> L10   | Infrastructure & OS Control  | POSIX Signals, systemd, Cgroups    |
+===================================================================================+
```

---

## 3. Boundary Specifications

### 3.1 Layer 1 to Layer 2 Interface: Physical Hardware to HAL

The interface between physical hardware (L1) and the Device Abstraction Layer (L2) encapsulates OS kernel drivers and vendor-specific communication protocols.

#### 1. Camera Device Interface (`CameraDeviceInterface`)
```python
class CameraDeviceInterface(ABC):
    """Abstract interface for video capture hardware devices."""

    @abstractmethod
    async def open(self, device_path: str, config: CameraConfig) -> None:
        """Open and configure the camera sensor device."""
        ...

    @abstractmethod
    async def capture_frame(self) -> VideoFrameBuffer:
        """Read a single frame into volatile RAM.

        Raises:
            DeviceDisconnectedException: If physical sensor is unplugged.
            DeviceReadTimeoutException: If frame capture exceeds deadline.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Release sensor file descriptors and free memory."""
        ...

    @abstractmethod
    def get_diagnostics(self) -> DeviceDiagnostics:
        """Return frame rate, exposure, sensor temperature, and dropped frame counts."""
        ...
```

#### 2. Audio Capture Device Interface (`AudioInputDeviceInterface`)
```python
class AudioInputDeviceInterface(ABC):
    """Abstract interface for acoustic microphone elements and arrays."""

    @abstractmethod
    async def open(self, device_name: str, config: AudioConfig) -> None:
        """Initialize PCM capture stream (e.g. 16kHz mono or multi-channel)."""
        ...

    @abstractmethod
    async def read_chunk(self, chunk_samples: int) -> AudioChunkBuffer:
        """Read a discrete PCM chunk into an ephemeral ring buffer.

        Raises:
            DeviceBufferOverrunException: If ALSA buffer overruns.
            DeviceDisconnectedException: If USB mic is disconnected.
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close audio capture device handle."""
        ...
```

#### 3. Robot Telemetry Interface (`RobotTelemetryInterface`)
```python
class RobotTelemetryInterface(ABC):
    """Abstract interface for robot odometry, IMU, and joint state buses."""

    @abstractmethod
    async def read_odometry(self) -> OdometryState:
        """Read instantaneous linear (vx, vy) and angular (wz) velocities."""
        ...

    @abstractmethod
    async def read_joint_states(self) -> JointStateCollection:
        """Read head and neck pan/tilt angles for gaze compensation."""
        ...
```

---

### 3.2 Layer 2 to Layer 3 Interface: HAL to Perception Pipelines

The boundary between L2 (Device Abstraction) and L3 (Perception) transfers volatile memory buffers with zero disk writes.

#### Buffer Contract Models
```python
@dataclass(frozen=True)
class VideoFrameBuffer:
    """Ephemeral in-memory video frame."""

    frame_id: int
    timestamp_utc: datetime
    timestamp_monotonic_ns: int
    width: int
    height: int
    pixel_format: str  # e.g. "RGB888", "BGR888", "YUYV"
    data: memoryview  # Direct view into ring buffer RAM
    camera_id: str

    def zero_wipe(self) -> None:
        """Zero-overwrite memory buffer immediately after feature extraction."""
        ctypes.memset(ctypes.addressof(self.data), 0, len(self.data))


@dataclass(frozen=True)
class AudioChunkBuffer:
    """Ephemeral in-memory PCM audio chunk."""

    chunk_id: int
    timestamp_utc: datetime
    sample_rate_hz: int
    channels: int
    pcm_data: memoryview
    is_speech_active: bool | None = None
```

---

### 3.3 Layer 3 to Layer 5/4 Interface: Perception to Core Event Bus

Perception pipelines emit structured observations exclusively by wrapping them in Phase 1.2 `EventEnvelope[ObservationPayload]` instances and publishing them to the L5 Core Event Bus.

#### Published Event Envelope Contract
- **Topic Convention:** `observation.<modality>.<sub_type>` (e.g., `observation.visual.face_mesh`, `observation.audio.speech_emotion`, `observation.behaviour.pose_stgcn`, `observation.multimodal.fused`).
- **Payload Schema:** `eon.schemas.observations.ObservationPayload`
- **Envelope Metadata:**
  - `event_type`: `EventType.OBSERVATION` (`"eon.observation"`)
  - `source_id`: Originating perception node (e.g., `"eon.perc.vision"`)
  - `priority`: `EventPriority.NORMAL`
  - `classification`: `DataClassification.INTERNAL`
- **Safety Guarantee:** Contains non-authoritative flag: `is_authoritative_stop=False`.

---

### 3.4 Layer 5 to Layer 4 Interface: Core Runtime to Intelligence Engines (Engine SPI)

All seven intelligence engines implement the uniform `EonEngineInterface`. The L5 Core Lifecycle Manager controls engine initialization, startup, pause, resume, and shutdown via this SPI.

```python
class EonEngineInterface(ABC):
    """Uniform Service Provider Interface (SPI) implemented by all seven engines."""

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Unique engine identifier: ERS, EMS, ERE, PSE, SIE, ERG, or HBU."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Engine semantic version string."""
        ...

    @abstractmethod
    async def initialize(
        self, config: dict[str, Any], event_bus: EventBus, context_provider: Any
    ) -> None:
        """Perform one-time initialization, load configs, and register subscriptions.

        Must not spawn heavy long-running background tasks until start() is called.
        """
        ...

    @abstractmethod
    async def start(self) -> None:
        """Transition engine from CREATED to RUNNING.

        Activate worker tasks and begin processing event queues.
        """
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Temporarily suspend event consumption during robot docking/idle."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Resume processing after pause."""
        ...

    @abstractmethod
    async def stop(self, timeout_seconds: float) -> None:
        """Drain in-flight queues, cancel internal tasks, and release resources.

        Must complete cleanly within timeout_seconds.
        """
        ...

    @abstractmethod
    async def get_health(self) -> ComponentHealthPayload:
        """Return current component health status, error counts, and metrics."""
        ...
```

---

### 3.5 Layer 4 to Layer 6 Interface: Engines to Context and Memory

Engines access session context, working memory, and optional persistent storage through strongly typed context interfaces.

#### 1. Session Context Accessor (`SessionContextAccessor`)
```python
class SessionContextAccessor(ABC):
    """Interface for querying and updating the active interaction session."""

    @abstractmethod
    def get_current_session_id(self) -> SessionId:
        """Return active session UUID or anonymous default."""
        ...

    @abstractmethod
    def get_interaction_context(self) -> InteractionContextPayload:
        """Return current interaction stage, participant count, and engagement state."""
        ...

    @abstractmethod
    def update_interaction_stage(self, stage: InteractionStage, metadata: dict[str, Any]) -> None:
        """Update active 12-stage interaction state machine."""
        ...
```

#### 2. Long-Term Memory Service Provider Interface (`LongTermMemorySPI`)
```python
class LongTermMemorySPI(ABC):
    """SPI for persistent episodic and semantic interaction memory."""

    @abstractmethod
    async def store_record(self, record: MemoryRecord, user_consent_token: str) -> MemoryId:
        """Persist an episodic or preference record under active user consent.

        Raises:
            ConsentRevokedException: If consent scope does not permit retention.
            StorageQuotaExceededException: If local memory quota is reached.
        """
        ...

    @abstractmethod
    async def retrieve_memories(self, query: MemoryQuery) -> list[MemoryRecord]:
        """Query historical interaction records filtered by semantic relevance."""
        ...

    @abstractmethod
    async def delete_user_history(self, user_id: str, auth_token: str) -> DeletionConfirmation:
        """Verifiably delete all records and crypto-shred encryption keys for user_id."""
        ...
```

---

### 3.6 Layer 3/4 to Layer 7 Interface: Perception & Engines to Model Adapters

All local machine learning runtimes (ONNX Runtime, `llama.cpp`, Piper TTS) and deterministic rule systems are encapsulated within L7 Model Adapters.

#### 1. General Inference Adapter Interface (`InferenceAdapterInterface`)
```python
class InferenceAdapterInterface(ABC):
    """Abstract interface for local ML model execution."""

    @property
    @abstractmethod
    def model_id(self) -> str:
        """Identifier matching models.yaml registry."""
        ...

    @abstractmethod
    async def load(self, weights_path: Path, backend: ExecutionBackend) -> None:
        """Load model weights and initialize runtime execution session."""
        ...

    @abstractmethod
    async def execute(self, inputs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        """Execute synchronous model inference within an isolated threadpool.

        Raises:
            ModelExecutionTimeoutException: If execution exceeds allocated deadline.
            InferenceFailureException: If tensor shapes or execution fails.
        """
        ...

    @abstractmethod
    async def unload(self) -> None:
        """Unload weights from RAM/VRAM to free resources."""
        ...
```

#### 2. Local SLM Dialogue Generator Interface (`LlmAdapterInterface`)
```python
class LlmAdapterInterface(ABC):
    """Abstract interface for local quantized SLM text generation (llama.cpp)."""

    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        grammar_json_schema: str | None = None,
        max_tokens: int = 128,
        temperature: float = 0.7,
        timeout_seconds: float = 0.500,
    ) -> str:
        """Generate a constrained response within strict time bounds."""
        ...
```

#### 3. Neural TTS Synthesizer Interface (`TtsAdapterInterface`)
```python
class TtsAdapterInterface(ABC):
    """Abstract interface for local neural speech vocoding (Piper TTS)."""

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        pitch_shift: float = 0.0,
    ) -> AsyncIterator[AudioPlaybackChunk]:
        """Stream 16kHz PCM audio chunks with synchronized viseme phoneme timestamps."""
        ...
```

---

### 3.7 Layer 5 to Layer 8 Interface: Core Runtime to SDK and ROS 2 Bridge

The SDK and Integration Layer connects external robot processes to the EON Core Runtime.

#### 1. Asynchronous Client Interface (`AsyncEonClient`)
```python
class AsyncEonClient:
    """Primary asynchronous developer client for OVIC EON."""

    async def connect(self, endpoint: str = "in_process") -> None:
        """Connect to local in-process runtime or Unix domain socket."""
        ...

    async def publish_observation(self, observation: ObservationPayload) -> None:
        """Submit an observation into the EON processing pipeline."""
        ...

    async def register_emotion_callback(
        self, callback: Callable[[EmotionEstimatePayload], Awaitable[None]]
    ) -> SubscriptionId:
        """Subscribe to real-time consolidated emotion estimates."""
        ...

    async def register_response_proposal_callback(
        self, callback: Callable[[ResponseProposalPayload], Awaitable[None]]
    ) -> SubscriptionId:
        """Subscribe to generated multimodal dialogue and gesture proposals."""
        ...
```

#### 2. ROS 2 Integration Message Mapping
The ROS 2 bridge node (`eon_node`) translates between ROS 2 topics and EON event envelopes:
- `/eon/observations` (`eon_msgs/msg/Observation` -> `EventType.OBSERVATION`)
- `/eon/emotions` (`EventType.EMOTION_ESTIMATE` -> `eon_msgs/msg/EmotionEstimate`)
- `/eon/proposals` (`EventType.CUSTOM` / Response -> `eon_msgs/msg/ResponseProposal`)
- `/eon/safety_advisories` (`EventType.SAFETY_ADVISORY` -> `eon_msgs/msg/SafetyAdvisory`)
- Service `/eon/reset_session` (`eon_msgs/srv/ResetSession`)

---

### 3.8 Layer 8 to Layer 9 Interface: SDK to API Layer

L9 (FastAPI REST & WebSockets) exposes L8 SDK capabilities over standard HTTP/WS:

```text
+===================================================================================+
| HTTP Method & Route               | Function                | Output Schema       |
+===================================================================================+
| GET /api/v1/health                | System Health Report    | ComponentHealthPayload|
| GET /api/v1/metrics               | Bus Performance Metrics | EventBusMetricsSnap |
| GET /api/v1/engines               | Engine Status Roster    | list[EngineReport]  |
| GET /api/v1/session/current       | Active Session State    | InteractionContext  |
| POST /api/v1/session/reset        | Reset Interaction Turn  | OperationResult     |
| POST /api/v1/memory/purge         | User Data Erasure (GDPR)| DeletionReceipt     |
| WS /api/v1/stream/events          | Real-Time Event Stream  | EventEnvelope (JSON)|
+===================================================================================+
```

---

### 3.9 All Layers to Layer 10 Interface: Infrastructure, OS & Supervision

All EON software components interact with L10 via standard OS mechanisms:
- **POSIX Signal Handling:** `SIGTERM` and `SIGINT` trigger graceful shutdown sequences through `EventBus.stop()`.
- **Systemd Watchdog:** L5 Core periodically sends `sd_notify("WATCHDOG=1")` heartbeats every 2.0s; systemd restarts the daemon if heartbeats cease for >10.0s.
- **Log Aggregation:** Standard structured JSON log lines emitted to `stdout`/`stderr` captured by `journald`.
- **Resource Quotas:** Enforced via Linux cgroups v2 (`MemoryMax=2048M`, `CPUQuota=250%`).
