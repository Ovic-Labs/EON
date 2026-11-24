# OVIC EON — Cloud Cost and Scalability Model Specification

**Document ID:** `EON-SPEC-CLD-008`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cloud Architects, Financial Operations (FinOps), Product Managers  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024  

---

## 1. Scalability Dimensions and Edge-Driven Cost Efficiency

Traditional cloud-dependent AI robotics architectures require continuous streaming of high-resolution video and audio to cloud GPUs, resulting in prohibitive cloud compute and egress costs ($>\$500\text{/robot/month}$).

Because EON performs **100% of perception and model inference locally on edge CPUs**:
- **Bandwidth Consumption:** Only high-level event summaries and aggregated telemetry are synchronized ($\le 5\text{ MB/robot/day}$).
- **Cloud Compute Overhead:** Cloud instances perform lightweight JSON/Protobuf routing and PostgreSQL transactions, requiring zero cloud GPUs.

```text
+-------------------------------------------------------------------------+
|                  Cost Modeling (Analytical Estimates)                   |
|                                                                         |
|  - Telemetry Volume per Robot: ~5 MB / day                              |
|  - Ingestion API Requests: ~10 requests / hour / robot                  |
|  - Est. Cloud Infrastructure Cost: ~$1.20 - $2.50 / robot / month       |
|  - Cloud GPU Requirement: ZERO ($0.00)                                  |
+-------------------------------------------------------------------------+
```

---

## 2. Horizontal Scaling Architecture

- **Stateless Gateway Tier:** Envoy and API Gateway instances scale horizontally behind an AWS ALB or Google Cloud HTTPS Load Balancer.
- **Database Partitioning:** PostgreSQL telemetry tables partitioned by `tenant_id` and date range (`timescaledb` hypertable).
