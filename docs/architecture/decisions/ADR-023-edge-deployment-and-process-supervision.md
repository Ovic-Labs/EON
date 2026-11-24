# ADR-023: Edge Deployment Architecture and Process Supervision

**Document ID:** `EON-ADR-023`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Edge Computing, Operating System Integration, Process Supervision  

---

## 1. Context and Problem Statement

Robots run on resource-constrained embedded computers with limited RAM, CPU quotas, and strict thermal envelopes. Emotional intelligence processes must not induce kernel Out-Of-Memory (OOM) conditions or starve safety-critical navigation routines.

## 2. Decision

We decide to architect a deterministic Edge Deployment and Supervision model:
1. **CPU-First Baseline:** The entire system executes deterministically on x86_64 and ARM64 CPUs with documented INT8/FP16 ONNX models. Optional GPU/NPU acceleration via modular execution providers.
2. **Cgroups v2 Resource Partitioning:** Enforces strict memory caps (`MemoryMax`) and CPU quotas (`CPUQuota`) in the `systemd` service descriptor.
3. **Hardware & Software Watchdogs:** 2-second `systemd` watchdog petting with automatic restart on deadlock; OOM score adjustment (`OOMScoreAdjust=-500`) protecting the core daemon.
4. **Atomic A/B Updates:** Dual-slot bootloader partitioning with automatic 3-strike boot rollback.

## 3. Alternatives Considered

- *Alternative A: Mandatory GPU Execution.* Rejected: Excludes low-power embedded robotics SBCs (Intel Core Ultra, ARM64).
- *Alternative B: Unconstrained Background Process.* Rejected: High risk of robot freeze during heavy vision bursts.

## 4. Consequences and Implications

- **Positive:** Predictable resource footprint, deterministic failure containment, and field resilience.
- **Negative:** Requires strict model quantization to fit into 2GB low-resource memory budgets.
- **Security Implications:** Systemd sandboxing (`ProtectSystem=strict`, `NoNewPrivileges=true`).
- **Privacy Implications:** Encrypted SQLite local storage with per-subject DEKs.
- **Performance Implications:** CPU inference throughput matches deployment profile budgets.
- **Related ADRs:** ADR-006, ADR-010, ADR-012, ADR-017.
- **Supersession History:** None.
