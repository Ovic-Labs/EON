# ADR-020: Native C++ SDK Architecture (`libeonsdk`)

**Document ID:** `EON-ADR-020`  
**Date:** 2026-11-24  
**Status:** `APPROVED`  
**Deciders:** Antigravity Engineering Architecture Team  
**Scope:** Client SDKs, Real-Time Ingestion, ROS 2 Integration  

---

## 1. Context and Problem Statement

While the Python SDK (`eon-sdk`) provides an agile development interface for research and high-level behavioral scripting, robotics execution environments demand deterministic latency, zero garbage-collection pauses, bounded memory allocations, and direct integration into C++ middleware stacks (such as ROS 2 C++ nodes and custom motion controllers).

## 2. Decision

We decide to architect a native C++ SDK (`libeonsdk`) with:
1. ISO C++17 standardization with Pimpl (Pointer to Implementation) idiom for all public interface classes to guarantee ABI stability.
2. A flat, versioned C-ABI bridge header (`eon_c.h`) for foreign function interfaces (FFI).
3. Zero-copy shared memory (`eon::shm`) abstractions using POSIX `/dev/shm` and Windows Named File Mapping.
4. Monadic error returns (`eon::Result<T, EonError>`) across public boundaries, preventing unhandled exceptions from crossing shared library boundaries.

## 3. Alternatives Considered

- *Alternative A: Pure Python bindings wrapped in C++ via pybind11 embedding.* Rejected: Imposes severe Python GIL contention, high memory footprint, and non-deterministic GC latency.
- *Alternative B: Pure gRPC C++ Client.* Rejected: Excludes zero-copy local shared memory and introduces high serialization overhead for 30 FPS video frames.

## 4. Consequences and Implications

- **Positive:** Enables sub-millisecond IPC event dispatch, eliminates heap allocations in steady-state perception loops, and provides seamless compatibility with ROS 2 C++ nodes.
- **Negative:** Requires rigorous manual memory management and strict ABI compliance checking in CI.
- **Security Implications:** Socket permissions and peer credentials (`SO_PEERCRED`) enforced during local connection.
- **Privacy Implications:** Enforces client-side zero-retention invariant for raw video/audio buffers.
- **Performance Implications:** Target IPC dispatch latency analytical target: $p_{50} \le 0.15\text{ ms}, p_{99} \le 0.50\text{ ms}$.
- **Related ADRs:** ADR-007, ADR-019, ADR-021, ADR-027.
- **Supersession History:** None.
