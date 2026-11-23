# OVIC EON — Master Licensing Compliance Matrix

**Project:** OVIC EON
**Document ID:** `EON-RES-LIC-001`
**Phase:** Phase 1 — Technical Research and Feasibility
**Classification:** Comprehensive Commercial Licensing & Intellectual Property Matrix
**Version:** 1.0.0
**Status:** Approved

---

## 1. Overview and Scope

This document provides the authoritative compliance register for all machine-learning model weights, datasets, speech voices, software runtimes, and algorithmic components evaluated in Sub-phases 1.12 and 1.13.

Every asset is categorized into one of six legal status levels:
- `APPROVED`: Fully cleared for commercial distribution without royalties.
- `APPROVED WITH CONDITIONS`: Cleared subject to specific legal covenants (attribution notices, terms of use compliance).
- `RESEARCH ONLY`: Restricted to internal offline benchmarking; prohibited from runtime shipping.
- `QUARANTINED`: Suspended from builds pending further provenance verification.
- `REJECTED`: Incompatible with commercial distribution.
- `UNKNOWN`: Insufficient evidence to establish legal clearance.

---

## 2. Model and Weight Checkpoint Compliance Register

| Asset ID | Asset Name & Checkpoint | Sub-phase | Repository / Origin | Code License | Weight / Binary License | Training Data Provenance | Commercial Status | Required Conditions / Restrictions |
|---|---|---|---|---|---|---|---|---|
| `LIC-MOD-01` | **MediaPipe Face Mesh** (`face_landmarker.task`) | 1.12 | Google MediaPipe | Apache-2.0 | Apache-2.0 | Consented internal Google | **APPROVED** | Retain standard Apache 2.0 notice. |
| `LIC-MOD-02` | **MediaPipe Hands & Pose** (`pose_landmarker_lite.task`) | 1.12 | Google MediaPipe | Apache-2.0 | Apache-2.0 | Consented internal Google | **APPROVED** | Retain standard Apache 2.0 notice. |
| `LIC-MOD-03` | **HSEmotion** (`enet_b0_8_va_mtl.onnx`) | 1.12 | HSE-asavchenko | Apache-2.0 | Apache-2.0 | AffectNet / Synthetic | **APPROVED WITH CONDITIONS** | Include author copyright notice; verify downstream AffectNet commercial terms. |
| `LIC-MOD-04` | **Silero VAD** (`silero_vad.onnx`) | 1.12 | Snakers4 | MIT | MIT | Synthetic / Public Domain | **APPROVED** | Include MIT attribution banner in notice file. |
| `LIC-MOD-05` | **SpeechBrain ECAPA-TDNN** (`ecapa-tdnn.onnx`) | 1.12 | SpeechBrain | Apache-2.0 | Apache-2.0 | Common Voice 11.0 | **APPROVED WITH CONDITIONS** | Must use Common Voice checkpoint; VoxCeleb-derived checkpoint is quarantined. |
| `LIC-MOD-06` | **all-MiniLM-L6-v2** (`model_qint8.onnx`) | 1.12 | Sentence-Transformers | Apache-2.0 | Apache-2.0 | 1B sentence pairs (Reddit, S2ORC) | **APPROVED** | Standard Apache 2.0 attribution. |
| `LIC-MOD-07` | **Qwen2.5-1.5B-Instruct** (`qwen2.5-1.5b-instruct-q4_k_m.gguf`) | 1.12 | Alibaba QwenLM | Apache-2.0 | Apache-2.0 | Multi-trillion token web corpus | **APPROVED** | Fully permissive. Commercial use and redistribution approved. |
| `LIC-MOD-08` | **Qwen2.5-0.5B-Instruct** (`qwen2.5-0.5b-instruct-q4_k_m.gguf`) | 1.12 | Alibaba QwenLM | Apache-2.0 | Apache-2.0 | Multi-trillion token web corpus | **APPROVED** | Fully permissive edge fallback. |
| `LIC-MOD-09` | **Phi-3.5-mini-instruct** (`Phi-3.5-mini-instruct-Q4_K_M.gguf`) | 1.12 | Microsoft | MIT | MIT | Synthetic & filtered web | **APPROVED** | Standard MIT attribution. |
| `LIC-MOD-10` | **Gemma-2-2B-it** (`gemma-2-2b-it-Q4_K_M.gguf`) | 1.12 | Google | Apache-2.0 | Gemma Terms of Use | Google web corpus | **APPROVED WITH CONDITIONS** | Adhere to Google Prohibited Use Policy and attribution clauses. |
| `LIC-MOD-11` | **Llama-3.2-1B-Instruct** (`llama-3.2-1b-instruct-q4_k_m.gguf`) | 1.12 | Meta AI | Custom Meta | Llama 3.2 Community | Meta web corpus | **APPROVED WITH CONDITIONS** | Requires "Built with Llama" notice; $<700\text{M}$ monthly active user restriction. |
| `LIC-MOD-12` | **Piper TTS Engine** (`piper` C++ binary) | 1.12 | Rhasspy | MIT | MIT | N/A (Software) | **APPROVED** | Include MIT attribution in software release. |
| `LIC-MOD-13` | **Piper Voice: en_US-lessac-medium** (`.onnx`) | 1.12 | Rhasspy | MIT | Public Domain / CC0 | LibriTTS Paula Lessac | **APPROVED** | Fully unencumbered public domain voice model. |
| `LIC-MOD-14` | **Piper Voice: en_GB-alan-low** (`.onnx`) | 1.12 | Rhasspy | MIT | MIT | Alan speech corpus | **APPROVED** | Permissive MIT voice model. |
| `LIC-MOD-15` | **OpenFace 2.0** (`cen_patches.dat`) | 1.12 | TadasBaltrusaitis | Custom Academic | Custom Non-Comm | Multi-PIE, LFW | **REJECTED** | Non-commercial clause in legacy dependencies and datasets. |
| `LIC-MOD-16` | **Coqui XTTS-v2** (`model.pth`) | 1.12 | Coqui AI | MPL-2.0 | CPML (Non-Commercial) | Proprietary multi-speaker | **REJECTED** | Coqui Public Model License explicitly forbids commercial exploitation. |
| `LIC-MOD-17` | **OpenPose Body 25** (`pose_iter_584000.caffemodel`) | 1.12 | CMU | Custom Dual | Commercial Fee (\$25k) | CMU Panoptic | **REJECTED** | Prohibitive commercial license fee. |

