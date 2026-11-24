# OVIC EON — Cloud Data Storage Specification

**Document ID:** `EON-SPEC-CLD-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cloud Database Architects, Data Engineers  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024  

---

## 1. Cloud Storage Tiering

The optional cloud infrastructure separates data into three specialized storage tiers:

```text
+-------------------------------------------------------------------------+
| Tier 1: Operational Context Store (PostgreSQL with pgvector)            |
| - Stores consented subject preferences, long-term episodic summaries    |
| - Encrypted at rest via AES-256-GCM envelope encryption                |
+-------------------------------------------------------------------------+
| Tier 2: Fleet Time-Series Telemetry Store (TimescaleDB / ClickHouse)    |
| - Stores robot CPU/memory metrics, FPS, error rates, uptime             |
| - Retained for 90 days with automatic rolling aggregation               |
+-------------------------------------------------------------------------+
| Tier 3: Artifact Repository (S3-Compatible Object Storage)              |
| - Stores signed ONNX model weights, firmware images, and delta patches  |
| - Immutability via object versioning and strict checksum verification   |
+-------------------------------------------------------------------------+
```

---

## 2. Backup and Disaster Recovery

- **Automated Snapshots:** Point-In-Time Recovery (PITR) with continuous WAL archiving for operational databases.
- **Cross-Region Replication:** Asynchronous geo-replication for disaster recovery (RPO $\le 5\text{ minutes}$, RTO $\le 30\text{ minutes}$).
- **Data Residency Compliance:** Cloud storage clusters can be pinned to specific geographic jurisdictions (e.g., EU-only for GDPR compliance).
