# OVIC EON — Robot Sensor Abstraction Specification

**Document ID:** `EON-SPEC-ROB-004`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.13)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Perception Engineers, Computer Vision Engineers  
**Traceability:** `EON-ARCH-ROB-001`, ADR-022  

---

## 1. Perceptual Modality Abstraction

The RAL normalizes diverse physical sensor configurations into consistent perception representations:

1. **Visual Streams:**
   - Ingests monocular RGB, stereo RGB, RGB-D, or wide-angle fisheye cameras.
   - Normalizes all streams to standard sRGB color space, planar or interleaved formats, and extracts 2D bounding boxes and facial landmarks.
   - Zero-copy ring buffer storage ensures no frame copies during preprocessing.
2. **Acoustic Streams:**
   - Ingests microphone arrays, USB audio interfaces, or network RTP streams.
   - Standardizes audio into single-channel 16 kHz, 16-bit signed PCM audio buffers with 20 ms chunk duration.
   - Performs beamforming and acoustic echo cancellation (AEC) abstraction prior to emotion analysis.
3. **Spatial Kinematics and Odometry:**
   - Normalizes robot base velocities and head joint angles relative to the robot's base coordinate frame (`base_link`).
   - Ensures social gaze estimation compensates for the robot's own body motion.
