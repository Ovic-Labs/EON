# OVIC EON — EON Core Initialization Sequence

**Document ID:** `EON-ARCH-CORE-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.3 — Design EON Core  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/EON_CORE_ARCHITECTURE.md` (`EON-ARCH-CORE-004`)
- `docs/architecture/EON_CORE_COMPONENTS.md` (`EON-ARCH-CORE-005`)
- `docs/architecture/EON_CORE_STATE_MODEL.md` (`EON-ARCH-CORE-007`)

---

## 1. Executive Summary

This document defines the deterministic 12-step initialization sequence executed by **EON Core** during system bootstrap. Every step has defined preconditions, actions, postconditions, and deterministic failure outcomes.

---

## 2. The 12-Step Initialization Sequence

```text
Step 1: Configuration Loading
   │  (Parse YAML, validate schemas, substitute environment variables)
   ▼
Step 2: Environment Validation
   │  (Check OS, Python version >=3.10, memory availability >=500MB)
   ▼
Step 3: Security & Key Initialization
   │  (Initialize CryptoShredder, verify key store permissions)
   ▼
Step 4: Dependency Discovery & Graph Construction
   │  (Inspect engine declarations, build dependency graph)
   ▼
Step 5: Core Component Registration
   │  (Register EventBus, HealthManager, ConfigurationManager)
   ▼
Step 6: Engine Discovery & Registration
   │  (Instantiate and register the seven engines)
   ▼
Step 7: Interface Validation & Contract Verification
   │  (Verify engines implement EonEngineInterface, validate versioning)
   ▼
Step 8: Context Service Initialization
   │  (Initialize SessionContextManager, verify storage SPI)
   ▼
Step 9: Event Infrastructure Initialization
   │  (Start EventBus router, allocate bounded subscriber priority queues)
   ▼
Step 10: Model Adapter Registration & Hardware Discovery
   │  (Detect CPU SIMD / NPU, register ONNX, llama.cpp, Piper adapters)
   ▼
Step 11: Subsystem Health & Diagnostics Check
   │  (Execute pre-flight ping across all engines and adapters)
   ▼
Step 12: Readiness Declaration
   │  (Transition system state to READY, emit SystemReadyEvent)
   ▼
[ READY FOR INGESTION & INTERACTION ]
```

---

## 3. Detailed Step Specifications

| Step | Phase Name | Execution Responsibility | Failure Action |
|---|---|---|---|
| **1** | Configuration Loading | `ConfigurationManager` | Fatal: Abort startup, return exit code 1 |
| **2** | Environment Validation | `CoreApplicationManager` | Fatal: Abort if Python < 3.10 or RAM < 500MB |
| **3** | Security Initialization | `CryptoKeyManager` | Fatal: Abort if key permissions are insecure |
| **4** | Dependency Discovery | `DependencyResolver` | Fatal: Abort if circular dependency detected |
| **5** | Component Registration | `ComponentRegistry` | Fatal: Abort if singleton collision occurs |
| **6** | Engine Registration | `EngineRegistry` | Warning: Missing optional engines marked absent |
| **7** | Interface Validation | `PolicyEnforcer` | Fatal: Reject engine if interface non-compliant |
| **8** | Context Initialization | `SessionContextManager` | Fallback: Degrade to RAM-only ephemeral mode |
| **9** | Event Bus Initialization | `EventBus` | Fatal: Abort if queue allocation fails |
| **10**| Model Adapter Register | `ModelAdapterRegistry` | Fallback: Select CPU deterministic templates |
| **11**| Pre-Flight Health Check | `HealthManager` | Degraded: If non-critical engine fails ping |
| **12**| Readiness Declaration | `CoreApplicationManager` | State transitions to `CoreState.READY` |

---

## 4. Failure and Rollback Policy During Startup

If a **Fatal Step** fails:
1. System state immediately transitions to `CoreState.FAILED`.
2. Any partially initialized engines receive `stop(timeout=1.0)`.
3. Event bus queues are closed and drained.
4. A structured JSON failure report is emitted to `stderr`.
5. Process terminates with a non-zero exit code.
