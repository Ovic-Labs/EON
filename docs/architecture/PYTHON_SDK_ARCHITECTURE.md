# EON Python SDK Architecture Specification

**Document ID:** `EON-ARCH-SDK-001`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `ARCHITECTURE SPECIFICATION`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/SYSTEM_LAYERED_ARCHITECTURE.md` (`EON-ARCH-001`)  
**Cross-References:**  
- `docs/architecture/API_ARCHITECTURE.md` (`EON-ARCH-API-001`)  
- `docs/architecture/EON_CORE_ARCHITECTURE.md` (`EON-ARCH-CORE-004`)  
- `docs/architecture/EVENT_DRIVEN_COMMUNICATION.md` (`EON-ARCH-COMM-001`)  
- `docs/architecture/SHARED_CONTEXT_ARCHITECTURE.md` (`EON-ARCH-CTX-001`)  
- `docs/architecture/MODEL_ADAPTER_ARCHITECTURE.md` (`EON-ARCH-MOD-001`)  
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)  

---

## 1. Executive Summary & Purpose

The OVIC EON Python Software Development Kit (SDK) provides an idiomatic, strongly-typed, high-performance programmatic interface to the EON Emotional Intelligence Infrastructure. It serves as the primary integration boundary for robotics engineers, application developers, and human-robot interaction (HRI) researchers developing emotional intelligence workflows.

This document establishes the foundational architectural specifications for the Python SDK, covering its core responsibilities, dual-mode client design (In-Process direct component binding vs. Remote networked transport), synchronous and asynchronous programming paradigms, dependency isolation boundaries, and relationship to the underlying EON Core and API Gateway layers.

> [!IMPORTANT]
> The code listings throughout this document represent architectural contract specifications and illustrative client patterns. Per Phase 2 engineering governance, production intelligence engine runtimes are not implemented within this phase.

---

## 2. SDK Responsibilities & Design Principles

### 2.1 Core Responsibilities

The EON Python SDK is responsible for:

1. **Client Ergonomics & Idiomatic Interface:** Providing an intuitive Pythonic API complying with PEP 8, PEP 484 (type hints), PEP 561 (typing distribution marker), and modern async/await patterns (PEP 492).
2. **Dual-Mode Execution:** Seamlessly switching between **Local In-Process Mode** (direct shared-memory and component binding for zero-overhead robot on-board execution) and **Remote Client Mode** (REST, WebSocket, and gRPC communication across networks via the EON API Gateway).
3. **Transport & Protocol Abstraction:** Encapsulating network serialization, connection pooling, multiplexing, transport negotiation, and protocol translation (HTTP/JSON, gRPC/Protobuf, WebSocket).
4. **Lifecycle & Resource Management:** Supporting context-managed sessions (`with` and `async with`), deterministic socket cleanup, keep-alives, and graceful connection teardown.
5. **Resilience & Fault Tolerance:** Automatic connection failover, exponential backoff with randomized jitter, heartbeating, and declarative idempotent request retries.
6. **Strict Security & Authentication:** Transparent handling of mTLS client certificates, API keys, JWT bearer token lifecycle (automatic refresh), and least-privilege capability headers.
7. **Strong Typing & Data Validation:** Type-safe models for all domain entities, inputs, outputs, events, and errors utilizing runtime-validated structures (Pydantic / dataclasses).

### 2.2 Design Principles

| Principle | Architectural Mandate |
| :--- | :--- |
| **Zero Runtime Lock-In** | The SDK client interface remains identical whether operating locally in-process or remotely across a network gateway. |
| **Type Safety First** | 100% type annotation coverage. Full compliance with `mypy --strict`. Zero reliance on untyped `Any` dictionaries for public APIs. |
| **Async Native, Sync Friendly** | Built from the ground up on modern `asyncio`. Synchronous interfaces are provided via an ergonomic wrapper layer over the async core. |
| **Lean Core Dependencies** | Minimal foundational dependencies (`httpx`, `pydantic`, `typing-extensions`). Heavy dependencies (gRPC, PyTorch, ROS 2) are optional extras. |
| **Fail-Safe & Predictable** | Deterministic error hierarchies rooted in `EonError`. Rich diagnostic exceptions without leaking raw socket errors or stack traces to callers. |
| **Memory & CPU Efficiency** | Zero-copy streaming when possible, efficient buffer reuse, and connection connection pooling to prevent descriptor exhaustion on edge compute. |

---

## 3. Dual-Mode Client Architecture

The EON Python SDK supports two operational execution modes through a unified client abstraction:

```text
+-------------------------------------------------------------------------------+
|                             EON Python SDK Interface                           |
|         (EonClient [Sync]  /  AsyncEonClient [Async]  /  Subsystem Clients)   |
+-------------------------------------------------------------------------------+
                                      |
                   Mode Negotiation & Runtime Binding
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+-------------------------------+         +-------------------------------------+
|     Local In-Process Mode     |         |         Remote Client Mode          |
|  (Direct In-Memory Binding)   |         |     (Networked Transport Layer)     |
+-------------------------------+         +-------------------------------------+
| - Zero serialization overhead |         | - HTTP/REST Transport (httpx)       |
| - Shared memory event bus     |         | - WebSocket Client (streaming)      |
| - Direct Engine / Core calls  |         | - gRPC Transport (Protobuf)         |
| - Sub-millisecond latency     |         | - TLS 1.3 / mTLS / JWT Auth         |
| - Dedicated to Edge Compute   |         | - Cloud / Distributed Robot Fleet   |
+-------------------------------+         +-------------------------------------+
         |                                                         |
         v                                                         v
