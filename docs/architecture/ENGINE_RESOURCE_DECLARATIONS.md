# OVIC EON — Engine Resource Declarations Specification

**Document ID:** `EON-SPEC-LIFE-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.4 — Design Engine Lifecycle  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/ENGINE_LIFECYCLE_CONTRACT.md` (`EON-SPEC-LIFE-001`)
- `docs/architecture/ENGINE_BOUNDARY_SPECIFICATIONS.md` (`EON-SPEC-ENG-001`)

---

## 1. Executive Summary

This specification establishes the standardized resource declaration schema and engine-specific resource profiles across CPU threads, heap memory, queue capacity, and optional accelerator needs.

---

## 2. Resource Declaration Schema

```python
class AcceleratorType(str, Enum):
    NONE = "none"
    CPU_SIMD = "cpu_simd"
    NPU_RKNN = "npu_rknn"
    GPU_CUDA = "gpu_cuda"


class EngineResourceDeclarations(EonBaseModel):
    """Resource budget and hardware requirements declared by each engine."""

    engine_id: str
    max_worker_threads: int = Field(default=1, gt=0, le=4)
    max_heap_memory_mb: int = Field(gt=0, le=1024)
    target_frequency_hz: float = Field(gt=0.0)
    queue_capacity: int = Field(default=100, gt=10, le=1000)
    backpressure_policy: BackpressurePolicy = Field(default=BackpressurePolicy.DROP_OLDEST)
    accelerator_preference: AcceleratorType = Field(default=AcceleratorType.CPU_SIMD)
```

---

## 3. Seven-Engine Resource Profiles

```text
+=======================================================================================+
| Engine | Target Freq | Max Threads | Max RAM  | Queue Depth | Backpressure | Accel    |
+=======================================================================================+
| ERS    | 30.0 Hz     | 2 workers   | 65 MB    | 100 items   | DROP_OLDEST  | CPU/NPU  |
| EMS    | 10.0 Hz     | 1 worker    | 45 MB    | 200 items   | WAIT (50ms)  | CPU Only |
| ERE    | Event-driven| 1 worker    | 35 MB    | 100 items   | DROP_OLDEST  | CPU Only |
| PSE    | Event-driven| 1 worker    | 25 MB    | 50 items    | DROP_OLDEST  | CPU Only |
| SIE    | 20.0 Hz     | 1 worker    | 45 MB    | 100 items   | DROP_OLDEST  | CPU Only |
| ERG    | Event-driven| 2 workers   | 120 MB   | 50 items    | REJECT       | CPU/NPU  |
| HBU    | 30.0 Hz     | 2 workers   | 55 MB    | 100 items   | DROP_OLDEST  | CPU/NPU  |
+=======================================================================================+
```

Total combined engine heap budget: **$390\text{ MB}$** (well within the $450\text{ MB}$ operational limit defined in `CONST-PERF-003`).
