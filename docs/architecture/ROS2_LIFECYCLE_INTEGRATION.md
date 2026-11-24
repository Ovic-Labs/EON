# OVIC EON — ROS 2 Lifecycle Integration Specification

**Document ID:** `EON-SPEC-ROS-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Software Engineers, Systems Integrators  
**Traceability:** `EON-ARCH-ROS-001`, `EON-ARCH-LIFE-001`, ADR-013, ADR-021  

---

## 1. Dual Lifecycle Coordination

EON Core maintains an internal **11-State Engine Lifecycle FSM** projected externally into a **7-State Operational Health Model** (`EON-ARCH-LIFE-001` v2.0.0). ROS 2 utilizes a standardized 4-state managed lifecycle (`rclcpp_lifecycle`).

The `eon_ros2_bridge` acts as the bidirectional coordinator between both lifecycle models:

```text
+------------------------------------+          +------------------------------------+
|       ROS 2 Managed Lifecycle      |          |     EON Core Operational Health    |
+------------------------------------+          +------------------------------------+
| UNCONFIGURED                       | <------> | UNINITIALIZED                      |
| INACTIVE                           | <------> | INITIALIZING / STOPPED             |
| ACTIVE                             | <------> | ACTIVE                             |
| (Degraded / Throttled)             | <------> | DEGRADED                           |
| (Suspended)                        | <------> | PAUSED                             |
| FINALIZED                          | <------> | FAULTED                            |
+------------------------------------+          +------------------------------------+
```

---

## 2. Transition Handlers and Guard Conditions

1. **`on_configure()` Handler:**
   - Establishes connection to EON Core daemon via `libeonsdk`.
   - Validates engine discovery (`/api/v1/engines`).
   - If EON Core is not reachable, transition fails (`CallbackReturn::FAILURE`), preventing ROS 2 launch file from proceeding.
2. **`on_activate()` Handler:**
   - Triggers `eon::lifecycle::Transition(EngineState::ACTIVE)`.
   - Enables ROS publishers and starts subscriber callbacks.
   - Activates heartbeat publishing on `/eon/lifecycle_state`.
3. **`on_deactivate()` Handler:**
   - Issues `Transition(EngineState::PAUSED)`.
   - Pauses sensor streaming into EON Core, conserving edge CPU/memory resources while preserving context.
4. **`on_cleanup()` Handler:**
   - Disconnects IPC handles and frees all allocated ROS message buffers.
5. **`on_error()` Handler:**
   - Catches unhandled exceptions, notifies ROS diagnostics, issues safe neutral motion proposal, and transitions to `FINALIZED`.
