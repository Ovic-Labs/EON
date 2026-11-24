# OVIC EON — Robot Simulation Architecture Specification

**Document ID:** `EON-SPEC-ROB-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Simulation Engineers, Robotics Researchers  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022  

---

## 1. Simulation Architecture and Synthetic Evaluation

To validate emotional intelligence algorithms without risking physical robot damage or human injury, EON provides first-class support for robotics simulation platforms:

```text
+-------------------------------------------------------------------------+
|                  Simulation Platform (Isaac Sim / Gazebo)               |
|  - Synthetic Human Avatars (Walking, gesturing, facial expressions)     |
|  - Virtual RGB-D Sensors & Microphone Simulators                        |
|  - Simulated Robot Kinematics (URDF / USD)                              |
+-------------------------------------------------------------------------+
                                    |
                (ROS 2 / ZeroMQ Virtual Sensor Topics)
                                    v
+-------------------------------------------------------------------------+
|                 EON Simulation Hardware Adapter (`eon-sim`)              |
|  - Ingests synthetic sensor feeds                                       |
|  - Translates EON motion proposals into virtual joint commands          |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         EON Core Runtime Service                        |
+-------------------------------------------------------------------------+
```

---

## 2. Supported Simulation Engines

1. **NVIDIA Isaac Sim (USD-based):** High-fidelity synthetic human photorealism (Omniverse Humanoid characters) with PhysX dynamics.
2. **Gazebo Sim (Ignition):** Standard open-source robotics simulation with ROS 2 plugin support.
3. **Webots:** Lightweight simulation for educational and desktop social robots.
