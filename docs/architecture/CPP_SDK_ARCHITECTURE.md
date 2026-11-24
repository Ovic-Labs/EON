# OVIC EON — C++ SDK Architecture Specification

**Document ID:** `EON-ARCH-CPP-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Software Engineers, C++ Systems Developers, Embedded AI Engineers  
**Traceability:** PRD Section 4.5, SRS-ARCH-010, ADR-020, ADR-014, ADR-013  
**Compatibility:** EON Core v0.1.0, Python SDK (`eon-sdk`), ROS 2 (Humble / Iron / Jazzy)

---

## 1. Executive Summary and Architectural Mission

The **OVIC EON C++ SDK** (`libeonsdk`) provides the native, high-performance, deterministic C++ client bindings for interacting with the OVIC EON emotional intelligence infrastructure. While the Python SDK (`eon-sdk`) serves rapid prototyping, research pipelines, and high-level behavioral scripting, robotic execution environments demand deterministic latency, minimal runtime overhead, strict memory boundedness, and native integration into robotic middleware stacks (notably ROS 2 nodes, DDS transports, and real-time motion controllers).

The C++ SDK is designed under five non-negotiable architectural mandates:
1. **CPU-First & Edge-First Determinism:** Bounded execution profiles operating without mandatory GPUs or cloud dependencies, fully capable of execution on x86_64 and ARM64 edge compute platforms.
2. **Zero-Copy Data Transfer:** Direct memory mapping and IPC shared-memory ring buffers for high-frequency perceptual observation ingestion (depth maps, audio frames, embeddings) without copying serialization payloads.
3. **RAII and Memory Safety:** Strict lifecycle management, eliminating raw pointer ownership, memory leaks, and unbounded queue allocations.
4. **Pimpl & C-ABI Stability:** Binary stability across compiler versions and seamless cross-language FFI interoperation with the Python runtime.
5. **Non-Authoritative Robotics Safety Boundary:** Enforcing the architectural rule that social intelligence outputs are non-authoritative (`is_authoritative_stop=False`). EON never directly writes to physical actuator hardware.

> [!IMPORTANT]
> **Implementation Status Notice:** This document establishes the complete architectural specification for the C++ SDK. In accordance with Phase 2 governance rules, this component is classified as **DESIGNED — NOT IMPLEMENTED**. No production C++ implementation or runtime benchmarking is claimed.

---

## 2. Layered Architecture and System Context

The C++ SDK resides between host robotic applications / middleware and the underlying EON runtime infrastructure:

```text
+--------------------------------------------------------------------------+
|                     Host Robotic Application Layer                       |
|   (ROS 2 Lifecycle Nodes, Custom C++ Robotics Software, Navigation)       |
+--------------------------------------------------------------------------+
                                    |
                                    v
+--------------------------------------------------------------------------+
|                       libeonsdk (Public C++17 API)                       |
|  [eon::client::EonClient]       [eon::events::EventPublisher/Subscriber] |
|  [eon::context::ContextHandle]  [eon::lifecycle::LifecycleMonitor]       |
+--------------------------------------------------------------------------+
                                    |
                                    v  (Pimpl / Stable ABI Boundary)
+--------------------------------------------------------------------------+
|                   eon::internal (Private Implementation)                 |
|  - Thread Pool & Dispatcher      - Shared Memory (POSIX / Win32)         |
|  - Lock-Free SPSC Ring Buffers   - Protocol Buffer / FlatBuffers Codec   |
|  - IPC Client (Unix Domain / Pipes) - Security & Token Validation        |
+--------------------------------------------------------------------------+
             |                                              |
             v (Zero-Copy SHM)                              v (Local IPC / UDS)
