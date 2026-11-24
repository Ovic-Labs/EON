# ADR-022: Hardware-Independent Robot Abstraction Layer (RAL)

**Document ID:** `EON-ADR-022`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Robot Morphology, Kinematics, Actuator Decoupling  

---

## 1. Context and Problem Statement

EON must operate across diverse physical robot embodiments (humanoids, wheeled mobile bases, social desktop avatars, quadruped platforms). Hardcoding robot-specific kinematics or actuator protocols into EON's intelligence engines would destroy modularity and cross-platform portability.

## 2. Decision

We decide to establish the **Robot Abstraction Layer (RAL)**:
1. Normalizes perception inputs into standardized sensor packets (camera, audio, odometry).
2. Establishes a dynamic capability negotiation model (`RobotCapabilityManifest`) allowing robots to declare available sensors, expressive actuators, and kinematic limits.
3. Formulates behavioral outputs strictly as **non-authoritative proposals** (`SocialMotionProposal` with `is_authoritative = false`).
4. Enforces an unbypassable boundary where the robot manufacturer's safety controller retains exclusive authority over physical motor actuation.

## 3. Alternatives Considered

- *Alternative A: Direct Actuator Motor Control in EON.* Rejected: Violates ISO 13482 safety principles and risks human injury.
- *Alternative B: Robot-Specific Engine Builds.* Rejected: High maintenance cost and fractured codebase.

## 4. Consequences and Implications

- **Positive:** Complete decoupling of emotional intelligence from physical hardware; full support for simulated platforms (Isaac Sim, Gazebo).
- **Negative:** Requires capability negotiation during robot connection.
- **Security Implications:** Zero motor driver code inside EON prevents actuator takeover via EON compromise.
- **Privacy Implications:** Hardware adapter can enforce local physical recording indicator LEDs.
- **Performance Implications:** Negligible overhead ($\le 0.05\text{ ms}$) for proposal clamping.
- **Related ADRs:** ADR-009, ADR-014, ADR-021.
- **Supersession History:** None.
