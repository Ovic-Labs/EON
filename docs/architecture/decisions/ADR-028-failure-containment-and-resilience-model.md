# ADR-028: Failure Containment and Resilience Model

**Document ID:** `EON-ADR-028`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Systems Reliability, Fault Tolerance, Failure Containment  

---

## 1. Context and Problem Statement

Robots are physical systems operating in dynamic real-world environments. Unhandled software crashes, memory exhaustion, or network partitions in emotional intelligence pipelines must never compromise the physical safety of the robot or surrounding humans.

## 2. Decision

We decide to mandate a comprehensive **Failure Containment and Resilience Model**:
1. **Fail-Silent Robotics Contract:** In the event of an EON failure, the robot times out and gently returns expressive actuators to neutral holding postures without jerky motions or navigation halts.
2. **Priority-Lane Ingress Drops:** Bounded circular queues drop oldest perceptual frames (`DROP_OLDEST`) under saturation, ensuring low-latency safety signals are never blocked.
3. **Engine Crash Isolation:** Each of the seven intelligence engines executes in isolated worker threads or sub-processes; a crash in ERS or SIE transitions that engine to `FAULTED` without bringing down the core event bus.
4. **Hardware Watchdog Integration:** Automated systemd and micro-controller watchdogs pet heartbeat signals every 2.0 seconds with automated restart limits.

## 3. Alternatives Considered

- *Alternative A: Fail-Stop Emergency Robot E-Stop.* Rejected: Emotion engine crashes should not cause abrupt, hazardous emergency stops of moving 100kg mobile robots.
- *Alternative B: Unbounded Ingress Buffering.* Rejected: Triggers out-of-memory kernel panics under perception bursts.

## 4. Consequences and Implications

- **Positive:** Bounded memory, predictable failure modes, fail-silent social behavior.
- **Negative:** Non-critical observation frames are dropped during severe CPU contention.
- **Security Implications:** Resists denial-of-service queue exhaustion attacks.
- **Privacy Implications:** Volatile memory dropped during failure contains zero persisted residue.
- **Performance Implications:** High-frequency event throughput remains stable under edge loads.
- **Related ADRs:** ADR-012, ADR-014, ADR-021, ADR-022, ADR-023.
- **Supersession History:** None.
