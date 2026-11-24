# OVIC EON — ROS 2 Failure Handling Specification

**Document ID:** `EON-SPEC-ROS-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Reliability Engineers, Robotics Safety Integrators  
**Traceability:** `EON-ARCH-ROS-001`, SRS-SAFE-001, ADR-021, ADR-028  

---

## 1. Fail-Silent Social Behavior Principle

When any component in the EON infrastructure crashes, hangs, or experiences severe latency spikes:
- **No Uncontrolled Motion:** The robot must never jerk, freeze in an alarming posture, or emit invalid motor commands.
- **Fail-Silent Contract:** If EON stops publishing `/eon/erg/motion_proposal`, the host robot's social motion controller times out (after 200 ms) and gently returns actuators to a neutral, resting posture.
- **Diagnostic Signaling:** Diagnostics are immediately updated to `WARN` or `ERROR` without interfering with navigation or low-level obstacle avoidance.

---

## 2. Failure Scenarios and Containment

| Failure Mode | Detection Mechanism | Immediate Containment | Recovery Action |
|---|---|---|---|
| **EON Core Crash** | IPC socket broken in `libeonsdk` | Bridge emits zero velocity proposal; sets node to `DEGRADED` | Background watchdog attempts daemon restart up to 3 times |
| **Camera Sensor Stalled** | Ingress frame rate drops below 1 Hz | ERS enters `DEGRADED` (audio-only inference mode) | Emit diagnostic warning; resume vision on frame arrival |
| **DDS Network Partition** | Liveliness lease expires on ROS topic | Cease publication of stale observations | Resynchronize context once DDS discovery completes |
| **Memory Pressure (OOM Risk)** | Resident memory exceeds budget cap | Sensor bridge drops frame rate from 15 FPS to 5 FPS | Reclaim buffers; log warning to `/eon/diagnostics` |
