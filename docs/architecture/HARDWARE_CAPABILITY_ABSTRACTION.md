# OVIC EON — Hardware Capability Abstraction Specification

**Document ID:** `EON-SPEC-MOD-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design  
**Sub-phase:** 2.7 — Design Model Adapter Architecture  
**Status:** Approved Engineering Architecture Specification  
**Version:** 1.0.0  
**Classification:** Technical Architecture Specification  
**Document Owner:** Principal Software Architect  
**Related Documents:**
- `docs/architecture/MODEL_ADAPTER_ARCHITECTURE.md` (`EON-ARCH-MOD-001`)

---

## 1. Executive Summary

This specification establishes the hardware discovery mechanisms used by EON Core to detect processor capabilities, available RAM, and optional NPU/GPU accelerators at startup.

---

## 2. Hardware Detection Sequence

```text
1. Inspect CPU Architecture (x86_64 vs aarch64)
2. Probe Vector Extensions (AVX2, AVX-512, ARM NEON, ARM FP16)
3. Check Available Physical RAM (Verify >= 1800 MB available for Tier 1)
4. Probe Device Nodes:
   - Check /dev/rknpu (Rockchip NPU detected)
   - Check /dev/nvhost-ctrl (NVIDIA Tegra/Jetson detected)
5. Select Optimal Execution Provider (Default: CPU-First)
```

**Thermal & Throttling Guard:** If CPU temperature exceeds $80^\circ\text{C}$ or throttling is detected via `/sys/devices/system/cpu/`, the adapter switches high-rate vision from 30 fps to 15 fps to shed thermal load.
