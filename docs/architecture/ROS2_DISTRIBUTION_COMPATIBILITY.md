# OVIC EON — ROS 2 Distribution Compatibility Specification

**Document ID:** `EON-SPEC-ROS-007`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.12)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** ROS 2 Maintainers, Release Engineers, Robotics Integrators  
**Traceability:** `EON-ARCH-ROS-001`, ADR-021  
**Authoritative References:**  
- Open Robotics ROS 2 Releases: `https://docs.ros.org/en/rolling/Releases.html`  
- ROS Enhancement Proposal 2000 (REP-2000): `https://www.ros.org/reps/rep-2000.html`  

---

## 1. Distribution Support Policy and Official Tiers

OVIC EON integrates with the Robot Operating System 2 (ROS 2) ecosystem via the optional `eon_ros2_bridge` package. To guarantee system reliability, long-term security maintenance, and compatibility with commercial robotics platforms, EON strictly adheres to the official Open Robotics release lifecycle:

| Distribution Name | Release Type | Target Operating System | Release Date | End of Life (EOL) | EON Support Tier | Support Policy & Status |
|---|---|---|---|---|---|---|
| **ROS 2 Humble Hawksbill** | Long Term Support (LTS) | Ubuntu 22.04 LTS (Jammy) | May 2022 | **May 2027** | **Tier 1 (Primary)** | Fully supported. Primary production target for existing commercial robotics deployments (NVIDIA JetPack 5/6, Clearpath, TurtleBot 4). |
| **ROS 2 Jazzy Jalisco** | Long Term Support (LTS) | Ubuntu 24.04 LTS (Noble) | May 2024 | **May 2029** | **Tier 1 (Primary)** | Fully supported. Primary production target for modern and future robotics platforms on Ubuntu 24.04 LTS. |
| **ROS 2 Kilted Kaiju** | Standard (Non-LTS) | Ubuntu 24.04 LTS (Noble) | May 2025 | **November 2026** | **Tier 2 (Planned)** | Secondary support. Planned for validation following general availability in May 2025. |
| **ROS 2 Rolling Ridley** | Rolling Development | Ubuntu 24.04 LTS (Noble)+ | Continuous | Continuous | **Continuous Build** | Automated CI target for early detection of upstream API changes and deprecations. |
| **ROS 2 Iron Irwini** | Standard (Non-LTS) | Ubuntu 22.04 / 23.04 | May 2023 | **November 2024** | **Legacy / EOL (Unsupported)** | **End of Life reached in November 2024.** No active bug fixes, security patches, or support commitments. Best-effort build guidance only. |
| **ROS 2 Galactic Geochelone** | Standard (Non-LTS) | Ubuntu 20.04 / 21.10 | May 2021 | **November 2022** | **Unsupported (EOL)** | Deprecated and unsupported. |
| **ROS 2 Foxy Fitzroy** | Long Term Support (LTS) | Ubuntu 20.04 LTS (Focal) | June 2020 | **May 2023** | **Unsupported (EOL)** | Deprecated and unsupported. |

---

## 2. Tier 1 Support Commitments (Humble & Jazzy)

For Tier 1 distributions, OVIC EON commits to:
1. **Automated CI Validation:** Matrix builds running on every commit against official binary Debian packages for both `amd64` (x86_64) and `arm64` (aarch64).
2. **First-Party Message Packages:** Native pre-compiled `eon_msgs` interface packages matching distribution standards.
3. **Managed Lifecycle Nodes:** Full validation of `rclcpp_lifecycle::LifecycleNode` state transitions and error recovery hooks.
4. **Tested RMW Implementations:** Verified against both `rmw_cyclonedds_cpp` and `rmw_fastrtps_cpp`.
5. **Security Enclave Support:** Compatibility with SROS 2 keystores and DDS security access control policies.

---

## 3. Legacy and End-of-Life (EOL) Policy: ROS 2 Iron Irwini

ROS 2 Iron Irwini was an intermediate non-LTS release with an 18-month lifecycle concluding in **November 2024**.

> [!WARNING]
> **ROS 2 Iron End-of-Life Notice:**
> - As of November 2024, ROS 2 Iron Irwini has officially reached End-of-Life per REP-2000. Upstream Open Robotics repositories no longer provide updates, security patches, or binary backports for Iron.
> - EON classifies ROS 2 Iron strictly as **Legacy / EOL (Unsupported)**.
> - No new features or critical security fixes will be validated against ROS 2 Iron.
> - Existing robot integrators running Iron are strongly advised to migrate to **ROS 2 Humble** (supported through May 2027 on Ubuntu 22.04) or **ROS 2 Jazzy** (supported through May 2029 on Ubuntu 24.04).

---

## 4. Middleware (RMW) Compatibility

OVIC EON tests and qualifies the bridge against the standard ROS 2 Middleware implementations:

| RMW Layer | Distribution Default | Support Level | Notes |
|---|---|---|---|
| `rmw_cyclonedds_cpp` | Humble default | **Tier 1 (Certified)** | Recommended for high-reliability local IPC and multi-node discovery. |
| `rmw_fastrtps_cpp` | Jazzy default | **Tier 1 (Certified)** | High throughput on multicore Linux architectures; validated with eProsima Fast DDS 2.x. |
| `rmw_zenoh_cpp` | Optional / Experimental | **Tier 3 (Experimental)** | Evaluated for ultra-low-power edge nodes and high-latency wireless mesh links. |

---

## 5. Standalone Independence Guarantee

EON Core is strictly **independent of ROS 2**:
- A host system without ROS 2 installed can compile, configure, and execute EON Core, the Python SDK (`eon-sdk`), and the C++ SDK (`libeonsdk`).
- The `eon_ros2_bridge` package is an optional client built conditionally when `ament_cmake` is detected during CMake configuration (`if(TARGET ament_cmake ...)`).
- Crash, failure, or absence of the ROS 2 daemon has zero impact on core emotional intelligence processing or local shared memory IPC.
