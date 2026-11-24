# ADR-021: ROS 2 Decoupled Integration Strategy

**Document ID:** `EON-ADR-021`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Robotics Middleware, ROS 2 Integration  

---

## 1. Context and Problem Statement

ROS 2 is the prevailing middleware standard in robotics. However, tight architectural coupling between EON Core and ROS 2 would create massive dependency overhead (rclcpp, DDS vendors, colcon build tools) for non-ROS robotic platforms and standalone embedded systems.

## 2. Decision

We decide to maintain complete independence of EON Core from ROS 2:
1. EON Core remains a standalone service communicating over local IPC (`libeonsdk`).
2. ROS 2 support is provided via an optional, standalone bridge package: `eon_ros2_bridge`.
3. All ROS 2 bridge nodes implement standard `rclcpp_lifecycle::LifecycleNode` contracts, synchronized with EON's 7-state operational health projection.
4. All motion outputs are published as non-authoritative proposals (`is_authoritative = false`).

## 3. Alternatives Considered

- *Alternative A: Native ROS 2 Node Architecture for all 7 EON Engines.* Rejected: Forces ROS 2 as a mandatory build and runtime dependency, preventing standalone lightweight edge deployments.
- *Alternative B: Custom non-lifecycle ROS 2 nodes.* Rejected: Precludes deterministic launch coordination with Nav2 and robot state managers.

## 4. Consequences and Implications

- **Positive:** Maximum architectural flexibility; EON can run in ROS 2, ROS 1, Zenoh, or pure RTOS environments.
- **Negative:** Introduces a lightweight bridge layer between ROS 2 topics and EON IPC.
- **Security Implications:** Supports SROS 2 / DDS Security with X.509 certificate validation.
- **Privacy Implications:** Prevents unauthorized node subscription to private emotion observation topics.
- **Performance Implications:** Zero-copy SHM passing reduces frame conversion overhead.
- **Related ADRs:** ADR-008, ADR-013, ADR-014, ADR-020.
- **Supersession History:** None.
