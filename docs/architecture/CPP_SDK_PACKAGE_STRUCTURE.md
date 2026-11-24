# OVIC EON — C++ SDK Package Structure Specification

**Document ID:** `EON-ARCH-CPP-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** C++ Developers, Build Engineers, Package Maintainers  
**Traceability:** `EON-ARCH-CPP-001`, ADR-020  

---

## 1. Directory and Source Tree Layout

The C++ SDK repository structure is organized according to modern CMake and C++ packaging best practices:

```text
eon-cpp-sdk/
├── CMakeLists.txt                      # Root CMake build configuration
├── cmake/
│   ├── eon-config.cmake.in             # CMake package configuration template
│   ├── compiler_warnings.cmake         # Strict warning flags (-Wall -Wextra -Werror)
│   └── sanitizers.cmake                # ASan, UBSan, TSan configuration
├── include/                            # Public Header Files (Installed)
│   └── eon/
│       ├── eon.hpp                     # Umbrella header
│       ├── version.hpp                 # Version macros (EON_SDK_VERSION_MAJOR, etc.)
│       ├── types.hpp                   # Core primitive types, UUIDs, timestamps
│       ├── result.hpp                  # Expected/Result monadic error type
│       ├── client/
│       │   ├── client.hpp              # eon::client::EonClient
│       │   └── client_options.hpp      # Connection configuration
│       ├── events/
│       │   ├── event_envelope.hpp      # Envelope, headers, payload variants
│       │   ├── publisher.hpp           # EventPublisher interface
│       │   ├── subscriber.hpp          # EventSubscriber interface
│       │   └── event_filter.hpp        # Filter predicates
│       ├── context/
│       │   ├── context_handle.hpp      # Context query handle
│       │   └── snapshot.hpp            # Read-only state snapshot
│       ├── lifecycle/
│       │   ├── engine_state.hpp        # 7-State EngineState enum
│       │   └── health_report.hpp       # Health telemetry structs
│       ├── shm/
│       │   ├── shared_memory.hpp       # Zero-copy ring buffer descriptors
│       │   └── memory_view.hpp         # Non-owning buffer slice view
│       ├── robot/
│       │   ├── motion_proposal.hpp     # Non-authoritative motion proposal
│       │   └── interaction.hpp         # Social interaction payloads
│       └── c_api/
│           └── eon_c.h                 # Flat C-ABI interface for FFI
├── src/                                # Private Implementation Sources
│   ├── client/
│   │   ├── client_impl.hpp             # EonClient::Impl definition
│   │   └── client_impl.cpp             # IPC handshake and lifecycle management
│   ├── events/
│   │   ├── publisher_impl.cpp
│   │   └── subscriber_impl.cpp
│   ├── ipc/
│   │   ├── socket_transport.hpp        # Unix Domain Socket & Windows Named Pipe
│   │   ├── socket_transport_posix.cpp
│   │   └── socket_transport_win32.cpp
│   ├── shm/
│   │   ├── shm_posix.cpp               # shm_open / mmap implementation
│   │   └── shm_win32.cpp               # CreateFileMapping / MapViewOfFile
│   ├── threading/
│   │   ├── thread_pool.hpp
│   │   └── thread_pool.cpp
│   ├── utils/
│   │   ├── ring_buffer.hpp             # Lock-free SPSC buffer
│   │   └── time.cpp
│   └── c_api/
│       └── eon_c_bridge.cpp            # C-ABI wrapper implementations
├── tests/
│   ├── unit/                           # GoogleTest unit tests
│   │   ├── test_types.cpp
│   │   ├── test_result.cpp
│   │   ├── test_ring_buffer.cpp
│   │   └── test_lifecycle_enum.cpp
│   ├── integration/                    # IPC mock integration tests
│   │   └── test_ipc_handshake.cpp
│   └── benchmark/                      # Google Benchmark harness
│       └── bench_event_dispatch.cpp
├── examples/                           # Reference usage examples
│   ├── basic_subscriber.cpp
│   ├── zero_copy_perception.cpp
│   └── ros2_lifecycle_adapter.cpp
└── package.xml                         # ROS 2 package manifest (ament_cmake)
```

---

## 2. Header Inclusion Model and Pimpl Discipline

To guarantee fast compilation times, prevent macro pollution, and isolate private dependencies (such as flatbuffers or OS socket headers) from consumer code:
1. **Public Headers:** Only include standard C++17 headers (`<string>`, `<memory>`, `<vector>`, `<chrono>`, `<functional>`) and internal `eon/` headers.
2. **Pimpl Enforcement:** All client-facing classes expose an opaque `Impl` pointer:
   ```cpp
   namespace eon::client {
   class EonClient {
   public:
       explicit EonClient(const ClientOptions& options);
       ~EonClient();
       EonClient(EonClient&&) noexcept;
       EonClient& operator=(EonClient&&) noexcept;
       EonClient(const EonClient&) = delete;
       EonClient& operator=(const EonClient&) = delete;

       Result<void> Connect();
       Result<void> Disconnect();
       bool IsConnected() const noexcept;

   private:
       class Impl;
       std::unique_ptr<Impl> impl_;
   };
   }
   ```
3. **No Private Symbols in Public Headers:** No OS headers (`<sys/socket.h>`, `<windows.h>`) are ever included in the `include/eon/` directory.

---

## 3. Package Deliverables and Artifacts

Building the SDK produces:
- `libeonsdk.so` / `libeonsdk.dylib` / `eonsdk.dll` (Shared library with versioned SONAME).
- `libeonsdk_static.a` / `eonsdk_static.lib` (Optional static library).
- `eon-config.cmake` and `eon-config-version.cmake` for `find_package(eon REQUIRED)`.
- `eon.pc` (pkg-config descriptor).
- Optional Debian (`.deb`) and RPM packages generated via CPack.
- ROS 2 `ament_cmake` package support.
