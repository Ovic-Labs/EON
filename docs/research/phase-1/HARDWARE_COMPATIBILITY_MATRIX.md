# OVIC EON — Master Hardware Compatibility Matrix

**Project:** OVIC EON
**Document ID:** `EON-RES-HW-001`
**Phase:** Phase 1 — Technical Research and Feasibility
**Classification:** Hardware Platform Compatibility & Benchmark Register
**Version:** 1.0.0
**Status:** Approved

---

## 1. Scope and Tier Definitions

This matrix evaluates real-world robotics edge computing platforms against OVIC EON's seven intelligence engines.

Hardware Tiers:
- **Tier 1 (Basic CPU):** Entry-level ARM/x86 single-board computers ($4\text{--}8\text{ GB}$ RAM, $5\text{--}15\text{ W}$). Template-based response generation only.
- **Tier 2 (Recommended CPU):** Mainstream multicore mobile/desktop edge CPUs ($16\text{ GB}$ RAM, $15\text{--}45\text{ W}$). Supports local Qwen2.5-1.5B SLM and full neural perception.
- **Tier 3 (Accelerated Edge):** Multicore CPU + integrated NPU or low-power edge GPU ($16\text{--}32\text{ GB}$ RAM, $25\text{--}65\text{ W}$).
- **Tier 4 (High-Performance Robotics):** Workstation CPU + discrete robotics GPU ($32\text{--}64\text{ GB}$ RAM, $50\text{--}150\text{ W}$).

---

## 2. Platform Compatibility and Engine Support Matrix

| Platform ID | Hardware Platform & Processor | Architecture | Memory & Bus | Tier | Perception (ERS/HBU) | Memory & Cognition (EMS/ERE/PSE) | Social Engine (SIE) | SLM Response Gen (ERG) | TTS Voice (ERG) | Verdict & Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| `HW-01` | **Raspberry Pi 5**<br>Broadcom BCM2712 (4x A76 @ 2.4GHz) | ARM64 (NEON) | 8GB LPDDR4X (Single/Dual 32-bit) | **Tier 1** | MediaPipe ($15\text{ FPS}$) [REP] | SQLite + Rules ($<1\text{ ms}$) [REP] | HFSM + VAD ($<2\text{ ms}$) [REP] | **Templates Only** ($<5\text{ ms}$)<br>SLM disabled [EST] | Piper Medium (RTF 0.12) [REP] | **FEASIBLE (Tier 1 Baseline).** Operates cleanly with deterministic templates. |
| `HW-02` | **Rockchip RK3588**<br>(4x A76 @ 2.4GHz + 4x A55 @ 1.8GHz, 6 TOPS NPU) | ARM64 (NEON, I8MM, NPU) | 16GB LPDDR4X (128-bit bus) | **Tier 2/3** | MediaPipe ($30\text{ FPS}$ CPU)<br>RKNN NPU [REP] | Qdrant + MiniLM ($<6\text{ ms}$) [REP] | Full HFSM + TRP ($<1.5\text{ ms}$) [REP] | Qwen2.5-1.5B ($16.5\text{ tok/s}$ CPU)<br>RKLLM ($22\text{ tok/s}$) [REP] | Piper Medium (RTF 0.05) [REP] | **FEASIBLE.** Outstanding price/performance for embedded robotics. |
| `HW-03` | **Intel Core i5-1240P**<br>(4P + 8E cores, 16 threads, Iris Xe 80EU) | x86_64 (AVX2, VNNI) | 16GB Dual-Channel DDR4-3200 | **Tier 2** | Full Multimodal ($30\text{ FPS}$) [REP] | Qdrant + MiniLM ($<4.5\text{ ms}$) [REP] | Full HFSM + TRP ($<1.2\text{ ms}$) [REP] | Qwen2.5-1.5B ($24.0\text{ tok/s}$ CPU) [REP] | Piper Medium (RTF 0.04) [REP] | **FEASIBLE (Standard Target).** Clean CPU-only operation. |
| `HW-04` | **Intel Core Ultra 5 225U**<br>(2P + 8E + 2LP cores, 14 threads, Intel NPU) | x86_64 (AVX2, VNNI, OpenVINO) | 16GB Dual-Channel LPDDR5-6400 | **Tier 2/3** | Full Multimodal ($30\text{ FPS}$ CPU/iGPU) [REP] | Qdrant + MiniLM ($<4.0\text{ ms}$) [REP] | Full HFSM + TRP ($<1.0\text{ ms}$) [REP] | Qwen2.5-1.5B ($28.5\text{ tok/s}$ CPU) [REP] | Piper Medium (RTF 0.035) [REP] | **FEASIBLE.** Owner's machine. High memory bandwidth gives fast token streaming. |
| `HW-05` | **AMD Ryzen 7 7840U / 8840U**<br>(8 cores / 16 threads Zen 4, Radeon 780M) | x86_64 (AVX-512, VNNI, Vulkan) | 32GB Dual-Channel LPDDR5x-7500 | **Tier 2/3** | Full Multimodal ($60\text{ FPS}$ CPU/Vulkan) [REP] | Qdrant + MiniLM ($<3.2\text{ ms}$) [REP] | Full HFSM + TRP ($<0.8\text{ ms}$) [REP] | Qwen2.5-1.5B ($38.0\text{ tok/s}$ CPU/AVX-512) [REP] | Piper Medium (RTF 0.025) [REP] | **FEASIBLE (Top Performer).** AVX-512 delivers remarkable CPU inference. |
| `HW-06` | **NVIDIA Jetson Orin Nano**<br>(6-core ARM A78AE, Ampere 1024 CUDA, 40 TOPS) | ARM64 + CUDA Unified Memory | 8GB 128-bit LPDDR5 | **Tier 3** | Full Multimodal ($60\text{ FPS}$ TensorRT) [REP] | Qdrant + MiniLM ($<3.0\text{ ms}$) [REP] | Full HFSM + TRP ($<1.0\text{ ms}$) [REP] | Qwen2.5-1.5B ($32.0\text{ tok/s}$ cuBLAS) [REP] | Piper Medium (RTF 0.03) [REP] | **FEASIBLE (Accelerated).** 8GB unified RAM requires careful KV-cache limits. |
| `HW-07` | **NVIDIA Jetson AGX Orin**<br>(12-core ARM A78AE, 2048 CUDA, 275 TOPS) | ARM64 + CUDA Unified Memory | 32GB / 64GB 256-bit LPDDR5 | **Tier 4** | Panoramic Multi-Camera ($120\text{ FPS}$ TRT) [PUB] | High-context Qdrant ($<1.5\text{ ms}$) [REP] | Multi-Person Social ($<0.5\text{ ms}$) [REP] | Qwen2.5-7B ($35.0\text{ tok/s}$ TRT-LLM) [PUB] | Real-time multi-voice [PUB] | **FEASIBLE (Tier 4 Enterprise).** Capable of multi-person commercial robotics. |

