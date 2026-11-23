# OVIC EON — Context Lifecycle Specification

**Document ID:** `EON-SPEC-CTX-002`  
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

This specification establishes the end-to-end lifecycle stages governing context records: Creation, Validation, Normalization, Retrieval, Update, Expiration, Deletion, and Version Migration.

---

## 2. Context Lifecycle Sequence

```text
[ Creation ]
     │  Validate schemas and access permissions
     ▼
[ Normalization ]
     │  Clamp numerical bounds, UTC timestamp alignment
     ▼
[ Active Storage ]
     ├─► Volatile Working Memory (RAM) ──(Session End)──► [ Expired / Purged ]
     │
     └─► Encrypted Persistent Store ──(TTL / Request)─► [ Cryptographic Shredding ]
```

### Lifecycle Stage Rules
1. **Creation & Validation:** Incoming context updates are validated against Pydantic models. Unrecognized fields are strictly rejected (`extra="forbid"`).
2. **TTL Expiration:** Episodic interaction records expire automatically after 30 days unless explicitly renewed.
3. **Session Purge:** When SIE transitions to `DISENGAGED` or `FAREWELL`, all volatile working memory buffers are wiped from RAM.
4. **Deletion Workflows:** User deletion requests initiate hard row removal and user key destruction within $<500\text{ ms}$.
