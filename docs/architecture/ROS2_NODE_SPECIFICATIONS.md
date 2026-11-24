# OVIC EON — ROS 2 Node Specifications

**Document ID:** `EON-ARCH-ROS-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Software Developers, Robotics Engineers  
**Traceability:** `EON-ARCH-ROS-001`, ADR-021  

---

## 1. Managed Lifecycle Node Architecture

All nodes within `eon_ros2_bridge` inherit from `rclcpp_lifecycle::LifecycleNode`. This guarantees that nodes can be configured, activated, deactivated, and cleaned up through the standard ROS 2 lifecycle manager (`ros2 lifecycle set ...`).

```text
                      +-------------------+
                      |   UNCONFIGURED    |
                      +-------------------+
                                |
                   on_configure | on_cleanup
                                v
                      +-------------------+
                      |     INACTIVE      |
                      +-------------------+
                                |
                    on_activate | on_deactivate
                                v
                      +-------------------+
                      |      ACTIVE       |
                      +-------------------+
                                |
                   on_shutdown  | on_error
                                v
                      +-------------------+
                      |    FINALIZED      |
                      +-------------------+
```

---

## 2. Node Specifications

### 2.1 `eon_sensor_bridge_node`
- **Purpose:** Ingests perception data from standard ROS topics, transforms frames via `tf2_ros`, and feeds EON observation pipelines.
- **Parameters:**
  - `camera_topic` (string, default: `"camera/color/image_raw"`): Input RGB image stream.
  - `audio_topic` (string, default: `"audio/channel0"`): Input PCM audio stream.
  - `enable_zero_copy_shm` (bool, default: `true`): Uses POSIX SHM for image payloads.
  - `throttle_fps` (double, default: `15.0`): Maximum perceptual sampling rate.
- **Lifecycle Actions:**
  - `on_configure`: Establishes IPC connection to EON Core via `libeonsdk`; allocates SHM ring buffer.
  - `on_activate`: Creates ROS subscribers and starts frame conversion worker.
  - `on_deactivate`: Unsubscribes from camera/audio streams; drains pending frames.
  - `on_cleanup`: Destroys SHM handles and closes client connection.

### 2.2 `eon_social_response_bridge_node`
- **Purpose:** Listens to EON `ERG` output proposals and translates them into robot actions and trajectory proposals.
- **Parameters:**
  - `motion_proposal_topic` (string, default: `"eon/motion_proposal"`): Output proposal topic.
  - `dialogue_proposal_topic` (string, default: `"eon/dialogue_proposal"`): Output dialogue suggestion.
  - `proposal_timeout_ms` (int, default: `500`): Invalidation threshold.
- **Enforcement:** Explicitly stamps `is_authoritative = false` on all published proposals.

### 2.3 `eon_diagnostics_node`
- **Purpose:** Translates EON 7-state operational health into ROS 2 `diagnostic_msgs/msg/DiagnosticArray`.
- **Publish Rate:** 2 Hz (or immediately upon state transition).
- **Diagnostics Namespace:** `/eon/engines/<engine_name>`.
