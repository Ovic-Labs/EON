# OVIC EON — Robot Safety Boundaries Specification

**Document ID:** `EON-SPEC-ROB-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Safety Engineers, Systems Certifiers, Robotics Architects  
**Traceability:** `EON-ARCH-ROB-001`, SRS-SAFE-001, ADR-014, ADR-022  

---

## 1. Mandatory Physical Robot Safety Boundary

In compliance with EON Principle 2.4 and ISO 13482 (Safety requirements for personal care robots):

> [!CAUTION]
> **Fundamental Safety Invariant:** EON’s emotion and social intelligence systems **must never directly authorize physical robot movement**. The robot manufacturer's certified safety controller, collision avoidance layer, and physical emergency stop hardware retain absolute final authority.

```text
       [EON Emotion Response Generation (ERG)]
                         |
                         v (Suggests: "Nod head affirmatively")
             [SocialMotionProposal]
          (is_authoritative = false)
                         |
                         v
       +------------------------------------+
       |  Robot Manufacturer Safety Arbiter |
       |                                    |
       |  - Obstacle proximity check        |
       |  - Emergency Stop status           |
       |  - Torque and velocity limits      |
       +------------------------------------+
            /                           \
 (Approved & Clamped)              (Safety Conflict / E-Stop Active)
          /                               \
         v                                 v
[Low-Level Motor Drivers]         [Motion Rejected / Neutral Halt]
```

---

## 2. Fail-Silent Safety Guarantee

1. **Safety Interlock Monitoring:** The RAL continuously inspects the robot's safety status. If an emergency stop is active, all EON motion proposals are suppressed immediately.
2. **Zero Motor Authority:** EON has zero network or IPC access to low-level actuator buses (EtherCAT, CANopen).
3. **Heartbeat Watchdog:** If EON crashes or experiences an execution hang, the safety arbiter detects the absence of heartbeats within 200 ms and commands safe idle holding torques.