+-------------------------------+         +-------------------------------------+
|        EON Core Kernel        |         |           EON API Gateway           |
| (Context, Broker, Lifecycle)  |         | (docs/architecture/API_ARCHITECTURE)|
+-------------------------------+         +-------------------------------------+
```

### 3.1 Local In-Process Mode

In **Local In-Process Mode**, the SDK binds directly to the running EON Core runtime within the same Python interpreter or native host process:
- **Use Case:** Robot onboard compute (e.g., NVIDIA Jetson AGX Orin, Advantech edge nodes) where minimal latency and zero serialization overhead are mandatory.
- **Mechanism:** Direct Python module references and memory pointers to `eon.core.kernel.Kernel`, `eon.core.context.ContextManager`, and `eon.core.broker.EventBroker`.
- **Latency Target:** $< 0.5\text{ ms}$ call latency for context lookups and synchronous event dispatching.
- **Concurrency:** Leverages Python `asyncio` loop running alongside core task supervisors; inter-engine threading managed via OS-native worker threads.

### 3.2 Remote Client Mode

In **Remote Client Mode**, the SDK communicates across a network boundary with an external EON instance:
- **Use Case:** Distributed architectures, remote teleoperation stations, developer workstations, fleet management dashboards, and microservice containers.
- **Mechanism:** Transport adapters executing against the EON API Gateway (`EON-ARCH-API-001`):
  - **HTTP/REST Transport:** JSON/Protobuf requests over HTTP/1.1 or HTTP/2 using persistent connection pools (`httpx.AsyncClient`).
  - **WebSocket Transport:** Bidirectional, full-duplex event streaming, subscription management, and push notifications.
  - **gRPC Transport:** High-throughput, strongly-typed binary RPC and bidirectional streaming (available when `[grpc]` extra is installed).
- **Security:** Hardware-accelerated TLS 1.3, optional mTLS mutual verification, and automated token injection.

---

## 4. Synchronous vs. Asynchronous Programming Paradigms

The SDK provides parallel interfaces tailored to different application architectures:

```text
               +----------------------------------+
               |        BaseClient (Protocol)     |
               +----------------------------------+
                                |
             +------------------+------------------+
             |                                     |
             v                                     v
+--------------------------+         +--------------------------+
|      AsyncEonClient      |         |        EonClient         |
|      (Async Native)      |         |     (Sync Ergonomic)     |
+--------------------------+         +--------------------------+
| - Coroutine-based        |         | - Blocking call wrappers |
| - High concurrency       |         | - Simple scripting & CLI |
| - Async generators/iter  |         | - Thread-safe wrappers   |
| - Non-blocking I/O       |         | - Synchronous iterators  |
| - PEP 492 (async/await)  |         | - Legacy codebase compat |
+--------------------------+         +--------------------------+
```

### 4.1 Asynchronous Interface (`AsyncEonClient`)

The asynchronous client is the native, primary implementation. All I/O operations are non-blocking coroutines running within an `asyncio` event loop:
- High concurrency: Capable of maintaining hundreds of concurrent event streams and perception updates on edge hardware.
- Real-time streaming: Uses asynchronous iterators (`async for event in client.events.subscribe(...)`).
- Resource cleanup: Clean shutdown via asynchronous context managers (`async with AsyncEonClient(...) as client:`).

### 4.2 Synchronous Interface (`EonClient`)

The synchronous client is an ergonomic wrapper designed for standard scripts, notebooks, legacy sync applications, and simple test harnesses:
- Thread-safe blocking execution: Dispatches calls to an internal managed `asyncio` loop running on a dedicated background thread or resolves futures cleanly.
- Simple synchronous iterators: Implements generator-based event stream consumption with background queue buffering.
- Familiar context management: Standard `with EonClient(...) as client:` block semantics.

---

## 5. Architectural Relationship to EON Subsystems

The Python SDK acts as the unifier for all underlying Phase 2 architectural subsystems:

```text
+---------------------------------------------------------------------------------------+
|                                    EonClient Architecture                              |
+---------------------------------------------------------------------------------------+
  |                   |                   |                   |                   |
  v                   v                   v                   v                   v
