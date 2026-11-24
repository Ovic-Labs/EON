# OVIC EON — Robot Capability Model Specification

**Document ID:** `EON-SPEC-ROB-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Software Engineers, Product Integrators  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022  

---

## 1. Capability Declaration Schema

During initial registration, the robot hardware adapter transmits a `RobotCapabilityManifest` to EON Core. This manifest describes available perceptual inputs and expressive outputs:

```json
{
  "$schema": "https://eon.oviclabs.com/schemas/v1/robot-capability.json",
  "robot_id": "humanoid_talos_04",
  "morphology": "HUMANOID",
  "sensors": {
    "rgb_camera": { "available": true, "max_fps": 30, "resolution": [1920, 1080] },
    "depth_camera": { "available": true, "max_fps": 15, "resolution": [640, 480] },
    "microphone_array": { "available": true, "channels": 4, "sample_rate_hz": 16000 },
    "imu": { "available": true, "rate_hz": 100 }
  },
  "actuators": {
    "head_pan_tilt": { "available": true, "max_pan_rad": 1.57, "max_tilt_rad": 0.78 },
    "facial_display": { "available": false },
    "light_ring": { "available": true, "led_count": 24, "rgb": true },
    "speech_synthesizer": { "available": true, "supports_prosody_modulation": true },
    "gesture_arms": { "available": true, "dof_per_arm": 7 },
    "mobile_base": { "available": true, "type": "BIPEDAL" }
  },
  "safety_envelope": {
    "max_velocity_head_rad_s": 1.0,
    "max_linear_speed_m_s": 0.5,
    "min_social_distance_m": 0.8
  }
}
```

---

## 2. Capability Negotiation and Expressive Fallback

When the Emotion Response Generation (ERG) engine creates a behavioral response, the RAL queries the capability model:

```text
[ERG Generates Response: "Attentive Greeting"]
                   |
                   v
      [Capability Arbiter Check]
      - Head pan-tilt available?  --> YES: Emit gaze proposal
      - Facial screen available?  --> NO:  Trigger Fallback Path
                                           |
                                           v
                   [Fallback: Modulate LED light ring to gentle green breathe
                              + Adjust speech prosody pitch +15%]
```

### Expressive Fallback Matrix

| Desired Expression | Primary Actuator | Fallback Tier 1 | Fallback Tier 2 | Fallback Tier 3 |
|---|---|---|---|---|
| **Attentive Gaze** | Pan-Tilt Head | Body Turn (Mobile Base) | Eye Display Vector | Voice Orientation Cue |
| **Warm Smile** | Facial Display | Light Ring Color Shift | Pleasant Audio Chime | Soft Speech Prosody |
| **Affirmative Nod** | Head Pitch Joint | Light Ring Flash | Vocal Confirmation ("Mhm") | None (Omit) |
| **Social Approach** | Mobile Base | Gaze Toward User | Audio Greeting | None (Stationary) |
