# OVIC EON — ROS 2 Service and Action Contracts

**Document ID:** `EON-SPEC-ROS-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Developers, Robotics Integrators  
**Traceability:** `EON-ARCH-ROS-001`, ADR-021  

---

## 1. Custom Service Definitions (`eon_msgs/srv`)

### 1.1 `eon_msgs/srv/GetEngineState.srv`
Queries the operational health of a specific EON intelligence engine:
```text
# Request
string engine_id          # e.g., "ers", "ems", "ere", "pse", "sie", "erg", "hbu"
---
# Response
bool success
string engine_state       # UNINITIALIZED, INITIALIZING, ACTIVE, PAUSED, DEGRADED, STOPPED, FAULTED
uint64 uptime_ms
string last_error_message
```

### 1.2 `eon_msgs/srv/PurgeSubjectContext.srv`
Requests immediate contextual shredding of user data (Right to be Forgotten):
```text
# Request
string subject_id         # Unique subject context identifier
bool confirm_shredding    # Mandatory explicit confirmation
---
# Response
bool success
uint32 records_purged
string message
```

---

## 2. Custom Action Definitions (`eon_msgs/action`)

### 2.1 `eon_msgs/action/ExecuteSocialInteraction.action`
Coordinates multi-modal social interaction sequences (e.g., welcoming a visitor):
```text
# Goal
string interaction_type        # e.g., "GREETING", "EMPATHIC_LISTENING", "FAREWELL"
string subject_id
uint32 timeout_seconds
---
# Result
bool completed_successfully
string termination_reason      # "USER_DEPARTED", "TIMED_OUT", "COMPLETED", "INTERRUPTED"
uint32 total_duration_ms
---
# Feedback
string current_phase           # "APPROACH", "ENGAGING", "CONCLUDING"
float32 interaction_progress   # 0.0 to 1.0
float32 detected_valence       # Latest estimated user valence
```
