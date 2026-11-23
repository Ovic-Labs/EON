# OVIC EON — Engine Lifecycle Contract Specification

**Document ID:** `EON-SPEC-LIFE-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/ENGINE_LIFECYCLE_ARCHITECTURE.md` (`EON-ARCH-LIFE-001`)
- `docs/architecture/ENGINE_STATE_TRANSITIONS.md` (`EON-ARCH-LIFE-002`)

---

## 1. Executive Summary

This specification formalizes the unified Service Provider Interface (SPI) and metadata declarations that all seven EON intelligence engines must implement.

---

## 2. Standard Lifecycle Operations

Every engine implements the following standard programmatic operations:

| Operation | Purpose | Inputs | Precondition | Postcondition | Timeout |
|---|---|---|---|---|---|
| `register()` | Register metadata with Engine Registry | Engine metadata | None | Engine in `REGISTERED` | < 100 ms |
| `validate()` | Verify config, schemas, dependencies | Engine config | `REGISTERED` | Engine in `VALIDATING` -> `INITIALIZING` | < 500 ms |
| `initialize()` | Allocate internal queues, compile rules | Core services, EventBus | `INITIALIZING` | Engine in `INITIALIZED` | < 2000 ms |
| `start()` | Launch worker tasks, subscribe to bus | None | `INITIALIZED` | Engine in `RUNNING` | < 1000 ms |
| `pause()` | Temporarily suspend queue processing | None | `RUNNING` | Engine in `PAUSED` | < 200 ms |
| `resume()` | Resume event processing from pause | None | `PAUSED` | Engine in `RUNNING` | < 200 ms |
| `health_check()`| Probe component health & error rates | None | Any operational | Returns `ComponentHealthPayload` | < 50 ms |
| `reconfigure()` | Apply hot-reloaded configuration | New config dict | `RUNNING`/`PAUSED` | Config updated or rejected | < 500 ms |
| `stop()` | Drain queues, cancel background tasks | Timeout seconds | Operational | Engine in `STOPPED` | < 5000 ms |
| `recover()` | Attempt reset from degraded state | Recovery context | `DEGRADED`/`FAILED` | Engine in `RUNNING` or `FAILED` | < 3000 ms |

---

## 3. Formal Engine Lifecycle Contract (Python Interface)

```python
class EonEngineContract(ABC):
    """Universal lifecycle and capability contract for all seven engines."""

    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Official engine identifier: ERS, EMS, ERE, PSE, SIE, ERG, or HBU."""
        ...

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Descriptive engine name."""
        ...

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version string (e.g. '0.1.0')."""
        ...

    @property
    @abstractmethod
    def contract_version(self) -> str:
        """Lifecycle contract version (e.g. '1.0.0')."""
        ...

    @abstractmethod
    def get_resource_declarations(self) -> EngineResourceDeclarations:
        """Declare thread limits, memory budgets, and optional accelerator needs."""
        ...

    @abstractmethod
    def get_dependency_declarations(self) -> list[str]:
        """Declare upstream event topics or engines required for startup."""
        ...

    @abstractmethod
    async def validate(self, config: dict[str, Any]) -> ValidationReport:
        """Validate configuration parameters prior to resource allocation."""
        ...

    @abstractmethod
    async def initialize(
        self, config: dict[str, Any], event_bus: Any, context_provider: Any
    ) -> None:
        """Allocate queues, register event subscriptions, and prepare models."""
        ...

    @abstractmethod
    async def start(self) -> None:
        """Activate event consumption workers and transition to RUNNING."""
        ...

    @abstractmethod
    async def pause(self) -> None:
        """Pause worker tasks without discarding queue items."""
        ...

    @abstractmethod
    async def resume(self) -> None:
        """Resume processing of paused worker tasks."""
        ...

    @abstractmethod
    async def stop(self, timeout_seconds: float) -> None:
        """Drain queues, cancel tasks, and transition to STOPPED."""
        ...

    @abstractmethod
    async def health_check(self) -> ComponentHealthPayload:
        """Return real-time health metrics, memory usage, and error counters."""
        ...

    @abstractmethod
    async def recover(self, reason: str) -> bool:
        """Attempt self-healing recovery after a failure or degradation."""
        ...
```
