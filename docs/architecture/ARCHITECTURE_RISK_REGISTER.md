# OVIC EON — Architecture Risk Register

**Document ID:** `EON-REG-RISK-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Engineering Leadership, Risk Managers, Robotics Safety Officers  
**Traceability:** `EON-ARCH-CORE-001`, ADR-028  

---

## 1. Systemic Architecture Risk Register

This register documents key architectural risks identified across Phase 2, assessing their impact, probability, mitigation strategies, and residual severity:

| Risk ID | Risk Category | Risk Description | Probability | Impact | Mitigation Strategy | Residual Risk |
|---|---|---|---|---|---|---|
| **RSK-01** | Hardware / Memory | Low-cost ARM edge SBCs (e.g., 4GB SBCs) experience memory exhaustion under peak multimodal inference loads. | High | High | Low-Resource profile mandates INT8 quantized models, 2GB cgroups hard cap, and 10 FPS vision throttling. | Medium |
| **RSK-02** | Latency / GIL | Python SDK consumers experience latency jitter in high-frequency event callbacks due to Python GIL lock contention. | Medium | Medium | C++ SDK (`libeonsdk`) provided as first-class high-performance client; Python utilizes non-blocking async loops. | Low |
| **RSK-03** | Real-World Affect Accuracy | Facial expressions in natural environments exhibit extreme lighting, partial occlusions, and cultural variances. | High | Medium | Invariant: Inferences are marked as uncertain observations (`is_definitive_claim=false`), backed by multi-modal fusion. | Low |
| **RSK-04** | Hardware Wear-Leveling | Modern SSD Flash Translation Layers prevent guaranteed physical flash sector zeroing upon data purge. | Certain (100%) | High | Cryptographic shredding via per-subject AES-256 DEK destruction; plaintext data rendered mathematically undecipherable. | Low |
| **RSK-05** | Safety Controller Override | Downstream robot integrators accidentally map EON motion proposals directly to motor drives without safety checking. | Low | Critical | Proposals are stamped immutable `is_authoritative = false`; integration documentation strictly forbids direct driver mapping. | Low |
| **RSK-06** | Upstream Dependency Supply Chain | Vulnerability in third-party neural runtimes (e.g., ONNX Runtime CVE) exposed on edge compute. | Medium | High | Automated SBOM generation (CycloneDX), Dependabot vulnerability scanning, and sandboxed subprocess execution. | Low |
| **RSK-07** | Wireless Network Drops in Cloud Sync | Extended robot operation in Wi-Fi blackouts causes sync queue buffer overflow. | High | Low | Local store-and-forward SQLite queue with ring buffer drop of non-critical telemetry; 100% offline edge autonomy. | Low |
| **RSK-08** | Inter-Engine Deadlock | Circular event waiting between EMS (Emotion Modelling) and ERE (Empathy Reasoning). | Low | High | Strict unidirectional acyclic event flow hierarchy; engines never block waiting for synchronous peer responses. | Negligible |