+-------------+     +-------------+     +-------------+     +-------------+     +-------------+
|   Engines   |     |   Events    |     |   Context   |     |   Models    |     |   Health    |
|   Client    |     |   Client    |     |   Client    |     |   Client    |     |   Client    |
+-------------+     +-------------+     +-------------+     +-------------+     +-------------+
  |                   |                   |                   |                   |
  | Lifecycle         | Pub/Sub           | Shared Context    | Inference &       | Liveness &  |
  | State & Control   | Taxonomy          | Access Control    | Adapters          | Telemetry   |
  | EON-ARCH-LIFE-001 | EON-ARCH-COMM-001 | EON-ARCH-CTX-001  | EON-ARCH-MOD-001  | EON-CORE-004|
  v                   v                   v                   v                   v
+---------------------------------------------------------------------------------------+
|                   Unified Transport Abstraction (Local Direct / Remote Gateway)       |
+---------------------------------------------------------------------------------------+
```

1. **EON Core (`EON-ARCH-CORE-004`):** SDK manages boot parameters, kernel health monitoring, and system-level configuration synchronization.
2. **Engine Lifecycle (`EON-ARCH-LIFE-001`):** `client.engines` provides lifecycle transition triggers (`start`, `stop`, `pause`, `recover`) and state queries across the seven engines.
3. **Event-Driven Communication (`EON-ARCH-COMM-001`):** `client.events` wraps envelope packing/unpacking, topic taxonomy resolution, WebSocket/shared-memory streaming, and ACK tracking.
4. **Shared Context Manager (`EON-ARCH-CTX-001`):** `client.context` provides typed read/write access to human profiles, interaction state, active sessions, and privacy-filtered views.
5. **Model Adapter Layer (`EON-ARCH-MOD-001`):** `client.models` enables runtime model status inspection, warm-up triggering, fallback routing policies, and latency metrics retrieval.
6. **Data & Storage Layer (`EON-ARCH-DATA-001`):** Transparently adheres to data retention classifications, user consent scopes, and audit logging.

---

## 6. Illustrative Architecture Examples

> [!NOTE]
> The following 9 illustrative architecture examples demonstrate intended programmatic workflows, client ergonomics, typing usage, and dual-mode interactions with EON architectural subsystems. They are illustrative engineering specifications and do not imply production model inference runtime execution in Phase 2.

### 6.1 Example 1: Basic Synchronous Client Initialization and Health Inspection

```python
"""Illustrative Architecture Example 1: Basic Synchronous Client Initialization."""

from eon.client import EonClient
from eon.models.health import SystemHealthResponse


def inspect_system_health() -> None:
    """Connect to EON via sync client and inspect system health."""
    # Initialize client in remote mode targeting gateway
    with EonClient(
        base_url="https://edge-robot.local:8443", api_key="eon_test_key_abc123"
    ) as client:
        health: SystemHealthResponse = client.health.get_status()
        print(f"System State: {health.status.value}")
        print(f"Active Engines: {health.engines_healthy}/{health.engines_total}")
        for engine, status in health.engine_details.items():
            print(f" - {engine}: {status.state.value} (Uptime: {status.uptime_s}s)")


if __name__ == "__main__":
    inspect_system_health()
```

### 6.2 Example 2: Asynchronous Event Subscription and Real-Time Perception Stream

```python
"""Illustrative Architecture Example 2: Asynchronous Event Subscription."""

import asyncio
from eon.client import AsyncEonClient
from eon.models.events import EventEnvelope, PerceptionFaceDetectedPayload


