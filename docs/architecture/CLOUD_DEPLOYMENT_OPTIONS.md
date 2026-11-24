# OVIC EON — Cloud Deployment Options Specification

**Document ID:** `EON-SPEC-CLD-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Solutions Architects, Enterprise IT Infrastructure Teams  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024  

---

## 1. Deployment Models

To satisfy diverse enterprise security, healthcare compliance, and operational governance requirements, the optional cloud backend supports three deployment models:

1. **Multi-Tenant Public Cloud SaaS (OVIC Hosted):**
   - Fully managed by OVIC Labs on AWS / GCP / Azure.
   - Fast onboarding, automated rolling updates, and managed backups.
2. **Dedicated Private Cloud VPC:**
   - Single-tenant deployment inside the customer's cloud virtual private cloud (VPC).
   - Customer maintains complete ownership of VPC peering, KMS encryption keys, and network egress rules.
3. **On-Premises Hybrid Appliance:**
   - Deployed on local Kubernetes clusters (OpenShift, Rancher, microk8s) within hospital or enterprise server rooms.
   - Completely air-gapped from the public internet; robots sync locally over the private enterprise intranet.
