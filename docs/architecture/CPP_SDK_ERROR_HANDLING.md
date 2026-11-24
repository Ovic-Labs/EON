# OVIC EON — C++ SDK Error Handling Specification

**Document ID:** `EON-SPEC-CPP-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Software Engineers, Robotics Developers  
**Traceability:** `EON-ARCH-CPP-001`, `EON-SPEC-CPP-001`, ADR-020  

---

## 1. Exception Boundaries and Monadic Error Propagation

Robotic control systems and middleware (such as ROS 2 C++ nodes) have strict policies regarding exceptions. Throwing unhandled exceptions across ABI or library boundaries can cause abrupt process termination, violating robot safety standards.

Therefore, the C++ SDK adopts a strict dual-strategy error model:
1. **Public API: Monadic Returns (`eon::Result<T>`):** All public API methods return `eon::Result<T, EonError>`. No public method throws C++ exceptions across the public interface.
2. **Internal Implementation:** Internal logic may utilize RAII and lightweight exceptions (`eon::internal::InternalException`), but every public API wrapper is surrounded by a `try ... catch` barrier translating internal exceptions into structured `EonError` objects.
3. **Flat C-ABI:** Returns integer status codes (`int32_t`) with output error struct pointers.

---

## 2. Error Categorization and Recovery Actions

```cpp
namespace eon {

enum class ErrorSeverity {
    RECOVERABLE,         // Transient failure (e.g., timeout, queue full); caller may retry
    DEGRADED,            // Non-fatal degradation (e.g., engine running in fallback CPU mode)
    FATAL_CONNECTION,    // IPC transport broken; client must reconnect
    FATAL_ENGINE_FAULT   // An EON engine crashed; host should restart or enter safety stop
};

} // namespace eon
```

| Error Code | Severity | Description | Recommended Host Action |
|---|---|---|---|
| `TIMEOUT` | Recoverable | IPC request timed out | Retry with exponential backoff |
| `BUFFER_OVERFLOW` | Recoverable | Ingress/egress queue full | Throttle publisher or change drop policy |
| `NOT_CONNECTED` | Fatal Connection | Client attempted operation without active link | Call `Connect()` |
| `CONNECTION_LOST` | Fatal Connection | IPC pipe closed unexpectedly | Attempt reconnection cycle |
| `ENGINE_FAULTED` | Fatal Engine Fault | Core engine entered `FAULTED` state | Read diagnostic report, alert safety controller |