---

## 3. Acceleration Framework and Operator Coverage

| Runtime Engine | Primary Hardware Target | Supported EON Models | Unsupported Ops / Gotchas | CPU Fallback Status | Recommended Production Use |
|---|---|---|---|---|---|
| **ONNX Runtime (CPU)** | Universal x86_64 & ARM64 | Face Mesh, HSEmotion, Silero VAD, MiniLM, RTMPose | None (100% standard operator support) | Native Baseline | **MANDATORY BASELINE** |
| **llama.cpp (CPU)** | Universal x86_64 & ARM64 | Qwen2.5 (0.5B, 1.5B, 3B, 7B), Phi-3.5, Llama-3.2 | None (Optimized AVX2, AVX-512, NEON) | Native Baseline | **MANDATORY BASELINE** |
| **OpenVINO (NPU)** | Intel Core Ultra (Meteor Lake) | HSEmotion, all-MiniLM-L6-v2 | Autoregressive dynamic KV-cache in LLMs | Automatic fallback to CPU | **OPTIONAL (Vision/Embeddings)** |
| **Qualcomm QNN** | Snapdragon X Elite / RB5 | MobileNetV2, Silero VAD, Whisper encoder | GGUF dynamic tensors require QNN graph compilation | Fallback to CPU | **OPTIONAL (Future ARM Tier 3)** |
| **TensorRT / cuBLAS** | NVIDIA Jetson / Mobile RTX | All vision, audio, and language models | None (Requires CUDA 12.x driver stack) | Automatic fallback to CPU | **OPTIONAL ACCELERATOR** |
| **Vulkan Compute** | AMD Radeon / Intel Arc / Mali | `llama.cpp` Vulkan, ncnn vision | Shader compilation warmup latency on cold start | Fallback to CPU | **OPTIONAL CROSS-PLATFORM** |
