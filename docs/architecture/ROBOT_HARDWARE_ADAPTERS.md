# OVIC EON — Robot Hardware Adapters Specification

**Document ID:** `EON-SPEC-ROB-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Hardware Engineers, Systems Integrators  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022  

---

## 1. Adapter Architecture and Plugin Model

Robot hardware adapters in EON are dynamically loaded plugins or independent bridge processes. This isolates proprietary robot SDKs (e.g., SoftBank NAOqi, Boston Dynamics Spot SDK, Unitree SDK) from EON Core.

```text
+-------------------------------------------------------------------------+
|                                EON RAL                                  |
+-------------------------------------------------------------------------+
        |                                                 |
        v (Adapter Interface)                             v (Adapter Interface)
+-----------------------------------+             +-----------------------+
|  ROS 2 Bridge Adapter Plugin      |             | Standalone gRPC / UDS |
|  - Interfaces with /cmd_vel       |             |  Adapter Plugin       |
|  - Subscribes to /camera/image    |             |  - Direct robot IPC   |
+-----------------------------------+             +-----------------------+
        |                                                 |
        v                                                 v
[ROS 2 Robot Platform]                            [Proprietary Robot OS]
```

---

## 2. Standardized Adapter Reference Profiles

1. **ROS 2 Adapter (`eon-adapter-ros2`):**
   - Transports sensors via `sensor_msgs/msg/Image` and `audio_common_msgs`.
   - Publishes proposals to `/eon/motion_proposal`.
2. **gRPC / Protocol Buffer Adapter (`eon-adapter-grpc`):**
   - Designed for robots with non-ROS operating systems (e.g., Android-based companion robots or proprietary RTOS).
   - Bi-directional streaming RPC over local TCP or Unix Domain Socket.
3. **Shared Memory Direct Adapter (`eon-adapter-shm`):**
   - High-performance direct C++ memory linking for integrated monolithic robot controllers.
