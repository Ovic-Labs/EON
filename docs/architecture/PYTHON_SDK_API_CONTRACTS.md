# EON Python SDK API Contracts Specification

**Document ID:** `EON-SPEC-SDK-002`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `TECHNICAL SPECIFICATION`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/PYTHON_SDK_ARCHITECTURE.md` (`EON-ARCH-SDK-001`)  
**Cross-References:**  
- `docs/architecture/PYTHON_SDK_PACKAGE_STRUCTURE.md` (`EON-SPEC-SDK-001`)  
- `docs/architecture/API_ENDPOINT_CATALOG.md` (`EON-SPEC-API-001`)  
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)  
- `docs/architecture/EVENT_ENVELOPE_SPECIFICATION.md` (`EON-SPEC-ENV-001`)  
- `docs/architecture/CONTEXT_DATA_MODEL.md` (`EON-SPEC-CTX-001`)  

---

## 1. Scope & Purpose

This document provides formal, fully-typed Python interface contracts for the primary client classes in the EON Python SDK. Every public class, method, argument, return type, and raised exception is specified in compliance with PEP 484, PEP 526, and PEP 561 to ensure static type-checking passes under `mypy --strict`.

---

## 2. Top-Level Client Contracts

### 2.1 `AsyncEonClient` (Primary Asynchronous Interface)

```python
from __future__ import annotations

from types import TracebackType
from typing import Optional, Type
from eon.clients.auth import AsyncAuthClient
from eon.clients.context import AsyncContextClient
from eon.clients.engines import AsyncEngineClient
from eon.clients.events import AsyncEventClient
from eon.clients.health import AsyncHealthClient
from eon.clients.models import AsyncModelClient
from eon.config import ClientConfig, EonConfig
from eon.exceptions import EonConnectionError, EonTimeoutError
from eon.transports.base import BaseTransport


class AsyncEonClient:
    """Primary asynchronous client for interacting with OVIC EON infrastructure."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        config: Optional[ClientConfig] = None,
        transport: Optional[BaseTransport] = None,
    ) -> None:
        """Initialize an AsyncEonClient instance.

        Args:
            base_url: Base HTTP or Gateway URL of the EON service.
            api_key: Optional static API key for authentication.
            bearer_token: Optional JWT Bearer token.
            config: Full client configuration overrides.
            transport: Optional custom transport adapter.
        """
        ...

    @classmethod
    def from_config(cls, config: EonConfig) -> AsyncEonClient:
        """Factory constructor instantiating client from declarative EonConfig."""
        ...

    @property
    def is_connected(self) -> bool:
        """Return True if active transport connection is open and healthy."""
        ...

    @property
    def is_local(self) -> bool:
        """Return True if operating in direct in-process local binding mode."""
        ...

    @property
    def engines(self) -> AsyncEngineClient:
        """Subsystem client for managing intelligence engine lifecycles."""
        ...

    @property
    def events(self) -> AsyncEventClient:
        """Subsystem client for publishing, subscribing, and streaming events."""
        ...

    @property
    def context(self) -> AsyncContextClient:
        """Subsystem client for reading and updating shared contextual state."""
        ...

    @property
    def models(self) -> AsyncModelClient:
        """Subsystem client for inspecting neural models and hardware adapters."""
        ...

    @property
    def health(self) -> AsyncHealthClient:
        """Subsystem client for health, telemetry, and system diagnostics."""
        ...

    @property
    def auth(self) -> AsyncAuthClient:
        """Subsystem client for authentication and session credential management."""
        ...

    async def connect(self) -> None:
        """Explicitly establish underlying transport connections and verify handshake.

        Raises:
            EonConnectionError: If transport fails to connect or handshake fails.
            EonTimeoutError: If connection establishment exceeds configured timeout.
        """
        ...

    async def close(self) -> None:
        """Gracefully terminate transport connections, drain queues, and release sockets."""
        ...

    async def __aenter__(self) -> AsyncEonClient:
        """Asynchronous context manager entry."""
        ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Asynchronous context manager exit ensuring graceful teardown."""
        ...
```

### 2.2 `EonClient` (Ergonomic Synchronous Interface)

```python
from __future__ import annotations

from types import TracebackType
from typing import Optional, Type
from eon.clients.auth import AuthClient
from eon.clients.context import ContextClient
from eon.clients.engines import EngineClient
from eon.clients.events import EventClient
from eon.clients.health import HealthClient
from eon.clients.models import ModelClient
from eon.config import ClientConfig, EonConfig


