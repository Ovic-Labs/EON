# ADR-008: ROS 2 Integration and Lifecycle Node Boundary

**Document ID:** `EON-ADR-008`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-050`, `EON-NFR-055`, `EON-SRS-110`, `EON-ARCH-ROS2-001`

---

## 1. Context
ROS 2 (Robot Operating System 2) is the de facto industry standard middleware for commercial and academic robotics. Integrating EON with ROS 2 (specifically ROS 2 Jazzy Jalisco and Humble Hawksbill) is essential for commercial adoption. However, ROS 2 brings heavy dependencies (rclpy, rclcpp, DDS middleware, FastDDS/CycloneDDS) that must not infect EON's standalone edge runtime.

## 2. Problem
How should EON integrate with ROS 2 without making ROS 2 a mandatory runtime dependency for non-ROS robots or standalone deployments?

## 3. Decision
Isolate ROS 2 integration within an independent adapter package (**`eon_ros2`**) inside **Layer 8 (SDK & Integration Layer)**:
1. **Optional Dependency:** The core `ovic_eon` package maintains zero dependencies on `rclpy` or ROS 2 packages. ROS 2 support is installed as an optional extension (`pip install ovic_eon[ros2]`).
2. **Managed Lifecycle Node:** Implement `EonLifecycleNode` conforming to standard `rclpy.lifecycle` state machines (`Unconfigured`, `Inactive`, `Active`, `Finalized`), synchronized with EON's internal engine lifecycles.
3. **Standardized Message Definitions:** Expose native ROS 2 messages (`.msg`, `.srv`, `.action`) in package `eon_msgs` that cleanly map to Phase 1.2 Pydantic schemas.
4. **Safety Demarcation:** All ROS 2 topics published by `eon_node` (e.g., `/eon/proposals`) publish standard advisory messages. Robot safety nodes subscribe to advisory topics and apply certified collision and torque checks.

## 4. Alternatives Considered
1. **Re-architecting EON Core as Native ROS 2 Nodes:** Making each of the seven engines an independent ROS 2 node communicating via DDS topics. Rejected because DDS introduces significant memory footprint (>400 MB overhead for 7 nodes) and high serialization latency on embedded ARM64 boards, while making standalone non-ROS deployment impossible.
2. **Third-Party Bridge (rosbridge_suite / WebSockets):** Rejected due to high latency (>15 ms per message) and unreliable QoS guarantees for real-time perception.

## 5. Consequences
- **Positive:** EON remains lightweight and standalone for non-ROS platforms; ROS 2 developers receive first-class native lifecycle nodes and message types; clean safety boundaries.
- **Negative:** Requires maintaining conversion functions between ROS 2 `.msg` structures and Pydantic v2 models.

## 6. Risks and Mitigations
- **Risk:** Serialization performance bottleneck between ROS 2 messages and Pydantic schemas.
- **Mitigation:** Zero-copy buffer views and optimized C-extension serialization paths in `eon_ros2`.
