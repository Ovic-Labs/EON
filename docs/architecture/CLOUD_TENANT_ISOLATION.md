# OVIC EON — Cloud Tenant Isolation Specification

**Document ID:** `EON-SPEC-CLD-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Architects, Cloud Data Engineers  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024, ADR-025  

---

## 1. Multi-Tenant Isolation Strategy

In enterprise SaaS and multi-facility robotics deployments, strict data isolation between corporate tenants is mandatory:

```text
+-------------------------------------------------------------------------+
|                       Tenant Isolation Architecture                     |
+-------------------------------------------------------------------------+
| Tier 1: Logical Isolation (Shared Database, Separate Schemas)           |
| - PostgreSQL schema per tenant (`tenant_hospital_a`, `tenant_care_b`)   |
| - Row-Level Security (RLS) policies enforcing `tenant_id = current_user`|
+-------------------------------------------------------------------------+
| Tier 2: Physical Isolation (Dedicated Database per Tenant)             |
| - For high-compliance healthcare customers                              |
| - Separate database instances, separate KMS encryption keys            |
+-------------------------------------------------------------------------+
```

---

## 2. Cross-Tenant Leakage Prevention

1. **Cryptographic Key Separation:** Each tenant possesses a distinct Customer Master Key (CMK) managed in AWS KMS, Azure Key Vault, or HashiCorp Vault.
2. **Context Token Validation:** Every edge-to-cloud request carries a signed tenant claim. The API gateway rejects any request attempting to query or modify data belonging to an external `tenant_id`.
