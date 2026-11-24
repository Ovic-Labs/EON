# OVIC EON — ROS 2 Security and Namespaces Specification

**Document ID:** `EON-SPEC-ROS-005`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Security Engineers, Systems Architects  
**Traceability:** `EON-ARCH-ROS-001`, ADR-021, ADR-025  

---

## 1. SROS 2 and DDS Security Architecture

In production robotic deployments, DDS communications across WiFi or internal robot networks are vulnerable to eavesdropping and message injection. EON ROS 2 integration supports SROS 2 (Secure ROS 2) extensions compliant with the DDS Security standard:
- **Authentication:** X.509 certificate validation for every node. `eon_sensor_bridge` and `eon_social_response_bridge` possess distinct signed certificates issued by the robot's local Certificate Authority (CA).
- **Access Control:** XML permissions file restricting publish/subscribe rights. Unauthorized nodes cannot publish to `/eon/erg/motion_proposal` or eavesdrop on private emotion inference topics.
- **Cryptographic Encryption:** AES-256-GCM encryption applied to all DDS transport packets carrying emotion observations or personal context identifiers.

---

## 2. Hierarchical Namespaces and Multi-Robot Topology

To prevent topic collisions in multi-robot facilities (e.g., warehouse or hospital fleets):
- **Single Robot Deployment:** Default namespace is root (`/eon/...`).
- **Fleet Deployment:** All EON topics and services are prefixed with the robot namespace:
  - `/robot_01/eon/ers/emotion_observation`
  - `/robot_01/eon/erg/motion_proposal`
  - `/robot_02/eon/ers/emotion_observation`
- **Topic Remapping:** Supported natively in launch files:
  ```xml
  <node pkg="eon_ros2_bridge" exec="sensor_bridge_node" namespace="$(var robot_id)/eon">
    <remap from="camera/color/image_raw" to="/$(var robot_id)/camera/color/image_raw"/>
  </node>
  ```
