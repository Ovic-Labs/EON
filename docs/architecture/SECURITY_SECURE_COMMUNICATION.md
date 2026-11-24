# OVIC EON — Security Secure Communication Specification

**Document ID:** `EON-SPEC-SEC-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Network Engineers, Security Architects  
**Traceability:** `EON-ARCH-SEC-001`, ADR-025  

---

## 1. Transport Encryption Standards

All data in transit across system boundaries is encrypted using modern cryptographic standards:

1. **Local IPC (Inter-Process Communication):**
   - Unix Domain Sockets: Memory-isolated within the Linux kernel virtual memory subsystem.
   - SCM_RIGHTS / Anonymous Shared Memory: Segments mapped directly into authorized process address spaces; never exposed on network interfaces.
2. **ROS 2 Middleware Transport:**
   - SROS 2 (Secure ROS 2) extensions using DDS Security.
   - Symmetric AES-256-GCM data submessage encryption for observation topics.
3. **Optional Cloud & Remote Robot Telemetry:**
   - Transport Layer Security (TLS) version 1.3 exclusively.
   - Cipher Suites: `TLS_AES_256_GCM_SHA384` and `TLS_CHACHA20_POLY1305_SHA256`.
   - Legacy TLS versions (1.0, 1.1, 1.2) strictly disabled.