---

## 3. Dataset Compliance Register

| Asset ID | Dataset Name | Modality | Primary Use Case | Official License | Commercial Use | Redistribution | Classification | Mandatory Compliance Action |
|---|---|---|---|---|---|---|---|---|
| `LIC-DAT-01` | **HaGRID** | Video / RGB Hand Gestures | Gesture Model Training | CC-BY-SA 4.0 | Allowed | Allowed with SA | **APPROVED WITH CONDITIONS** | Provide author attribution; release derived gesture models under compatible terms. |
| `LIC-DAT-02` | **LibriTTS-R** | Speech Audio (585 hrs) | TTS Voice Training | CC-BY 4.0 | Allowed | Allowed | **APPROVED** | Include LibriTTS-R citation in attribution notices. |
| `LIC-DAT-03` | **CREMA-D** | Audio / Video Emotional Clips | ERS Validation | ODbL 1.0 | Allowed | Allowed | **APPROVED WITH CONDITIONS** | Include Open Database License copyright notice. |
| `LIC-DAT-04` | **Common Voice** | Multi-speaker Audio | Audio Feature Training | CC0 / ODbL | Allowed | Allowed | **APPROVED WITH CONDITIONS** | Prohibited from attempting human speaker re-identification. |
| `LIC-DAT-05` | **RAVDESS** | Emotional Speech / Song | Benchmarking Only | CC-BY-NC-SA 4.0 | **NO** | Restricted | **RESEARCH ONLY** | Restricted to lab eval; strictly excluded from training commercial weights. |
| `LIC-DAT-06` | **SHREC'17** | 3D Depth Hand Landmarks | Gesture Benchmarking | Custom Academic | **NO** | Restricted | **RESEARCH ONLY** | Offline evaluation only. |
| `LIC-DAT-07` | **EmpatheticDialogues**| Emotional Dialogue Text | Dialogue Evaluation | CC-BY-NC 4.0 | **NO** | Restricted | **RESEARCH ONLY** | Excluded from training commercial SLMs; evaluation metric use only. |
| `LIC-DAT-08` | **20BN-Jester** | Video Gestures | Gestural Benchmark | Academic Non-Comm | **NO** | Closed | **REJECTED** | Commercial distribution strictly prohibited. |
| `LIC-DAT-09` | **IEMOCAP** | Speech / Motion Capture | Speech Emotion Benchmark | Academic Non-Comm | **NO** | Restricted | **RESEARCH ONLY** | Lab benchmarking only; weights trained on IEMOCAP are quarantined. |

---

## 4. Software Runtimes and Third-Party Dependencies

| Dependency | Category | Current Version | License Type | Commercial Suitability | Compliance Guidelines |
|---|---|---|---|---|---|
| **Python** | Language Runtime | 3.10 / 3.11 / 3.12 | PSF License 2.0 | **APPROVED** | Permissive, zero royalty. |
| **ONNX Runtime** | Neural Inference Engine | 1.17.x / 1.18.x | MIT License | **APPROVED** | Permissive, embedded deployment approved. |
| **llama.cpp** | SLM Inference Engine | b2600+ | MIT License | **APPROVED** | Permissive, compiled as static/shared library. |
| **SQLite / SQLCipher** | Relational Storage | 3.45.x / 4.5.x | Public Domain / BSD | **APPROVED** | Permissive, embedded database. |
| **Qdrant Embedded** | Vector Database Engine | 1.9.x | Apache-2.0 | **APPROVED** | Permissive, local embedded vector index. |
| **MediaPipe** | Computer Vision Library | 0.10.x | Apache-2.0 | **APPROVED** | Permissive, Google patent grant included. |
| **Piper TTS** | Speech Synthesis Runtime| 1.2.x | MIT License | **APPROVED** | Permissive C++ runtime. |
| **eSpeak NG** | Phonemizer / Fallback | 1.51 | GPL-3.0 | **QUARANTINED** | Must run as isolated CLI subprocess; library linking strictly prohibited. |

---

## 5. Explicit Quarantine and Rejection Roster

The following assets are **STRICTLY PROHIBITED** from inclusion in commercial OVIC EON runtime containers, wheel distributions, and model weight bundles until explicit legal clearance:

1. **Coqui XTTS-v2 (`model.pth`):** Governed by Coqui Public Model License (CPML), prohibiting commercial exploitation.
2. **OpenFace 2.0 Checkpoints (`cen_patches_*.dat`):** Includes non-commercial academic components and datasets.
3. **OpenPose Body 25 Caffe Models:** Subject to commercial licensing fees (\$25,000/year).
4. **Weights Derived Exclusively from RAVDESS or IEMOCAP:** Due to CC-BY-NC and USC academic restrictions.
5. **20BN-Jester Video Dataset:** Commercial rights revoked following acquisition.
6. **Direct Dynamic Linking against eSpeak NG (GPL-3.0):** Violates open-core proprietary plugin boundary; must use isolated process IPC or Piper phonemization.
