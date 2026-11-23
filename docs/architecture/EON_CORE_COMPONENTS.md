# OVIC EON — EON Core Internal Components Specification

**Document ID:** `EON-ARCH-CORE-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.3 — Design EON Core  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EON_CORE_ARCHITECTURE.md` (`EON-ARCH-CORE-004`)
- `docs/architecture/EON_CORE_INITIALIZATION.md` (`EON-ARCH-CORE-006`)
- `docs/architecture/EON_CORE_STATE_MODEL.md` (`EON-ARCH-CORE-007`)

---

## 1. Executive Summary

This document establishes the detailed responsibilities, interfaces, state, and dependencies of the internal subsystems comprising **EON Core**.

---

## 2. Component Roster

EON Core is organized into twelve decoupled internal components:

```text
+=======================================================================================+
| Component Name                   | Primary Architectural Responsibility               |
+=======================================================================================+
| 1. Core Application Manager      | Master coordinator and external lifecycle anchor   |
| 2. Component Registry            | System-wide service registration and discovery     |
| 3. Engine Registry               | Specific catalog for the seven intelligence engines|
| 4. Dependency Resolver           | Topological sorting and circular dependency checks |
| 5. Lifecycle Coordinator         | Orchestrates phased state machine transitions      |
| 6. Configuration Manager         | Validates and provides hierarchical configuration  |
| 7. Policy Enforcement Interface  | Validates envelopes, non-authoritative flags & PII |
| 8. Health Manager                | Heartbeat aggregation and fault status tracking    |
| 9. Event Interface               | Bridge to the in-memory asynchronous Event Bus     |
| 10. Context Interface            | Bridge to Session Context and Working Memory       |
| 11. Model Adapter Registry       | Catalog of local ML runtimes and inference engines |
| 12. Shutdown Coordinator         | Graceful drain and orderly resource disposal       |
+=======================================================================================+
```

---

## 3. Detailed Component Specifications

### 3.1 Core Application Manager (`CoreApplicationManager`)
- **Purpose:** Serve as the unified entry point for starting, running, and stopping EON.
- **Responsibilities:**
  - Instantiate and wire all Core subsystems.
  - Execute the 12-step initialization sequence.
  - Coordinate graceful shutdown upon OS signals (`SIGTERM`, `SIGINT`).
  - Expose top-level system state (`get_system_state() -> CoreState`).
- **Interfaces:**
  - `async initialize(config_path: str | Path | None) -> None`
  - `async start() -> None`
  - `async stop(timeout_seconds: float = 5.0) -> None`
  - `get_state() -> CoreState`

### 3.2 Component Registry (`ComponentRegistry`)
- **Purpose:** Manage registration, lookup, and dependency injection of all platform-level services (Event Bus, Context Manager, Health Supervisor).
- **Responsibilities:**
  - Register singleton services with type-safe lookup keys.
  - Prevent duplicate service registration.
  - Provide safe shutdown hooks for registered components.
- **Interfaces:**
  - `register_service(service_type: type[T], instance: T) -> None`
  - `get_service(service_type: type[T]) -> T`
  - `has_service(service_type: type) -> bool`

### 3.3 Engine Registry (`EngineRegistry`)
- **Purpose:** Dedicated catalog managing the registration, metadata inspection, and instance tracking of the seven intelligence engines.
- **Responsibilities:**
  - Register engine instances conforming to `EonEngineInterface`.
  - Validate engine IDs against the official roster (`ERS`, `EMS`, `ERE`, `PSE`, `SIE`, `ERG`, `HBU`).
  - Provide engine iteration in dependency-resolved order.
- **Interfaces:**
  - `register_engine(engine: EonEngineInterface) -> None`
  - `get_engine(engine_id: str) -> EonEngineInterface`
  - `get_all_engines() -> list[EonEngineInterface]`

### 3.4 Dependency Resolver (`DependencyResolver`)
- **Purpose:** Compute valid execution orders and detect cyclic dependencies across engines and components.
- **Responsibilities:**
  - Parse engine dependency declarations.
  - Perform topological sort using Kahn's algorithm / Tarjan's strongly connected components algorithm.
  - Reject circular dependency graphs at startup with detailed diagnostic traces.
  - Determine parallel startup tiers for independent engines.
- **Interfaces:**
  - `resolve_startup_order(engines: list[EonEngineInterface]) -> list[list[str]]`
  - `resolve_shutdown_order(engines: list[EonEngineInterface]) -> list[list[str]]`
  - `validate_dependencies(engines: list[EonEngineInterface]) -> None`

