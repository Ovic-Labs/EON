# OVIC EON — Architecture Resilience Model Specification

**Document ID:** `EON-REV-RES-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Reliability Engineers, Site Reliability Engineers, Robotics Architects  
**Traceability:** `EON-ARCH-CORE-001`, ADR-028  

---

## 1. Resilience Architecture Framework

The EON Resilience Model formalizes the layered defensive mechanisms ensuring continuous, safe operation across degraded operational states:

```text
+-------------------------------------------------------------------------+
|                  Layer 1: Prevention & Bounded Resources                |
|  - Bounded ring buffers with DROP_OLDEST drop policy                    |
|  - Cgroups v2 memory.max and CPU quota caps                             |
|  - Pre-allocated zero-copy shared memory slots                          |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Layer 2: Detection & Health Heartbeats                 |
|  - 11-State Engine Lifecycle FSM with continuous health polling         |
|  - Systemd watchdog integration (2.0-second keepalive ping)             |
|  - Sensor frame rate and timestamp delta monitors                       |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Layer 3: Graceful Degradation                          |
|  - Camera loss triggers fallback to vocal prosody emotion recognition    |
|  - NPU/GPU fault triggers CPU fallback inference execution              |
|  - Motion proposals clamped to neutral resting postures on fault        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Layer 4: Automated Recovery & Rollback                 |
|  - Worker sandbox process restart with exponential backoff              |
|  - SQLite WAL recovery on unclean reboot                                |
|  - Dual-slot A/B bootloader fallback upon persistent boot failure       |
+-------------------------------------------------------------------------+
```

---

## 2. Mean Time Between Failures (MTBF) and Service Availability Targets

- **Analytical Availability Target:** $99.95\%$ uptime during robot operational shifts.
- **Max Unassisted Recovery Time:** $\le 3.0\text{ seconds}$ from worker process crash to degraded service restoration.
