# OVIC EON — Data Schema Versioning and Migrations Specification

**Document ID:** `EON-SPEC-DATA-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.8 — Design Data Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/DATA_ARCHITECTURE.md` (`EON-ARCH-DATA-001`)
- `docs/architecture/SCHEMA_VERSIONING_POLICY.md` (`EON-POL-VER-001`)

---

## 1. Executive Summary

This specification establishes the schema versioning rules and migration mechanics governing relational and serialized schemas across platform upgrades.

---

## 2. Versioning and Migration Mechanics

1. **Semantic Versioning:** All schemas declare SemVer `MAJOR.MINOR.PATCH` strings matching rules in `SCHEMA_VERSIONING_POLICY.md`.
2. **Backward Compatibility:** Minor additions (new optional fields) must provide default values (`None` or default factory). Existing consumers ignore unknown fields gracefully.
3. **Database Migrations:** Relational SQLite database schema migrations are managed via declarative version scripts (`src/eon/migrations/`).
4. **Pre-Migration Backup:** Before applying any schema migration, EON creates an atomic file snapshot (`eon_data.db.bak`). If migration fails, the transaction rolls back and restores the backup.