class EonClient:
    """Ergonomic synchronous wrapper client for scripts, notebooks, and tools."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        *,
        api_key: Optional[str] = None,
        bearer_token: Optional[str] = None,
        config: Optional[ClientConfig] = None,
    ) -> None: ...

    @classmethod
    def from_config(cls, config: EonConfig) -> EonClient: ...

    @property
    def is_connected(self) -> bool: ...

    @property
    def is_local(self) -> bool: ...

    @property
    def engines(self) -> EngineClient: ...

    @property
    def events(self) -> EventClient: ...

    @property
    def context(self) -> ContextClient: ...

    @property
    def models(self) -> ModelClient: ...

    @property
    def health(self) -> HealthClient: ...

    @property
    def auth(self) -> AuthClient: ...

    def connect(self) -> None: ...

    def close(self) -> None: ...

    def __enter__(self) -> EonClient: ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None: ...
```

---

## 3. Subsystem Client Contracts

### 3.1 `AsyncEngineClient` (Engine Lifecycle Management)

```python
from __future__ import annotations

from typing import List, Optional
from eon.exceptions import (
    EonEngineError,
    EonEngineStateError,
    EonNotFoundError,
    EonTimeoutError,
)
from eon.models.lifecycle import EngineInfo, EngineState, TransitionResult


class AsyncEngineClient:
    """Manages intelligence engine lifecycles, states, and recovery policies."""

    async def list_engines(self) -> List[EngineInfo]:
        """Retrieve operational metadata and states for all registered engines."""
        ...

    async def get_state(self, engine_id: str) -> EngineState:
        """Get the current operational lifecycle state of an engine.

        Raises:
            EonNotFoundError: If engine_id is not registered.
        """
        ...

    async def start(self, engine_id: str, *, timeout_s: float = 15.0) -> TransitionResult:
        """Trigger engine transition to ACTIVE state.

        Raises:
            EonEngineStateError: If current state cannot transition to ACTIVE.
            EonTimeoutError: If initialization exceeds timeout_s.
            EonEngineError: If engine initialization faults.
        """
        ...

    async def stop(self, engine_id: str, *, timeout_s: float = 10.0) -> TransitionResult:
        """Trigger engine transition to STOPPED state."""
        ...

    async def pause(self, engine_id: str, *, timeout_s: float = 5.0) -> TransitionResult:
        """Trigger engine transition to PAUSED state."""
        ...

    async def resume(self, engine_id: str, *, timeout_s: float = 5.0) -> TransitionResult:
        """Resume paused engine back to ACTIVE state."""
        ...

    async def recover(self, engine_id: str, *, timeout_s: float = 20.0) -> TransitionResult:
        """Execute automated recovery workflow on a DEGRADED or FAULTED engine."""
        ...
```

### 3.2 `AsyncEventClient` (Event-Driven Communication)

```python
from __future__ import annotations

from typing import AsyncIterator, List, Optional
from eon.exceptions import EonEventError, EonSerializationError
from eon.models.events import EventAck, EventEnvelope, EventFilter


class AsyncEventSubscription:
    """Active streaming event subscription."""

    def __aiter__(self) -> AsyncIterator[EventEnvelope]:
        """Asynchronous iterator yielding incoming event envelopes."""
        ...

    async def unsubscribe(self) -> None:
        """Cancel subscription and release broker resources."""
        ...


class AsyncEventClient:
    """Interface for publishing events and subscribing to topics."""

    async def publish(
        self,
        event: EventEnvelope,
        *,
        timeout_s: float = 5.0,
        wait_for_ack: bool = True,
    ) -> EventAck:
        """Publish a strongly-typed event envelope to the event broker.

        Raises:
            EonSerializationError: If envelope cannot be serialized.
            EonEventError: If broker rejects the event.
            EonTimeoutError: If broker acknowledgment exceeds timeout.
        """
        ...

    async def subscribe(
        self,
        topics: List[str],
        *,
        client_id: Optional[str] = None,
        filter_criteria: Optional[EventFilter] = None,
        buffer_size: int = 1000,
    ) -> AsyncEventSubscription:
        """Subscribe to event topics with optional metadata filtering.

        Raises:
            EonEventError: If topic syntax is invalid or authorization fails.
        """
        ...
```

### 3.3 `AsyncContextClient` (Shared Context Management)

```python
from __future__ import annotations

from typing import Any, Dict, Optional
from eon.exceptions import EonAccessDeniedError, EonContextConflictError
from eon.models.context import EngagementState, UserProfileContext


class AsyncContextClient:
    """Interface for querying and updating shared interaction and user context."""

    async def get_user_profile(
        self, subject_id: str, *, scope: str = "default"
    ) -> UserProfileContext:
        """Fetch privacy-filtered user profile context.

        Raises:
            EonAccessDeniedError: If caller lacks permission for requested scope.
            EonNotFoundError: If subject_id does not exist.
        """
        ...

    async def update_engagement(
        self,
        subject_id: str,
        engagement: EngagementState,
        *,
        expected_version: Optional[int] = None,
    ) -> None:
        """Update user engagement state using optimistic concurrency control.

        Raises:
            EonContextConflictError: If expected_version does not match current version.
            EonAccessDeniedError: If caller lacks write authority on context domain.
        """
        ...

    async def get_working_memory(self, session_id: str) -> Dict[str, Any]:
        """Fetch active session working memory state."""
        ...
```

### 3.4 `AsyncModelClient` (Model Adapter Inspection)

```python
from __future__ import annotations

from typing import List
from eon.models.models import HardwareProfile, ModelInspectionReport


class AsyncModelClient:
    """Inspects registered neural model adapters, runtimes, and hardware metrics."""

    async def list_active_models(self) -> List[ModelInspectionReport]:
        """Return active model adapters, operational status, and latency stats."""
        ...

    async def get_hardware_profile(self) -> HardwareProfile:
        """Inspect host hardware accelerators (CPU, GPU, NPU) and memory state."""
        ...

    async def trigger_warmup(self, model_id: str) -> bool:
        """Execute non-blocking warm-up inference run for a registered adapter."""
        ...
```

### 3.5 `AsyncHealthClient` (System Diagnostics & Telemetry)

```python
from __future__ import annotations

from eon.models.health import SystemHealthResponse


class AsyncHealthClient:
    """Telemetry, liveness, and system health status inspection."""

    async def get_status(self) -> SystemHealthResponse:
        """Retrieve aggregated system health, uptime, and engine state summary."""
        ...

    async def check_liveness(self) -> bool:
        """Simple boolean probe checking if gateway/kernel is responding."""
        ...

    async def check_readiness(self) -> bool:
        """Probe verifying all mandatory engines are initialized and ready."""
        ...
```
