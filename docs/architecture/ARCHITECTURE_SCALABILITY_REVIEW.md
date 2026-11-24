# OVIC EON — Architecture Scalability Review Specification

**Document ID:** `EON-REV-SCAL-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Architects, Performance Engineers, Robotics Integrators  
**Traceability:** PRD Section 4.5, SRS-PERF-001, ADR-028  

---

## 1. Executive Summary and Review Scope

This review evaluates the architectural scalability of OVIC EON across both vertical dimensions (hardware constraints on a single robot edge computer) and horizontal dimensions (concurrent users, multi-robot fleets, and optional cloud federation).

> [!IMPORTANT]
> **Analytical Design Notice:** All metrics in this document represent **analytical design estimates and engineering calculations**. In accordance with Phase 2 governance rules, they do not claim executed production load test benchmarks. Formal empirical validation will take place during Phase 3 runtime implementation.

---

## 2. Scalability Dimensions

### 2.1 Single-Robot Vertical Scalability
- **Perception Ingress:** Ingests up to 30 FPS 1080p RGB video and 16 kHz multi-channel audio using zero-copy POSIX shared memory ring buffers (`/dev/shm`), avoiding user-space buffer copies.
- **Engine Event Throughput:** Event bus architecture utilizes lock-free single-producer single-consumer (SPSC) ring buffers designed for an analytical throughput of $\ge 5,000\text{ events/sec}$ on an 8-core CPU.
- **Model Execution:** Tiered inference schedulers support dynamic downsampling (e.g., dropping vision from 15 FPS to 5 FPS) under high CPU load.

### 2.2 Concurrent Human Interaction Scalability
- **Single-User Dyadic Interaction:** Nominal operational baseline; 1 primary subject tracked with full facial, prosodic, and postural reasoning.
- **Group / Multi-User Scenarios (Classrooms / Public Atriums):**
  - Up to 4 simultaneous detected subjects in the visual field.
  - Primary interlocutor assigned based on visual gaze orientation, proximity ($< 1.5\text{ m}$), and speech turn-taking.
  - Secondary subjects tracked using lightweight low-dimensional bounding boxes and coarse affect; full deep emotion modeling reserved for the active interlocutor to preserve edge CPU budgets.

### 2.3 Horizontal Fleet Scalability
- **Decoupled Architecture:** Each robot operates as a completely independent edge processing node; fleet expansion ($N = 1$ to $N = 10,000$) introduces zero additional intra-robot latency.
- **Cloud Bandwidth:** Edge-first inference transmits only aggregated telemetry ($\le 5\text{ MB/robot/day}$), allowing standard cloud database clusters to support thousands of robots at minimal cost.
