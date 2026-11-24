# OVIC EON — Cloud Identity and Access Management Specification

**Document ID:** `EON-SPEC-CLD-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.15)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Cloud Security Engineers, IAM Administrators  
**Traceability:** `EON-ARCH-CLD-001`, ADR-024, ADR-025  

---

## 1. Robot and Operator Authentication

Cloud access relies on two distinct authentication paths:
1. **Device Identity (Robots):**
   - Each robot provisioned with an X.509 client certificate stored in local hardware security (TPM 2.0 or secure element).
   - Certificates are issued by the OVIC Root CA or enterprise customer CA.
   - mTLS handshake authenticates the robot's hardware identity and tenant affiliation on every connection.
2. **Operator Identity (Humans / Admins):**
   - OAuth 2.0 and OpenID Connect (OIDC) integration (Okta, Microsoft Entra ID, Auth0).
   - Multi-Factor Authentication (MFA) mandatory for fleet administration consoles.

---

## 2. Role-Based Access Control (RBAC) Matrix

| Role | Scope | Permissions |
|---|---|---|
| **Fleet Administrator** | Tenant-wide | Register robots, trigger OTA firmware updates, view health telemetry |
| **Robotics Support Engineer** | Assigned robots | View diagnostics, inspect error logs, query operational states |
| **Robot Device Identity** | Self (single robot) | Submit sync events, query OTA manifest, publish heartbeat |
| **Audit Officer** | Tenant-wide | Read-only access to tamper-evident audit logs and consent registers |
