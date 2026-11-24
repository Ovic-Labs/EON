# OVIC EON — Privacy Media Processing Specification

**Document ID:** `EON-SPEC-PRIV-006`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.17)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Computer Vision Engineers, Audio Signal Processing Engineers  
**Traceability:** `EON-ARCH-PRIV-001`, ADR-026  

---

## 1. Volatile In-Memory Ring Buffer Pipeline

To guarantee that camera and microphone data cannot be recovered by forensic disk inspection:
1. **POSIX Shared Memory (`/dev/shm`):** Mounted exclusively as a `tmpfs` RAM filesystem. No swap file backing is permitted.
2. **Fixed Circular Capacity:** Visual frame buffers hold at most 3 consecutive frames ($< 100\text{ ms}$ buffer window). New incoming camera frames overwrite older memory slots in place.
3. **Acoustic Audio Buffers:** Audio buffers hold at most 500 ms of 16 kHz PCM data. Feature extraction computes mel-frequency cepstral coefficients (MFCCs) and prosodic contours directly in memory, discarding raw audio samples immediately upon feature extraction.

---

## 2. Hardware Video Stream Safeguards

- **No Local DVR Recording:** The robot software stack is prohibited from recording continuous MP4/AVI video files to disk unless an explicit, independent safety recording mode is physically signaled by the robot hardware.
- **Microphone LED Indicator:** Integration guidelines require host robots to activate a physical hardware LED indicator whenever the microphone or camera stream is active, providing clear physical transparency to bystanders.
