# OVIC EON — Security Threat Model Specification (STRIDE)

**Document ID:** `EON-SPEC-SEC-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.16)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Security Engineers, Penetration Testers, Systems Architects  
**Traceability:** `EON-ARCH-SEC-001`, ADR-025  

---

## 1. STRIDE Threat Analysis Matrix

The system undergoes threat modeling across all six STRIDE categories:

### 1.1 Spoofing (Identity Deception)
- **Threat ID:** `THR-SPOOF-01`
- **Attack Surface:** Local Unix Domain Socket `/var/run/eon/eon.sock`.
- **Threat Scenario:** A rogue non-privileged process on the host robot connects to EON Core, impersonating `eon_ros2_bridge` to inject false emotion events.
- **Impact:** High (Robot exhibits corrupted social behavior).
- **Likelihood:** Medium.
- **Mitigation:** Kernel-level peer credential inspection (`SO_PEERCRED`) verifying client UID/GID matches the authorized `eon-clients` group.
- **Residual Risk:** Low (Compromise of the `eon-clients` system user required).
- **Verification Method:** Negative automated integration test asserting connection rejection from unauthorized UID.

### 1.2 Tampering (Data Manipulation)
- **Threat ID:** `THR-TAMP-01`
- **Attack Surface:** Shared memory segment `/dev/shm/eon_perception_*`.
- **Threat Scenario:** A malicious local process writes noise or adversarial visual perturbations into the shared memory camera buffer to fool the ERS face analysis neural network.
- **Impact:** Medium (Incorrect emotion inference).
- **Likelihood:** Medium.
- **Mitigation:** SHM segment handles passed strictly via Unix socket file-descriptor passing (`SCM_RIGHTS`). Anonymous memory mapping (`memfd_create`) eliminates named `/dev/shm` filesystem links.
- **Residual Risk:** Low.
- **Verification Method:** Test asserting that unlinked `memfd` segments cannot be opened via filesystem paths.

### 1.3 Repudiation (Denial of Actions)
- **Threat ID:** `THR-REP-01`
- **Attack Surface:** Context deletion and consent modification requests.
- **Threat Scenario:** An operator claims a user’s context deletion request was never executed, or a malicious actor denies altering robot personality parameters.
- **Impact:** Medium (Regulatory compliance violation, audit failure).
- **Likelihood:** Low.
- **Mitigation:** Tamper-evident append-only audit log with SHA-256 cryptographic hash-chaining of all administrative and consent events.
- **Residual Risk:** Negligible.
- **Verification Method:** Automated script verifying cryptographic hash chain consistency.

### 1.4 Information Disclosure (Data Leakage)
- **Threat ID:** `THR-INFO-01`
- **Attack Surface:** On-disk SQLite context database (`context.db`).
- **Threat Scenario:** A physical attacker steals the robot's SSD or accesses an unencrypted disk backup, reading historical interaction summaries and user preferences.
- **Impact:** High (Severe privacy breach).
- **Likelihood:** Medium.
- **Mitigation:** Envelope encryption using AES-256-GCM. Per-subject Data Encryption Keys (DEKs) wrapped by a Key Encryption Key (KEK) protected by TPM 2.0 or secure system keyring.
- **Residual Risk:** Low.
- **Verification Method:** Cryptographic entropy analysis of on-disk database files.

### 1.5 Denial of Service (System Disruption)
- **Threat ID:** `THR-DOS-01`
- **Attack Surface:** Event publication ingress queue.
- **Threat Scenario:** A misbehaving sensor driver floods the EON event bus with 10,000 events/sec, exhausting memory and starving social response loops.
- **Impact:** High (EON Core crashes or freezes).
- **Likelihood:** High.
- **Mitigation:** Strict bounded circular queues with priority drops (`DROP_OLDEST`) and token-bucket ingress rate limiting per topic.
- **Residual Risk:** Low.
- **Verification Method:** Stress-testing queue under 100x nominal event load.

### 1.6 Elevation of Privilege (Unauthorized Authority)
- **Threat ID:** `THR-ELEV-01`
- **Attack Surface:** Actuator proposal channel to robot safety arbiter.
- **Threat Scenario:** An attacker exploits an ONNX runtime buffer overflow in ERS to gain shell access and attempts to command physical robot locomotion to injure a human.
- **Impact:** Critical (Physical hazard to humans).
- **Likelihood:** Low.
- **Mitigation:**
  1. Sandboxing of EON Core via `systemd` (`NoNewPrivileges=true`, `ProtectSystem=strict`).
  2. Non-Authoritative Architecture: EON has zero physical actuator drivers or CAN bus interfaces. The robot's independent safety controller rejects any motion exceeding speed or proximity limits.
- **Residual Risk:** Minimal.
- **Verification Method:** Architectural inspection proving total absence of motor control drivers in the EON code tree.
