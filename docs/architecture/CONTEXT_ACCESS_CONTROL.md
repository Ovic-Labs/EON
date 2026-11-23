# OVIC EON — Context Access Control Policy

**Document ID:** `EON-POL-CTX-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.6 — Design Shared Context Management  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/SHARED_CONTEXT_ARCHITECTURE.md` (`EON-ARCH-CTX-001`)
- `docs/architecture/CONTEXT_DATA_MODEL.md` (`EON-SPEC-CTX-001`)

---

## 1. Executive Summary

This specification defines the role-based least-privilege matrix governing which intelligence engines can read, write, update, or purge specific categories of context.

---

## 2. Cross-Engine Context Permissions Matrix

```text
+=======================================================================================+
| Engine | Session Context | Working Memory  | Episodic Memory | User Preferences       |
+=======================================================================================+
| ERS    | Read (Active)   | None            | None            | None                   |
| EMS    | Read / Write    | Read / Write    | Read / Write    | Read / Write (Consent) |
| ERE    | Read            | Read            | Read (History)  | Read                   |
| PSE    | Read            | None            | None            | Read (Style prefs)     |
| SIE    | Read / Write    | Read / Write    | Read            | Read                   |
| ERG    | Read            | Read            | Read (Recent)   | Read                   |
| HBU    | Read (Spatial)  | None            | None            | None                   |
+=======================================================================================+
```

### Access Enforcement Invariants
- **EMS Custodianship:** Only **EMS** has write and purge authority over long-term episodic and preference storage.
- **Perception Engines Isolated:** **ERS** and **HBU** have zero read or write access to historical episodic memory; they operate purely on transient sensory data.
