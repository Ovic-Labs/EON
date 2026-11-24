# OVIC EON — Robot Platform Compatibility Specification

**Document ID:** `EON-SPEC-ROB-008`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Integrators, Commercial Hardware Partners  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022  

---

## 1. Platform Evaluation and Compatibility Tiers

EON is designed for broad hardware extensibility across standard research and commercial platforms:

| Platform Category | Example Hardware | Compute Module | Expressive Actuation | Compatibility Tier |
|---|---|---|---|---|
| **Humanoid Service** | PAL Robotics TALOS / TIAGo | Jetson AGX Orin / x86 | 2-DOF Head, Dual Arms, Mobile Base | Tier 1 (Targeted) |
| **Bipedal Research** | Unitree H1 / Boston Dynamics Spot | Jetson Orin Nano / x86 | Torso Gaze, Audio, Light Cue | Tier 1 (Targeted) |
| **Wheeled Companion** | Clearpath TurtleBot 4 / Fetch | Raspberry Pi 4 / Intel i5 | OLED Display, Light Ring, Pan Head | Tier 1 (Targeted) |
| **Social Desktop** | Furhat / Misty II | Qualcomm RB5 / Jetson | Animated Back-projected Face, Neck | Tier 2 (Supported) |
| **Industrial CoBot** | Universal Robots UR10e + AGV | Industrial PC (IPC) | Audio Beacon, Light Stack, Arm Pose | Tier 2 (Supported) |

---

## 2. Hardware Extensibility Contract

Adding support for a novel robot requires only implementing the `IRobotHardwareAdapter` interface and supplying a `RobotCapabilityManifest`. No modifications to the seven EON core engines are permitted or required.
