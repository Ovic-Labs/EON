# OVIC EON — ROS 2 Distribution Compatibility Specification

**Document ID:** `EON-SPEC-ROS-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Maintainers, Release Engineers  
**Traceability:** `EON-ARCH-ROS-001`, ADR-021  

---

## 1. Distribution Support Policy and Rationale

EON targets Tier-1 Long Term Support (LTS) distributions of ROS 2, alongside current intermediate stable releases:

| Distribution | Release Type | Underlying OS | End of Life (EOL) | Support Tier |
|---|---|---|---|---|
| **ROS 2 Humble Hawksbill** | LTS | Ubuntu 22.04 LTS (Jammy) | May 2027 | **Tier 1 (Primary)** |
| **ROS 2 Iron Irwini** | Intermediate | Ubuntu 22.04 LTS / 23.04 | Nov 2024 (Extended) | **Tier 2 (Supported)** |
| **ROS 2 Jazzy Jalisco** | LTS | Ubuntu 24.04 LTS (Noble) | May 2029 | **Tier 1 (Primary)** |
| **ROS 2 Rolling Ridley** | Rolling | Ubuntu 24.04+ | Continuous | **Continuous Build** |

### Rationale
- **Humble:** The dominant commercial standard in contemporary production robotics (supported extensively by NVIDIA JetPack, Intel, and Clearpath).
- **Jazzy:** The newest 5-year LTS distribution on Ubuntu 24.04, critical for modern forward-looking hardware deployments.
- **RMW Middleware Support:** Validated against CycloneDDS, FastDDS, and Zenoh-RMW.

---

## 2. Standalone Independence Guarantee

EON Core is strictly **independent of ROS 2**. A host system without ROS 2 installed can compile and run EON Core and both Python and C++ SDKs. The `eon_ros2_bridge` is built only when `ament_cmake` is detected during CMake configuration (`if(TARGET ament_cmake ...)`).
