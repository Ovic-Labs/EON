# OVIC EON — Robot Actuator Abstraction Specification

**Document ID:** `EON-SPEC-ROB-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Control Engineers, HRI Developers  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022, ADR-014  

---

## 1. Actuator Abstraction Channels

EON categorizes all robot expressive outputs into four orthogonal channels:

```text
+-------------------------------------------------------------------------+
|                  Actuator Abstraction Layer Channels                    |
+-------------------------------------------------------------------------+
| Channel 1: Gaze & Neck (Pan/Tilt kinematics, social orientation)        |
| Channel 2: Facial & Lighting (OLED animated display, RGB LED patterns)  |
| Channel 3: Acoustic & Prosodic (TTS text, speech rate, pitch contour)   |
| Channel 4: Social Locomotion (Proxemic approach, comfortable distance)  |
+-------------------------------------------------------------------------+
```

---

## 2. Expression Clamping and Kinematic Limits

Before any motion proposal leaves the RAL:
1. **Velocity and Acceleration Clamping:** Trajectory suggestions are bounded by the robot's configured maximum joint velocities (e.g., neck pan $\le 1.2\text{ rad/s}$).
2. **Proxemic Distance Envelopes:** Mobile base approach proposals enforce a strict personal space buffer (default: minimum 0.8 meters from detected humans per Hall's proxemic model).
3. **Smooth Interpolation:** Sudden behavioral transitions are filtered using minimum-jerk trajectory generators to prevent unsettling or aggressive robot motions.
