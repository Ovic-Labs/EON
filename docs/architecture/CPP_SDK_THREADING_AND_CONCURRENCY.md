# OVIC EON — C++ SDK Threading and Concurrency Specification

**Document ID:** `EON-SPEC-CPP-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Concurrency Engineers, Real-Time Systems Programmers  
**Traceability:** `EON-ARCH-CPP-001`, SRS-PERF-001, ADR-020  

---

## 1. Threading Architecture and Thread Separation

`libeonsdk` isolates internal library concurrency from host application threads. The system defines three strictly separated thread categories:

```text
[User / Robot Nodes] ----(Thread-safe call)----> [EventPublisher Queue]
                                                        |
                                                        v
                                             [IPC Transport Thread]
                                                        |
                                                        v (Socket write)
                                             [EON Core Service]
                                                        | (Socket read)
                                             [IPC Ingress Thread]
                                                        |
                                                        v
                                             [Worker Thread Pool]
                                                        |
                                                        v
[User Callback Handlers] <-----------------------------+
```

1. **IPC Transport Thread:** Manages non-blocking epoll / kqueue / IOCP event loops for IPC I/O. Never executes user callbacks or blocks on user locks.
2. **Ingress Dispatch Thread:** Deserializes incoming event headers and enqueues tasks into the worker pool.
3. **Worker Thread Pool (`eon::ThreadPool`):** Executes registered user subscription callbacks. Configurable pool size (default: 2 threads). Protects internal transport threads from user-introduced delays.

---

## 2. Lock-Free and Synchronized Primitives

- **Single-Producer Single-Consumer (SPSC) Queues:** Used between dedicated internal threads. Implemented using standard C++17 memory fences (`std::memory_order_acquire` / `std::memory_order_release`) with zero mutex locks.
- **Shared Mutex for Dynamic Subscriptions:** Registration and deregistration of event handlers use `std::shared_mutex` (reader-writer lock). Ingestion threads acquire shared read locks, allowing concurrent callback execution without blocking ingestion.

---

## 3. Cooperative Cancellation and Shutdown Sequence

Shutdown of `EonClient` follows a deterministic sequence:
1. `IsConnected()` transitions to `false`; new publish requests return `NOT_CONNECTED`.
2. Active subscriptions stop receiving new events from the ingress thread.
3. In-flight tasks in the `ThreadPool` are completed up to a bounded shutdown timeout (default: 500 ms).
4. Cancellation tokens signal any active long-running operations.
5. Ingress and transport threads are joined.
6. IPC socket is cleanly closed, releasing OS file descriptors.
