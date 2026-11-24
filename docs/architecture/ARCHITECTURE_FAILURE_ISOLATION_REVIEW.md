# OVIC EON — Architecture Failure Isolation Review Specification

**Document ID:** `EON-REV-FAIL-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.20)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Safety Engineers, Systems Architects, SREs  
**Traceability:** `EON-ARCH-CORE-001`, SRS-SAFE-001, ADR-028, ADR-014  

---

## 1. Failure Scenarios and Containment Boundaries

This review defines eighteen deterministic failure scenarios across system boundaries, documenting triggers, detection, containment, degraded modes, and recovery mechanisms:

| Failure ID | Trigger Event | Detection Mechanism | Containment Boundary | Expected Degraded Mode | Recovery Mechanism | Safety Implications |
|---|---|---|---|---|---|---|
| **FAIL-01** | ERS Neural Model Segmentation Fault | SIGSEGV caught by worker sandbox | Worker Subprocess Sandbox | ERS enters `FAULTED`; HBU posture & voice prosody continue | Worker restarted by supervisor after 2s delay | Zero; non-authoritative output drops to neutral |
| **FAIL-02** | Camera Sensor Hardware Cable Disconnection | V4L2 `ioctl` returns `EIO` / zero frames | Sensor Driver / RAL | ERS transitions to `DEGRADED`; runs audio-only emotion analysis | Auto-reconnect loop at 1 Hz; log warning | Zero; motion proposals remain valid |
| **FAIL-03** | Microphone Array USB Bus Reset | ALSA read returns `EPIPE` (Buffer Overrun) | Audio Ingress Pipeline | ERS transitions to `DEGRADED`; runs vision-only emotion analysis | ALSA device reopened with backoff | Zero; visual gaze tracking continues |
| **FAIL-04** | Core Event Ingress Queue Flooding | High-frequency perception burst | Bounded queue threshold check | Queue executes `DROP_OLDEST` policy | Ingress rate throttle applied | Zero; freshest frames prioritized |
| **FAIL-05** | Shared Memory Segment Deadlock | Host process ungracefully terminated | IPC handshake timeout (500 ms) | Kernel POSIX SHM segment | Re-map segment and reset atomic slot locks | Zero; client receives `EON_ERR_TIMEOUT` |
| **FAIL-06** | Context SQLite Database File Corruption | SQLite `SQLITE_CORRUPT` error | Transaction rollback handler | Local Storage Manager | Restore from atomic snapshot (`context.db.backup`) | Context lost for active session; zero physical risk |
| **FAIL-07** | Abrupt Power Loss (Robot Battery Pull) | Hardware power cut (instant 0V) | Kernel power management | dm-crypt / SQLite WAL | Database replays WAL on boot; discard uncommitted RAM | Clean reboot; zero hardware damage |
| **FAIL-08** | Memory Saturation (Edge OOM Risk) | Memory exceeds `MemoryHigh` (1800MB) | cgroups v2 kernel notification | EON Daemon Process | Flush volatile caches; downsample vision to 5 FPS | Prevents kernel OOM killing robot navigation |
| **FAIL-09** | CPU Thermal Throttling | SoC temperature $\gt 85^\circ\text{C}$ | Thermal sysfs monitor | Model Runtime Schedulers | Switch to INT8 quantized fallback CPU models | Reduces thermal load; robot stays active |
| **FAIL-10** | ROS 2 DDS Network Partition | WiFi disconnected from ROS base | Liveliness lease expiration | `eon_ros2_bridge` | Bridge buffers proposals locally; diagnostics to `WARN` | Robot navigation stays local; zero risk |
| **FAIL-11** | C++ SDK Host Process Deadlock | User callback blocks worker thread | Thread pool watchdog timeout | Client SDK ThreadPool | Cancel inflight task; flag client state `DEGRADED` | Core daemon remains completely unaffected |
| **FAIL-12** | Cloud API Gateway Outage | TLS connection refused on port 443 | Sync Agent HTTP client | Cloud Sync Agent | Buffer events in local SQLite outbox queue | Edge robot operates with 100% autonomy |
| **FAIL-13** | Subject Encryption Key Deletion (Purge) | User issues Right to be Forgotten | Consent Management API | Crypto Engine | Ciphertext rendered mathematically unrecoverable | Verified compliance; zero data leak |
| **FAIL-14** | Robot Safety Arbiter Emergency Stop | Operator presses physical E-Stop button | Safety HAL status pin | Robot Safety Hardware | All EON motion proposals immediately vetoed | Physical power to motors cut by hardware relay |
| **FAIL-15** | Systemd Daemon Watchdog Timeout | Event bus loop frozen for $\gt 5.0\text{s}$ | systemd watchdog ping missed | systemd process supervisor | systemd terminates `eond` with SIGABRT and restarts | Robot social expression pauses safely |
| **FAIL-16** | Invalid Motion Trajectory Proposal | Bug in ERG generates extreme velocity | RAL Proposal Formatter | RAL / Safety Gate | Clamped to max velocity envelope ($1.0\text{ rad/s}$) | Dangerous motion prevented before reaching motors |
| **FAIL-17** | Corrupted Model ONNX Checksum | Tampered model file on disk | SHA-256 hash check at startup | Model Loader Subsystem | Refuse load; enter `FAULTED`; alert operator | Prevents execution of unvetted neural weights |
| **FAIL-18** | Multi-Robot DDS Topic Collision | Identical robot ID assigned to two robots | SROS 2 certificate validation | SROS 2 Security Enclave | Connection dropped due to duplicate cert CN | Prevents cross-robot command confusion |
