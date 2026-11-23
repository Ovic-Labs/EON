# ADR-009: Robot Hardware Abstraction and Non-Authoritative Actuation

**Document ID:** `EON-ADR-009`  
**Status:** Approved  
**Date:** 2026-11-23  
**Deciders:** Principal Software Architect, Founder, Engineering Leads  
**Related Requirements:** `EON-FR-055`, `EON-PSR-001` through `EON-PSR-005`, `EON-SRS-120`

---

## 1. Context
Autonomous robotics is governed by strict international safety standards (ISO 13849-1, ISO 10218-1, IEC 61508) requiring safety-critical functions (emergency stopping, collision avoidance, torque clamping) to run on deterministic, certified safety hardware (PLCs or certified real-time microcontrollers). In contrast, artificial emotional intelligence and social reasoning systems are probabilistic, empirical, and inherently non-deterministic.

## 2. Problem
How can OVIC EON propose expressive physical behaviors (head tilts, pointing gestures, communicative movements) without compromising robot physical safety or assuming liability for actuator commands?

## 3. Decision
Enforce a strict **Robot Abstraction and Non-Authoritative Actuation Boundary**:
1. **Advisory Outputs Only:** All actuation proposals emitted by EON (speech, visemes, gestures) carry `is_authoritative_stop=False`. EON produces advisory communicative intent, not motor control commands.
2. **Strict Actuation Decoupling:** EON never commands actuator PWM, CAN bus velocity setpoints, or joint motor controllers directly.
3. **Independent Safety Controller Sovereignty:** The host robot manufacturer's certified safety controller retains exclusive physical motion authority. The safety controller evaluates EON's proposed gestures against dynamic obstacle fields and joint limits, and may clamp, modify, or discard any gesture without impacting EON's internal state.
4. **Hardware Abstraction Layer (HAL):** L2 HAL exposes standard telemetry (odometry, joint positions) to EON while shielding EON from proprietary motor protocols.

## 4. Alternatives Considered
1. **Direct Joint Trajectory Generation Inside EON:** Having ERG generate low-level spline trajectories directly to motor drivers. Rejected because it violates ISO 13849-1 functional safety isolation and exposes EON to catastrophic physical liability.
2. **Treating Emotion Estimates as Authorized Safety Triggers:** Allowing an emotion estimate (e.g. user panic) to trigger an emergency stop directly. Rejected; safety-critical stops must originate from certified safety sensors (e-stop buttons, safety lidars), not probabilistic machine learning models.

## 5. Consequences
- **Positive:** Complies with ISO robotics safety standards; eliminates physical injury risks from AI hallucinations; simplifies OEM integration.
- **Negative:** Robot gestures may be suppressed or delayed by host safety controllers if obstacle corridors are narrow.

## 6. Risks and Mitigations
- **Risk:** Developers might misunderstand EON's outputs as executable motor commands.
- **Mitigation:** Explicit field `is_authoritative_stop=False` enforced by Pydantic validators; clear architectural documentation in all developer guides.
