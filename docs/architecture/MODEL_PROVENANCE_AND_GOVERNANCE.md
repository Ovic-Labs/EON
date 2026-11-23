# OVIC EON — Model Provenance and Governance Policy

**Document ID:** `EON-POL-MOD-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.7 — Design Model Adapter Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/MODEL_ADAPTER_ARCHITECTURE.md` (`EON-ARCH-MOD-001`)
- `docs/research/phase-1/models.yaml`

---

## 1. Executive Summary

This policy establishes the mandatory metadata, provenance tracking, and intellectual property due-diligence required for every model artifact deployed in OVIC EON.

---

## 2. Mandatory Model Metadata Record

Every model in `models.yaml` must define the following schema fields:

```yaml
model_id: "qwen2.5-1.5b-instruct-q4_k_m"
canonical_name: "Qwen2.5-1.5B-Instruct"
task: "surface_dialogue_nlg"
version: "1.5.0"
provider: "Alibaba Cloud / Qwen Team"
license: "Apache-2.0"
commercial_use_approved: true
checksum_sha256: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
source_url: "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF"
runtime_compatibility: ["llama.cpp", "cpu_simd"]
hardware_budget:
  min_ram_mb: 1200
  recommended_threads: 2
known_limitations: "Max context 4096 tokens; hallucination risk on clinical queries"
evaluation_status: "BENCHMARKED_LOCAL_REP"
```

> **Licensing Invariant:** A permissive package license (e.g. Apache 2.0 wrapper) does **not** grant commercial rights if the underlying model weights or training datasets contain Non-Commercial clauses (`CC BY-NC`). Every weight checkpoint is audited independently.
