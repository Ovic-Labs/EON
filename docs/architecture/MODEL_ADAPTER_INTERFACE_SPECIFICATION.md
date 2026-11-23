# OVIC EON — Model Adapter Interface Specification

**Document ID:** `EON-SPEC-MOD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.7 — Design Model Adapter Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/MODEL_ADAPTER_ARCHITECTURE.md` (`EON-ARCH-MOD-001`)

---

## 1. Executive Summary

This specification formalizes the abstract base classes (ABCs) and typed inference contracts implemented by all local model adapters.

---

## 2. Universal Inference Adapter Interface

```python
class InferenceAdapterInterface(ABC):
    """Abstract interface for local ML inference runtimes."""

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        """Unique adapter identifier."""
        ...

    @property
    @abstractmethod
    def supported_models(self) -> list[str]:
        """List of model identifiers supported by this adapter."""
        ...

    @abstractmethod
    async def load_model(self, model_id: str, config: ModelConfig) -> None:
        """Load model weights and allocate execution session."""
        ...

    @abstractmethod
    async def predict(self, model_id: str, inputs: dict[str, Any]) -> dict[str, Any]:
        """Execute inference synchronously in worker thread; return predictions."""
        ...

    @abstractmethod
    async def unload_model(self, model_id: str) -> None:
        """Free model weights and session memory."""
        ...

    @abstractmethod
    def get_health(self, model_id: str) -> ComponentHealthPayload:
        """Return memory footprint, average latency, and error counts."""
        ...
```

### Deterministic Rule Engine Adapter
For rule-based and template fallbacks, the `DeterministicRuleAdapter` implements `InferenceAdapterInterface`, executing instantaneous ($<5\text{ms}$) algebraic lookups with zero GPU/NPU dependencies.
