# OVIC EON — ROS 2 Quality of Service (QoS) Policies

**Document ID:** `EON-SPEC-ROS-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Systems Architects, Middleware Engineers  
**Traceability:** `EON-ARCH-ROS-001`, SRS-PERF-001, ADR-021  

---

## 1. QoS Profile Selection Rationale

ROS 2 DDS communication relies on Quality of Service (QoS) profiles to balance latency, packet loss, and reliability. Mismatched QoS policies between publishers and subscribers lead to silent communication dropouts.

EON categorizes all ROS 2 communication into three formal QoS profiles:

```text
+-------------------------------------------------------------------------+
| Profile A: Sensor Data QoS (High-rate perceptual streams)               |
| - Reliability: Best Effort        - Durability: Volatile                |
| - History: Keep Last (Depth: 5)   - Liveliness: Automatic               |
+-------------------------------------------------------------------------+
| Profile B: Social Proposals & Events QoS (Commands & Inferences)        |
| - Reliability: Reliable           - Durability: Volatile                |
| - History: Keep Last (Depth: 10)  - Deadline: 200 ms                    |
+-------------------------------------------------------------------------+
| Profile C: System Diagnostics & Lifecycle QoS (State & Config)          |
| - Reliability: Reliable           - Durability: Transient Local (Latched)|
| - History: Keep Last (Depth: 1)   - Liveliness: Manual by Topic         |
+-------------------------------------------------------------------------+
```

---

## 2. QoS Policy Mapping Table

| Topic / Stream | QoS Profile | Reliability | Durability | Depth | Deadline |
|---|---|---|---|---|---|
| `/eon/sensors/camera/image_raw` | Profile A (Sensor) | Best Effort | Volatile | 2 | None |
| `/eon/sensors/audio/audio_data` | Profile A (Sensor) | Best Effort | Volatile | 10 | None |
| `/eon/ers/emotion_observation` | Profile B (Events) | Reliable | Volatile | 5 | 200 ms |
| `/eon/erg/motion_proposal` | Profile B (Events) | Reliable | Volatile | 5 | 100 ms |
| `/eon/diagnostics` | Profile C (Diagnostics) | Reliable | Transient Local | 1 | 1000 ms |
| `/eon/lifecycle_state` | Profile C (Diagnostics) | Reliable | Transient Local | 1 | None |

### Deadline and Liveliness Monitoring
- For `/eon/erg/motion_proposal`, if no proposal is received within the 100 ms deadline, the robot's motion controller immediately detects subscriber deadline missed and returns head/gaze to neutral resting position.
