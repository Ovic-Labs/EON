# OVIC EON — Robot Abstraction Architecture Specification

**Document ID:** `EON-ARCH-ROB-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Hardware Engineers, Systems Architects, Integration Specialists  
**Traceability:** PRD Section 4.5, SRS-ARCH-012, ADR-022, ADR-014, ADR-021  

---

## 1. Executive Summary and Architectural Mission

The **OVIC EON Robot Abstraction Layer (RAL)** establishes a vendor-neutral, hardware-independent abstraction boundary between EON’s seven emotional intelligence engines and the physical robot platform.

Robotic platforms exhibit radical variations in morphology:
- **Humanoid Robots:** Articulated arms, multi-DOF expressive head, bipedal locomotion, animated digital face.
- **Wheeled Service Robots:** Non-holonomic or omnidirectional mobile base, fixed torso, tablet screen, LED light ring.
- **Social Desktop Robots:** Stationary base, expressive mechanical neck, motorized eyelids, speaker array.
- **Industrial Mobile Manipulators:** Heavy-duty collaborative arm on AGV base, audible tone emitter, safety beacon.

EON’s intelligence engines must not contain robot-specific kinematics, motor protocols (CANopen, EtherCAT, Dynamixel), or custom hardware drivers. The RAL decouples intelligence from embodiment by:
1. Translating normalized perception streams from diverse sensors into standardized observation formats.
2. Formulating behavioral and emotional responses into **non-authoritative proposals** adapted to the robot's physical capabilities.
3. Enforcing an unbypassable safety barrier where the robot manufacturer's safety controller retains exclusive authority over physical actuators.

---

## 2. Layered Architecture Topology

```text
+-------------------------------------------------------------------------+
|                  EON Intelligence Layer (7 Engines)                     |
|        [ERS]    [EMS]    [ERE]    [PSE]    [SIE]    [ERG]    [HBU]      |
+-------------------------------------------------------------------------+
                                    |
                    (Normalized Observations / Proposals)
                                    v
+-------------------------------------------------------------------------+
|                    Robot Abstraction Layer (RAL)                        |
|                                                                         |
|  +---------------------------+       +-------------------------------+  |
|  |   Sensor Abstraction      |       |   Capability Model & Arbiter  |  |
|  | (Camera, Audio, IMU, TF)  |       | (Negotiates features & limits)|  |
|  +---------------------------+       +-------------------------------+  |
|               ^                                      |                  |
|               |                                      v                  |
|  +---------------------------+       +-------------------------------+  |
|  | Hardware Adapter Plugin   |       |   Actuator Proposal Adapter   |  |
|  | (ROS 2, ZeroMQ, gRPC, IPC)|       | (Translates to robot dialect) |  |
|  +---------------------------+       +-------------------------------+  |
+-------------------------------------------------------------------------+
                                                       |
                                    (Non-Authoritative Proposals)
                                                       v
+-------------------------------------------------------------------------+
|                 Robot Manufacturer Safety Arbiter & HAL                 |
|   - Collision Avoidance (Nav2 Costmaps / Arm Trajectory Limits)         |
|   - Hardware Emergency Stop (Safety Relay / Actuator Power Interlock)   |
|   - Low-Level Motor Controllers (CAN / EtherCAT / Serial)               |
+-------------------------------------------------------------------------+
```

---

## 3. Core Architectural Principles of the RAL

1. **Hardware Invariance:** The core cognitive loop operates identically whether connected to a simulated robot in NVIDIA Isaac Sim, a physical humanoid robot, or a desktop avatar.
2. **Dynamic Capability Negotiation:** During connection handshake, the robot platform declares its supported sensors and expressive actuators. EON dynamically adjusts its reasoning pipelines.
3. **Graceful Expressive Degradation:** If a robot lacks a proposed expressive modality (e.g., no pan-tilt head), the RAL automatically routes emotional expression to available alternatives (e.g., modulated speech prosody or LED light cues).
4. **Absolute Physical Non-Authority:** EON never directly writes to motor registers or pulse-width modulators. All motion requests are formatted as proposals that may be modified, clamped, or vetoed by the robot's safety hardware.

---

## 4. Traceability Matrix

| Requirement ID | Architectural Requirement | Specification Document |
|---|---|---|
| `PRD-REQ-006` | Universal compatibility across diverse robot morphologies | `ROBOT_CAPABILITY_MODEL.md` |
| `SRS-ARCH-012` | Hardware-independent abstraction layer | `ROBOT_INTERFACE_CONTRACTS.md` |
| `ADR-022` | Architecture Decision Record: Robot Abstraction Layer | `ADR-022-hardware-independent-robot-abstraction.md` |
| `ADR-014` | Non-authoritative safety boundary enforcement | `ROBOT_SAFETY_BOUNDARIES.md` |
