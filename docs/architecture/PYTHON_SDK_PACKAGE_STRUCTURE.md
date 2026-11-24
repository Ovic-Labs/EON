# EON Python SDK Package Structure Specification

**Document ID:** `EON-SPEC-SDK-001`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `TECHNICAL SPECIFICATION`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/PYTHON_SDK_ARCHITECTURE.md` (`EON-ARCH-SDK-001`)  
**Cross-References:**  
- `docs/architecture/SYSTEM_LAYERED_ARCHITECTURE.md` (`EON-ARCH-001`)  
- `docs/architecture/API_ARCHITECTURE.md` (`EON-ARCH-API-001`)  

---

## 1. Scope & Objective

This document defines the physical and logical package structure for the EON Python SDK within the `src/eon/` directory hierarchy. It establishes module boundaries, public export conventions (`__all__`), internal versus external API surfaces, and dependency groupings to guarantee a lean runtime footprint on robotic edge devices while providing extensible capabilities for remote and distributed environments.

---

## 2. Directory Hierarchy & Codebase Mapping

The SDK implementation resides under `src/eon/`, organized into cohesive, modular packages:

```text
src/eon/
├── __init__.py                     # Root package marker and high-level public exports
├── py.typed                        # PEP 561 marker indicating inline type annotations
├── client.py                       # High-level EonClient (sync) and AsyncEonClient (async)
├── config.py                       # Configuration models, environment loaders, client options
├── exceptions.py                   # Complete EON SDK exception hierarchy
├── _internal/                      # Private internal utilities (NOT part of public API)
│   ├── __init__.py
│   ├── logging.py                  # Structured client logging and tracing helpers
│   ├── retry.py                    # Backoff, jitter, and retry strategy logic
│   ├── validation.py               # Runtime type and argument validators
│   └── version.py                  # Dynamic version resolution and build metadata
├── transports/                     # Transport abstraction layer
│   ├── __init__.py
│   ├── base.py                     # Abstract BaseTransport interface
│   ├── in_process.py               # Direct in-memory binding transport (Local mode)
│   ├── http.py                     # HTTP/REST transport using httpx (Remote mode)
│   ├── websocket.py                # WebSocket bidirectional streaming transport
│   └── grpc.py                     # Optional gRPC transport (when [grpc] extra is active)
├── clients/                        # Domain-specific client subsystems
│   ├── __init__.py
│   ├── base.py                     # BaseSubsystemClient protocol
│   ├── engines.py                  # EngineClient & AsyncEngineClient (lifecycle & control)
│   ├── events.py                   # EventClient & AsyncEventClient (pub/sub & streaming)
│   ├── context.py                  # ContextClient & AsyncContextClient (shared context)
│   ├── models.py                   # ModelClient & AsyncModelClient (model adapter inspection)
│   ├── health.py                   # HealthClient & AsyncHealthClient (telemetry & status)
│   └── auth.py                     # AuthClient & AsyncAuthClient (tokens & session claims)
├── models/                         # Strongly-typed domain and transfer models (Pydantic / dataclasses)
│   ├── __init__.py
│   ├── common.py                   # UUID, Timestamp, Confidence, Epistemology models
│   ├── events.py                   # EventEnvelope, CloudEvents v1.0.2 serialization models
│   ├── lifecycle.py                # EngineState, TransitionCommand, HealthReport
│   ├── context.py                  # UserProfile, InteractionTurn, EngagementState
│   ├── models.py                   # ModelMetadata, LatencyMetrics, HardwareProfile
│   └── health.py                   # SystemHealthResponse, SubsystemStatus
└── security/                       # Security, authentication, and credentials management
    ├── __init__.py
    ├── credentials.py              # APIKeyCredential, BearerTokenCredential, CertificateCredential
    ├── tokens.py                   # JWT decoding, expiry checking, automated renewal
    └── tls.py                      # SSLContext factory, mTLS certificate validation
```

---

## 3. Module Boundaries & Public Exports (`__all__`)

To maintain clean separation between the public API surface and internal implementation details, all public modules explicitly declare `__all__`.

### 3.1 Root Package (`src/eon/__init__.py`)

The root module exports only top-level clients, standard configurations, and primary exceptions:

```python
"""EON: Emotional Intelligence Infrastructure for Robotics."""

from eon.client import AsyncEonClient, EonClient
from eon.config import ClientConfig, EonConfig
from eon.exceptions import (
    EonAuthenticationError,
    EonConnectionError,
    EonError,
    EonRateLimitError,
    EonTimeoutError,
)

