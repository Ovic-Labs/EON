# OVIC EON — Robot Interface Contracts

**Document ID:** `EON-SPEC-ROB-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Software Engineers, C++ Developers  
**Traceability:** `EON-ARCH-ROB-001`, `EON-SPEC-CPP-001`, ADR-022  

---

## 1. C++ Standard Interfaces (`eon::robot`)

```cpp
#pragma once
#include <string>
#include <memory>
#include <vector>
#include "eon/result.hpp"

namespace eon::robot {

// 1. Robot Morphology Classification
enum class Morphology : uint8_t {
    UNKNOWN = 0,
    HUMANOID = 1,
    WHEELED_SERVICE = 2,
    DESKTOP_AVATAR = 3,
    QUADRUPED = 4,
    COLLABORATIVE_ARM = 5,
    SIMULATED = 6
};

// 2. Standardized Sensor Input Packet
struct SensorPacket {
    uint64_t timestamp_ns;
    std::string frame_id;
    const uint8_t* image_data = nullptr;
    size_t image_size_bytes = 0;
    const int16_t* audio_pcm = nullptr;
    size_t audio_sample_count = 0;
    double robot_pose[7]; // x, y, z, qx, qy, qz, qw
};

// 3. Actuator Output Proposal (Strictly Non-Authoritative)
struct SocialMotionProposal {
    std::string proposal_id;
    uint64_t timestamp_ns;
    uint32_t ttl_ms;

    // MANDATORY SAFETY INVARIANT
    static constexpr bool is_authoritative = false;

    // Head / Gaze Kinematics Proposal
    bool has_gaze_request = false;
    double target_pan_rad = 0.0;
    double target_tilt_rad = 0.0;
    double target_roll_rad = 0.0;

    // Body / Base Approach Proposal
    bool has_nav_proposal = false;
    double suggested_linear_velocity = 0.0;
    double suggested_angular_velocity = 0.0;

    // Expressive Lighting / Facial Cues
    std::string expressive_cue_id;
    uint32_t cue_duration_ms = 0;
};

// 4. Abstract Hardware Adapter Interface
class IRobotHardwareAdapter {
public:
    virtual ~IRobotHardwareAdapter() = default;
    virtual Result<void> Initialize(const std::string& config_uri) = 0;
    virtual Result<void> SendMotionProposal(const SocialMotionProposal& proposal) = 0;
    virtual Result<bool> IsSafetyInterlockEngaged() const = 0;
    virtual void RegisterSensorCallback(std::function<void(const SensorPacket&)> callback) = 0;
};

} // namespace eon::robot
```
