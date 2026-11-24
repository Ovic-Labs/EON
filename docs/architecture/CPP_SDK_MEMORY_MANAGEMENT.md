# OVIC EON — C++ SDK Memory Management Specification

**Document ID:** `EON-SPEC-CPP-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Software Engineers, Embedded C++ Specialists  
**Traceability:** `EON-ARCH-CPP-001`, SRS-PERF-001, ADR-020  

---

## 1. Principles of Deterministic Memory Management

In robotics deployments, dynamic heap allocation during steady-state operation can cause non-deterministic latency spikes due to memory fragmentation and lock contention inside system allocators. The C++ SDK is designed to adhere to real-time memory management principles:
1. **Zero Steady-State Heap Allocations for Ingestion:** Memory buffers for high-rate perceptual data are pre-allocated during initialization.
2. **Strict RAII Ownership:** All OS handles, socket descriptors, threads, and shared memory segments are wrapped in RAII guard types with zero-leak semantics.
3. **Bounded Circular Buffers:** Subscriber dispatch queues and SHM pipelines use fixed-size bounded ring buffers.
4. **Polymorphic Memory Resources (`std::pmr`):** C++17 `pmr` allocators allow users to supply custom memory pools or monotonic buffers for event payload deserialization.

---

## 2. Shared Memory Architecture (`eon::shm`)

For exchanging dense observation arrays (e.g., 640x480 RGB frames, 16kHz PCM audio buffers, 512-dim face embeddings) with EON Core:

```text
[Host Robot Sensor Process / C++ SDK]
               |
               | (1) Pre-allocated fixed-size ring buffer
               v
     +-----------------------------------------------+
     |      POSIX /dev/shm or Windows Named Memory   |
     |   [Slot 0]  [Slot 1]  [Slot 2] ... [Slot N]   |
     +-----------------------------------------------+
               ^
               | (2) Passes lightweight 64-byte descriptor via UDS IPC
               |
[EON Core Perception Engine (ERS / HBU)]
```

### 2.1 Ring Buffer Slot Descriptor
```cpp
namespace eon::shm {

struct alignas(64) ShmSlotHeader {
    std::atomic<uint32_t> state;       // 0: Free, 1: Writing, 2: Ready, 3: Reading
    uint32_t slot_index;
    uint64_t timestamp_ns;
    uint32_t payload_size_bytes;
    uint32_t format_fourcc;
    uint32_t width;
    uint32_t height;
    uint8_t  reserved[32];
};

class SharedMemoryBuffer {
public:
    static Result<std::unique_ptr<SharedMemoryBuffer>> Create(
        const std::string& segment_name,
        size_t slot_count,
        size_t slot_size_bytes
    );

    virtual ~SharedMemoryBuffer() = default;
    virtual Result<ShmSlotHeader*> AcquireWriteSlot(std::chrono::milliseconds timeout) = 0;
    virtual void CommitWriteSlot(ShmSlotHeader* slot) = 0;
    virtual void ReleaseReadSlot(ShmSlotHeader* slot) = 0;
};

} // namespace eon::shm
```

---

## 3. Queue Overflow and Drop Policies

To prevent memory growth when consumer threads are stalled:
```cpp
namespace eon::events {

enum class OverflowPolicy {
    DROP_OLDEST,         // Discard oldest element in queue (default for sensor data)
    DROP_NEWEST,         // Discard incoming event
    BLOCK_PRODUCER,      // Block calling thread until slot opens (bounded timeout)
    FAIL_AND_REPORT      // Immediately return BUFFER_OVERFLOW error
};

} // namespace eon::events
```

---

## 4. Leak Prevention and Audit

- **Valgrind & ASan Compliance:** The SDK is designed to be validated under AddressSanitizer (`-fsanitize=address`) and LeakSanitizer.
- **Explicit Finalization:** Destructors drain all internal ring buffers and unmap shared memory segments before process exit.
