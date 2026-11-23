# OVIC EON — Data Domain Model Specification

**Document ID:** `EON-SPEC-DATA-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)
- `docs/architecture/DATA_STORAGE_STRATEGY.md` (`EON-SPEC-DATA-002`)

---

## 1. Executive Summary

This specification defines the ten core data domains of OVIC EON, classifying their persistence tier, data ownership, schema representation, and sensitivity classification.

---

## 2. Ten Data Domains Taxonomy

```text
+=======================================================================================+
| Domain Name            | Persistence Tier | Primary Owner   | Format / Storage Engine |
+=======================================================================================+
| 1. Configuration Data  | Static Disk File | ConfigManager   | YAML / Pydantic v2      |
| 2. Engine Metadata     | In-Memory (RAM)  | EngineRegistry  | Python Objects          |
| 3. Model Metadata      | Static Disk File | ModelRegistry   | YAML (models.yaml)      |
| 4. Event Metadata      | Ephemeral In-Mem | EventBus Router | JSON EventEnvelope      |
| 5. Interaction Context | Ephemeral In-Mem | ContextManager  | RAM Circular Buffer     |
| 6. Session Context     | Session (RAM)    | ContextManager  | RAM State Object        |
| 7. User Preferences    | Persistent Disk  | EMS Engine      | Encrypted SQLite / SQLC |
| 8. Operational Telemetry| Bounded Disk Log| HealthSupervisor| JSON Log Lines          |
| 9. Observability Metric| In-Memory (RAM)  | MetricsCollector| Prometheus Counter Dict |
| 10. Audit Records      | Append-Only Log  | SecurityAuditor | Tamper-Evident Hash Log |
+=======================================================================================+
```