async def stream_perception_events() -> None:
    """Subscribe to real-time face detection events over WebSocket transport."""
    async with AsyncEonClient(base_url="https://edge-robot.local:8443") as client:
        # Subscribe to perception domain topic
        subscription = await client.events.subscribe(
            topics=["eon.perception.face.detected"], client_id="navigation_safety_node"
        )
        print("Connected to event stream. Waiting for perception events...")

        async for event in subscription:
            if isinstance(event.payload, PerceptionFaceDetectedPayload):
                print(
                    f"[{event.timestamp.isoformat()}] User Detected: "
                    f"id={event.payload.subject_id}, "
                    f"confidence={event.payload.confidence:.2f}, "
                    f"bounding_box={event.payload.bounding_box}"
                )


if __name__ == "__main__":
    asyncio.run(stream_perception_events())
```

### 6.3 Example 3: Shared Context Read and Write with Privacy Scoping

```python
"""Illustrative Architecture Example 3: Shared Context Interaction."""

import asyncio
from eon.client import AsyncEonClient
from eon.models.context import UserProfileContext, EngagementState


async def update_user_interaction_context() -> None:
    """Read and update user context ensuring privacy retention tags."""
    async with AsyncEonClient(base_url="https://edge-robot.local:8443") as client:
        subject_id = "user_4982a"

        # Fetch current user profile context
        context: UserProfileContext = await client.context.get_user_profile(
            subject_id=subject_id, scope="engagement_read"
        )
        print(f"Subject: {context.subject_id}, Known Preferences: {context.preferences}")

        # Update engagement state with confidence score and epistemological qualification
        await client.context.update_engagement(
            subject_id=subject_id,
            engagement=EngagementState(
                level="ATTENTIVE",
                confidence=0.88,
                interaction_turn=4,
                source_engine="eon-engine-engagement",
            ),
        )
        print("Successfully updated engagement state in shared context.")


if __name__ == "__main__":
    asyncio.run(update_user_interaction_context())
```

### 6.4 Example 4: Engine Lifecycle Management and Recovery Execution

```python
"""Illustrative Architecture Example 4: Engine Lifecycle Management."""

import asyncio
from eon.client import AsyncEonClient
from eon.models.lifecycle import EngineState, TransitionResult


async def manage_engine_lifecycle() -> None:
    """Inspect and trigger lifecycle recovery on an intelligence engine."""
    async with AsyncEonClient(base_url="https://edge-robot.local:8443") as client:
        engine_id = "eon-engine-speech"

        state = await client.engines.get_state(engine_id=engine_id)
        print(f"Current state of {engine_id}: {state.value}")

        if state == EngineState.DEGRADED:
            print(f"Engine {engine_id} is degraded. Initiating graceful restart...")
            result: TransitionResult = await client.engines.recover(
                engine_id=engine_id, timeout_s=10.0
            )
            print(
                f"Recovery finished: Success={result.success}, New State={result.new_state.value}"
            )


if __name__ == "__main__":
    asyncio.run(manage_engine_lifecycle())
```

### 6.5 Example 5: Model Adapter Status and Latency Inspection

```python
"""Illustrative Architecture Example 5: Model Adapter Inspection."""

import asyncio
from eon.client import AsyncEonClient
from eon.models.models import ModelInspectionReport


async def audit_model_adapters() -> None:
    """Inspect registered neural models, hardware backends, and latencies."""
    async with AsyncEonClient(base_url="https://edge-robot.local:8443") as client:
        adapters: list[ModelInspectionReport] = await client.models.list_active_models()
        print(f"Total Registered Model Adapters: {len(adapters)}")

        for report in adapters:
            print(
                f"Model: {report.model_id} ({report.version}) | "
                f"Backend: {report.backend.value} | "
                f"Device: {report.device} | "
                f"P95 Latency: {report.p95_latency_ms:.2f}ms | "
                f"Fallback: {report.fallback_active}"
            )


if __name__ == "__main__":
    asyncio.run(audit_model_adapters())
```

### 6.6 Example 6: Local In-Process Direct Binding Mode

```python
"""Illustrative Architecture Example 6: Local In-Process Direct Binding."""

from eon.client import EonClient
from eon.config import EonConfig


def run_local_embedded_agent() -> None:
    """Execute SDK in Local In-Process mode binding directly to on-board Kernel."""
    # Configure in-process direct binding mode (no HTTP / gateway overhead)
    config = EonConfig(
        execution_mode="local_in_process",
        core_config_path="/etc/eon/kernel.yaml",
        memory_bus_size_mb=64,
    )

    with EonClient.from_config(config) as client:
        print("SDK bound directly to local EON Kernel in memory.")
        # Local direct invocation bypasses JSON serialization
        status = client.health.get_status()
        print(f"Kernel Uptime: {status.uptime_seconds:.3f}s")
        print(f"Direct In-Memory Event Dispatcher: {client.is_local}")