__version__ = "0.1.0"

__all__ = [
    "AsyncEonClient",
    "ClientConfig",
    "EonAuthenticationError",
    "EonClient",
    "EonConnectionError",
    "EonError",
    "EonRateLimitError",
    "EonTimeoutError",
    "EonConfig",
    "__version__",
]
```

### 3.2 Models Package (`src/eon/models/__init__.py`)

Domain models are grouped logically and re-exported from `eon.models`:

```python
"""EON Strongly-Typed Domain Models."""

from eon.models.context import EngagementState, UserProfileContext
from eon.models.events import EventEnvelope, PerceptionFaceDetectedPayload
from eon.models.health import SubsystemStatus, SystemHealthResponse
from eon.models.lifecycle import EngineState, TransitionResult
from eon.models.models import HardwareProfile, ModelInspectionReport

__all__ = [
    "EngagementState",
    "EngineState",
    "EventEnvelope",
    "HardwareProfile",
    "ModelInspectionReport",
    "PerceptionFaceDetectedPayload",
    "SubsystemStatus",
    "SystemHealthResponse",
    "TransitionResult",
    "UserProfileContext",
]
```

### 3.3 Private Internal Boundary (`src/eon/_internal/`)

All code within `src/eon/_internal/` is strictly private:
- External callers must never import from `eon._internal`.
- SemVer stability guarantees do not apply to `_internal` modules.
- Linter checks and static analysis enforce that public modules do not re-export `_internal` symbols.

---

## 4. Dependency Footprint & Optional Extras

To ensure minimal overhead on embedded compute boards (e.g., NVIDIA Jetson, Raspberry Pi 5), the SDK divides dependencies into a minimal core and optional feature extras.

### 4.1 Dependency Strategy Matrix

| Tier | Group Name | Included Packages | Target Environment | Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Core** | `default` | `httpx>=0.25.0`, `pydantic>=2.4.0`, `typing-extensions>=4.8.0` | All environments (Client & Edge) | $< 15\text{ MB}$ |
| **Local** | `[local]` | `psutil>=5.9.0`, `pyyaml>=6.0.1` | Robot Onboard Direct Binding | $+ 5\text{ MB}$ |
| **Remote** | `[remote]` | `websockets>=12.0`, `aiohttp>=3.9.0` | WebSocket Streaming / Teleop | $+ 8\text{ MB}$ |
| **gRPC** | `[grpc]` | `grpcio>=1.59.0`, `protobuf>=4.24.0` | High-throughput binary RPC | $+ 30\text{ MB}$ |
| **ROS 2** | `[ros2]` | `rclpy` (system bridge / stubs) | ROS 2 Humble / Jazzy integration | Zero pip add |
| **Dev** | `[dev]` | `pytest`, `pytest-asyncio`, `ruff`, `mypy`, `build` | Developer workstations & CI | Dev only |

### 4.2 Declarative `pyproject.toml` Architecture Specification

```toml
[project]
name = "eon-sdk"
version = "0.1.0"
description = "Official Python SDK for OVIC EON Emotional Intelligence Infrastructure"
readme = "README.md"
requires-python = ">=3.10"
license = { text = "Apache-2.0" }
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.4.0",
    "typing-extensions>=4.8.0",
]

[project.optional-dependencies]
local = [
    "psutil>=5.9.0",
    "pyyaml>=6.0.1",
]
remote = [
    "websockets>=12.0",
    "aiohttp>=3.9.0",
]
grpc = [
    "grpcio>=1.59.0",
    "protobuf>=4.24.0",
]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
    "mypy>=1.6.0",
    "build>=1.0.0",
]
```

---

## 5. Architectural Separation: SDK vs. Intelligence Engine Runtimes

A critical architectural invariant established in Phase 2 is the strict boundary between the **SDK Client Library** and the **Engine Runtimes**:

1. **SDK Scope (`src/eon/`):** Contains transport drivers, communication protocols, request/response builders, serialization serializers, and typed client interfaces.
2. **Engine Runtimes Scope (Deferred to Future Implementation Phases):** The actual heavy neural network models, inference execution pipelines, face-tracking algorithms, and audio DSP routines do NOT reside inside the base SDK.
3. **Decoupled Packaging:** Future intelligence engine packages (e.g., `eon-engine-perception`, `eon-engine-speech`) will depend on `eon-sdk` as their client/communication contract layer, preventing monolithic dependency bloat.