### 3.5 Lifecycle Coordinator (`LifecycleCoordinator`)
- **Purpose:** Govern the synchronized state progression of all registered engines.
- **Responsibilities:**
  - Execute phased startup: `initialize()` -> `start()`.
  - Execute phased shutdown: `stop()` -> resource cleanup.
  - Enforce per-engine timeouts on lifecycle calls (`DEFAULT_HANDLER_TIMEOUT`).
  - Isolate failed engines during startup without blocking healthy peers.
- **Interfaces:**
  - `async initialize_all(config: dict[str, Any]) -> None`
  - `async start_all() -> None`
  - `async stop_all(timeout_seconds: float) -> None`

### 3.6 Configuration Manager (`ConfigurationManager`)
- **Purpose:** Centralized, immutable configuration provider.
- **Responsibilities:**
  - Load YAML/JSON configuration files with schema validation via Pydantic v2.
  - Support environment variable overrides (`EON__SECTION__KEY`).
  - Scrub sensitive credentials and keys from diagnostic dumps.
- **Interfaces:**
  - `load_config(source: str | Path | dict[str, Any]) -> EonSystemConfig`
  - `get_engine_config(engine_id: str) -> dict[str, Any]`

### 3.7 Policy Enforcement Interface (`PolicyEnforcer`)
- **Purpose:** Gatekeeper validating all inter-component events against security and safety invariants.
- **Responsibilities:**
  - Verify `EventEnvelope[T]` version compatibility.
  - Enforce `is_authoritative_stop=False` on all actuation proposals.
  - Scrub `DataClassification.RESTRICTED` fields from telemetry logs.
- **Interfaces:**
  - `validate_outgoing_event(envelope: EventEnvelope[Any]) -> None`
  - `validate_actuation_proposal(proposal: Any) -> None`

### 3.8 Health Manager (`HealthManager`)
- **Purpose:** Continuously aggregate health, heartbeats, and error rates across all subsystems.
- **Responsibilities:**
  - Ingest `ComponentHealthPayload` events from engines.
  - Evaluate overall system health status: `HEALTHY`, `DEGRADED`, `FAILED`.
  - Dispatch `SafetyAdvisoryEvent` upon critical component failure.
- **Interfaces:**
  - `update_component_health(payload: ComponentHealthPayload) -> None`
  - `get_system_health() -> SystemHealthReport`

### 3.9 Event Interface (`CoreEventInterface`)
- **Purpose:** Provide EON Core with direct access to publish and subscribe to the underlying L5 Event Bus.
- **Responsibilities:**
  - Expose Core publish and subscribe primitives.
  - Route system lifecycle and health events.
- **Interfaces:**
  - `async publish(envelope: EventEnvelope[Any], priority: EventPriority) -> DeliveryOutcome`
  - `async subscribe(topic: str, handler: EventHandler) -> SubscriptionId`

### 3.10 Context Interface (`CoreContextInterface`)
- **Purpose:** Bridge EON Core to L6 Context and Memory services.
- **Responsibilities:**
  - Initialize session context upon user encounter.
  - Enforce session expiration and working memory cleanup.
- **Interfaces:**
  - `get_session_context(session_id: SessionId) -> InteractionContextPayload`
  - `reset_session_context(session_id: SessionId) -> None`

### 3.11 Model Adapter Registry (`ModelAdapterRegistry`)
- **Purpose:** Catalog and coordinate local inference runtimes in L7.
- **Responsibilities:**
  - Detect hardware capabilities (CPU SIMD, OpenVINO, RKNN, CUDA).
  - Register model adapters and verify model artifact checksums.
  - Report model memory usage and health to the Health Manager.
- **Interfaces:**
  - `register_adapter(adapter: InferenceAdapterInterface) -> None`
  - `get_adapter(model_id: str) -> InferenceAdapterInterface`

### 3.12 Shutdown Coordinator (`ShutdownCoordinator`)
- **Purpose:** Coordinate orderly, bounded termination of the entire EON runtime.
- **Responsibilities:**
  - Cease sensor ingestion in L2/L3.
  - Signal conversational turn disengagement in SIE.
  - Drain pending event bus queues up to configured timeout (`5.0s`).
  - Terminate background worker threads and flush logs.
- **Interfaces:**
  - `async execute_graceful_shutdown(timeout_seconds: float) -> ShutdownReport`