if __name__ == "__main__":
    run_local_embedded_agent()
```

### 6.7 Example 7: Error Handling and Resilient Retry Flow

```python
"""Illustrative Architecture Example 7: Resilient Error Handling."""

import asyncio
from eon.client import AsyncEonClient
from eon.exceptions import (
    EonConnectionError,
    EonTimeoutError,
    EonAuthenticationError,
    EonRateLimitError,
    EonError,
)


async def robust_client_operation() -> None:
    """Demonstrate robust exception handling across network failure modes."""
    client = AsyncEonClient(
        base_url="https://edge-robot.local:8443",
        timeout=3.0,
        max_retries=3,
        retry_jitter=True,
    )

    try:
        await client.connect()
        profile = await client.context.get_user_profile("user_123")
        print(f"Retrieved profile: {profile}")
    except EonAuthenticationError as exc:
        print(f"Authentication rejected: {exc.detail}. Check API credentials.")
    except EonRateLimitError as exc:
        print(f"Rate limited by Gateway. Retry after: {exc.retry_after_s} seconds.")
    except (EonConnectionError, EonTimeoutError) as exc:
        print(f"Network transport fault: {exc}. Automatic retries exhausted.")
    except EonError as exc:
        print(f"General EON SDK operational fault: {exc}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(robust_client_operation())
```

### 6.8 Example 8: Secure Token-Based Client Authentication

```python
"""Illustrative Architecture Example 8: Token Authentication and mTLS."""

import asyncio
from eon.client import AsyncEonClient
from eon.security import SecurityConfig


async def connect_with_mtls_and_jwt() -> None:
    """Initialize client with mTLS certificates and JWT Bearer token."""
    security_config = SecurityConfig(
        tls_ca_cert_path="/etc/eon/certs/ca.pem",
        client_cert_path="/etc/eon/certs/client_robot_node.pem",
        client_key_path="/etc/eon/certs/client_robot_node.key",
        jwt_token_provider=lambda: "eyJhbGciOiJSUzI1NiIsInR5cCI6...",
    )

    async with AsyncEonClient(
        base_url="https://secure-robot.local:8443", security=security_config
    ) as client:
        token_info = await client.auth.get_token_claims()
        print(f"Authenticated as: {token_info.subject} | Scopes: {token_info.scopes}")


if __name__ == "__main__":
    asyncio.run(connect_with_mtls_and_jwt())
```

### 6.9 Example 9: Publishing Custom Multimodal Events to the Event Broker

```python
"""Illustrative Architecture Example 9: Publishing Custom Events."""

import asyncio
import uuid
from datetime import datetime, timezone
from eon.client import AsyncEonClient
from eon.models.events import EventEnvelope


async def publish_custom_teleoperation_intent() -> None:
    """Publish a strongly-typed intent event to the EON Event Broker."""
    async with AsyncEonClient(base_url="https://edge-robot.local:8443") as client:
        envelope = EventEnvelope(
            specversion="2.0.0",
            id=str(uuid.uuid4()),
            source="hri_operator_console",
            type="eon.interaction.intent.command",
            time=datetime.now(timezone.utc),
            datacontenttype="application/json",
            subject="operator_turn_take",
            data={
                "command": "pause_dialogue",
                "reason": "operator_override",
                "priority": "HIGH",
            },
        )

        ack = await client.events.publish(envelope)
        print(f"Event published successfully. Broker ACK ID: {ack.ack_id}")


if __name__ == "__main__":
    asyncio.run(publish_custom_teleoperation_intent())
```

---

## 7. Architectural Compliance & Traceability

This specification directly satisfies requirements from Phase 0 Product Foundation and Phase 1 Research:

| Requirement ID | Specification Section | Compliance & Verification Mechanism |
| :--- | :--- | :--- |
| `EON-SRS-DEV-001` | Section 2, 4 | Pythonic API with full sync and async typing support. |
| `EON-SRS-PERF-003` | Section 3.1 | Sub-millisecond direct in-process binding mode for robot onboard compute. |
| `EON-SRS-COMM-001` | Section 5, 6.2 | First-class event streaming wrapping `EON-SPEC-ENV-001` envelopes. |
| `EON-SRS-SEC-002` | Section 6.8 | mTLS mutual certificate validation and automated JWT token rotation. |
| `EON-SRS-CTX-001` | Section 5, 6.3 | Type-safe shared context access with privacy-scoped retention filters. |