+--------------------------------------------------------------------------+
|                         EON Core Runtime Service                         |
|   Seven Intelligence Engines (ERS, EMS, ERE, PSE, SIE, ERG, HBU)          |
+--------------------------------------------------------------------------+
```

### Namespace Hierarchy

All public types and functions reside within the `eon` root namespace:

```cpp
namespace eon {
    namespace client {     // Primary client lifecycle and connection handles
        class EonClient;
        struct ClientOptions;
    }
    namespace events {     // Event definitions, subscriptions, and publication
        class EventPublisher;
        class EventSubscriber;
        class EventFilter;
        struct EventEnvelope;
    }
    namespace context {    // Context read-only queries and transactional updates
        class ContextHandle;
        struct SubjectSnapshot;
    }
    namespace lifecycle {  // Engine health and operational state monitoring
        enum class EngineState;
        struct EngineHealthReport;
    }
    namespace shm {        // Zero-copy shared memory descriptors
        class SharedMemoryBuffer;
        class SharedMemoryView;
    }
    namespace robot {      // Robot abstraction contracts and motion proposals
        struct MotionProposal;
        struct InteractionPayload;
    }
}
```

---

## 3. Core Architectural Components

### 3.1 The Client Handle (`eon::client::EonClient`)
`EonClient` is the primary entry point for host applications. It implements the Pimpl (Pointer to Implementation) idiom:
- Manages local IPC connection to EON Core (Unix Domain Sockets on Linux/QNX, Named Pipes on Windows).
- Coordinates background thread pool lifecycle.
- Handles registration and authentication handshakes.
- Provides RAII-guaranteed shutdown and disconnection upon destruction.

### 3.2 Event Publisher and Subscriber (`eon::events`)
- **EventPublisher:** Dispatches strongly typed events (`eon::events::EventEnvelope`) into EON Core. Supports both synchronous blocking dispatch with bounded timeouts and asynchronous future-based dispatch (`std::future<eon::Result<DeliveryReceipt>>`).
- **EventSubscriber:** Registers typed callback handlers. Uses dedicated bounded worker threads to isolate user callbacks from SDK IPC ingestion threads.

### 3.3 Shared Memory Perception Bus (`eon::shm`)
For high-bandwidth perceptual observations (e.g., raw microphone PCM chunks, pre-processed facial landmarks, video frames):
- Utilizes POSIX shared memory (`shm_open`, `mmap`) on Linux and Named File Mappings on Windows.
- Allocates fixed-size circular ring buffers.
- Transfers metadata and memory offsets via standard IPC messages, allowing zero-copy memory access by ERS and HBU engines without socket payload serialization.

### 3.4 Operational Health and Lifecycle Monitoring (`eon::lifecycle`)
Exposes the reconciled **7-State Operational Health Projection**:
```cpp
enum class EngineState : uint8_t {
    UNINITIALIZED = 0,
    INITIALIZING  = 1,
    ACTIVE        = 2,
    PAUSED        = 3,
    DEGRADED      = 4,
    STOPPED       = 5,
    FAULTED       = 6
};
```
Host C++ applications can poll engine status or attach observer callbacks to react to state degradation.

---

## 4. Concurrency, Execution, and Memory Constraints

### 4.1 Concurrency Model
1. **Thread Separation:**
   - **IPC Ingress Thread:** Reads raw bytes from IPC socket and signals dispatch queues.
   - **Worker Pool (`eon::ThreadPool`):** Fixed-size worker pool (default: 2 threads) that invokes user callbacks.
   - **User Calling Threads:** May publish events concurrently; publication is thread-safe using lock-free single-producer multi-consumer queues or lightweight spinlocks.
2. **Cooperative Cancellation:**
   - All asynchronous operations accept an optional `std::stop_token` (C++20) or `eon::CancellationToken` (C++17) to terminate inflight operations cleanly.

### 4.2 Bounded Memory Mandate
- **No Unbounded Buffers:** Every subscriber queue has a strict maximum capacity (default: 256 events).
- **Overflow Policy:** Explicitly configurable (`DropOldest`, `DropNewest`, `RejectWithBackpressure`). Under robotic real-time conditions, `DropOldest` is default for perceptual streams to ensure freshest data is processed.
- **Custom Memory Allocators:** Supports `std::pmr::memory_resource` (Polymorphic Memory Resources) in C++17, enabling integration with monotonic or pool allocators in real-time robotic nodes.

---

## 5. Non-Authoritative Robotics Safety Contract

In strict compliance with EON Principle 2.4:
- The C++ SDK exposes `eon::robot::MotionProposal`.
- Every proposal includes `bool is_authoritative = false;` and `uint64_t proposal_ttl_ms;`.
- The C++ SDK provides helper adaptors that serialize these proposals into ROS 2 trajectory or twist proposals.
- It is architecturally prohibited for `libeonsdk` to invoke low-level CAN bus, EtherCAT, or serial actuator drivers.

---

## 6. Performance Expectations and Benchmark Qualification

> [!WARNING]
> **Provisional Performance Notice:** Sub-millisecond latency targets ($< 0.5\text{ ms}$ IPC roundtrip) are **provisional design targets** and do not represent verified production benchmarks. Formal runtime verification requires execution under the benchmark protocol defined in `CPP_SDK_COMPATIBILITY_MATRIX.md`.

Target performance specifications:
- **IPC Event Dispatch Latency (Analytical Target):** $p_{50} \le 0.15\text{ ms}$, $p_{99} \le 0.50\text{ ms}$ on local x86_64 and Jetson Orin compute nodes.
- **Memory Footprint:** Resident Set Size (RSS) $\le 12\text{ MB}$ for base client runtime (excluding zero-copy SHM allocations).
- **CPU Overhead:** $\le 1.5\%$ of a single modern CPU core at 100 Hz event publication rate.

---

## 7. Traceability Matrix

| Requirement ID | C++ SDK Architectural Specification | Verification Plan |
|---|---|---|
| `PRD-REQ-004` | High-frequency zero-copy perception pipeline via `eon::shm` | Benchmark SHM ring buffer under 1080p frame load |
| `SRS-ARCH-010` | Deterministic C++ API for ROS 2 and robotic platforms | Compile and link against ROS 2 Humble/Jazzy C++17 nodes |
| `ADR-020` | Native C++ SDK with Pimpl ABI and C-ABI bridge | Automated ABI break checker (`abi-compliance-checker`) |
| `ADR-013` | Reconciled 7-State Engine Lifecycle Enum | Unit tests asserting 1:1 mapping with Core FSM |
