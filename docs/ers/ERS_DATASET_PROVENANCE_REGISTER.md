# ERS Dataset Provenance & Commercial Licensing Register — Phase 3.1.4

**Project:** OVIC EON — Emotional Intelligence Infrastructure for Robotics  
**Organization:** OVIC Labs  
**Component:** ERS (Emotion Recognition System)  
**Standard:** Legal Provenance, Licensing Audit & Redistribution Policy  
**Date:** 2026-11-24  

---

## 1. Overview

In accordance with Phase 3.1.4 requirements, this register catalogs all machine learning datasets referenced, evaluated, or planned for OVIC EON ERS. It audits original source publications, software/data licenses, commercial derivation permissions, and redistribution constraints.

---

## 2. Benchmark Datasets Register

### 2.1 AffectNet
- **Dataset Identifier:** `affectnet-v1`
- **Origin / Authors:** Ali Mollahosseini, Behzad Hasani, Mohammad H. Mahoor (University of Denver)
- **Publication:** IEEE Transactions on Affective Computing (IEEE TAC), 2017
- **Acquisition URL:** http://mohammadmahoor.com/affectnet/
- **License Type:** Academic / Non-Commercial Research Use Only
- **Commercial Use Allowed:** **NO (STRICTLY PROHIBITED)**
- **Redistribution Allowed:** **NO (Direct download from authors only)**
- **Checksum / Digest:** `sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (Catalog Entry)
- **Operational Classification:** Research Benchmark Only. Models trained on AffectNet may not be deployed in commercial robotics systems without explicit commercial licensing.

### 2.2 RAF-DB (Real-world Affective Faces Database)
- **Dataset Identifier:** `raf-db-v1`
- **Origin / Authors:** Shan Li, Weihong Deng, JunPing Du (Beijing University of Posts and Telecommunications)
- **Publication:** IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2017
- **Acquisition URL:** http://www.whdeng.cn/RAF/model1.html
- **License Type:** Academic / Non-Commercial Research License
- **Commercial Use Allowed:** **NO (STRICTLY PROHIBITED)**
- **Redistribution Allowed:** **NO (Requires signed institutional agreement)**
- **Operational Classification:** Research Benchmark Only.

### 2.3 RAVDESS (Ryerson Audio-Visual Database of Emotional Speech and Song)
- **Dataset Identifier:** `ravdess-v1`
- **Origin / Authors:** Steven R. Livingstone, Frank A. Russo (Ryerson University)
- **Publication:** PLOS ONE, 2018
- **Acquisition URL:** https://zenodo.org/record/1188976
- **License Type:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)
- **Commercial Use Allowed:** **NO (STRICTLY PROHIBITED)**
- **Redistribution Allowed:** **YES (With attribution and ShareAlike constraints)**
- **Actors / Subjects:** 24 professional actors (12 female, 12 male)
- **Operational Classification:** Acoustic Research & Prosody Evaluation Benchmark.

### 2.4 CREMA-D (Crowd-sourced Emotional Multimodal Actors Dataset)
- **Dataset Identifier:** `crema-d-v1`
- **Origin / Authors:** Houwei Cao, David G. Cooper, Michael K. Keutmann, et al.
- **Publication:** IEEE Transactions on Affective Computing (IEEE TAC), 2014
- **Acquisition URL:** https://github.com/CheyneyComputerScience/CREMA-D
- **License Type:** Open Database License (ODbL) / Research License
- **Commercial Use Allowed:** **NO (Requires explicit commercial release)**
- **Redistribution Allowed:** **YES (Open access with attribution)**
- **Actors / Subjects:** 91 multicultural actors
- **Operational Classification:** Multimodal Audio-Visual Acoustic Benchmark.

---

## 3. Commercial Gating and Compliance Policy

OVIC Labs enforces a strict binary gating policy regarding dataset licensing:

1. **Commercial Clearance Invariant:** No model weights derived from datasets with `commercial_allowed = False` may be validated as `commercial_use_allowed = True` in any `ModelValidationRecord` or `ModelManifest`.
2. **Current Repository Baseline Status:**
   - Current baseline models (`facial_emotion_model.onnx`, `speech_emotion_model.onnx`) utilize synthetic graph initializations for pipeline execution and integration testing.
   - Empirical affective datasets have not been incorporated into production weights.
   - Commercial qualification status is strictly marked as:
     $$\text{commercial\_use\_status} = \mathbf{RESTRICTED}$$
3. **Future Production Training:** Commercial qualification requires proprietary in-house datasets collected under verified participant consent agreements, or fully cleared commercial datasets (e.g. Apache-2.0 or commercial enterprise licensing).
