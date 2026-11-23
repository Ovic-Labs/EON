# OVIC EON — API Versioning and Compatibility Specification

**Document ID:** `EON-SPEC-API-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.9 — Design API Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/API_ARCHITECTURE.md` (`EON-ARCH-API-001`)
- `docs/architecture/SCHEMA_VERSIONING_POLICY.md` (`EON-POL-VER-001`)

---

## 1. Executive Summary

This specification defines the URL path versioning, backward compatibility guarantees, and deprecation lifecycle for EON network APIs.

---

## 2. API Versioning Principles

1. **Path-Based Versioning:** All public endpoints carry a major version prefix in their route (`/api/v1/`).
2. **OpenAPI Specification:** FastAPI generates an interactive OpenAPI 3.1 specification at `/api/v1/openapi.json`.
3. **Deprecation Policy:** Deprecated endpoints are annotated with `deprecated: true` in OpenAPI and return a `Deprecation: @<timestamp>` HTTP header for a minimum of 6 months before removal in a subsequent major version.
