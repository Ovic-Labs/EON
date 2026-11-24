# OVIC EON — C++ SDK API Contracts Specification

**Document ID:** `EON-SPEC-CPP-001`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.11)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Robotics Software Engineers, C++ Developers  
**Traceability:** `EON-ARCH-CPP-001`, `EON-SPEC-SDK-002`, `EON-ARCH-LIFE-001`, ADR-013, ADR-020  

---

## 1. Scope and Design Principles

This specification details the formal C++17 API contracts for `libeonsdk`.
Key principles:
1. **Value Semantics and Const Correctness:** Methods that do not mutate state are marked `const noexcept` where applicable.
2. **Monadic Error Returns:** Functions subject to runtime failure return `eon::Result<T, EonError>` instead of throwing cross-boundary exceptions.
3. **Explicit Ownership:** Transfers of ownership use `std::unique_ptr` or rvalue references (`&&`).
4. **Non-Authoritative Motion:** All motion interfaces explicitly mark proposals as non-authoritative (`is_authoritative = false`).

---

## 2. Core API Type Definitions

### 2.1 Result Monad (`eon::Result<T>`)

```cpp
#pragma once
#include <variant>
#include <string>
#include <system_error>

namespace eon {

enum class ErrorCode : int {
    SUCCESS = 0,
    NOT_CONNECTED = 1,
    CONNECTION_LOST = 2,
    TIMEOUT = 3,
    INVALID_ARGUMENT = 4,
    BUFFER_OVERFLOW = 5,
    PERMISSION_DENIED = 6,
    ENGINE_FAULTED = 7,
    INTERNAL_ERROR = 8
};

struct EonError {
    ErrorCode code;
    std::string message;
    std::string context_id;
};

template <typename T>
class Result {
public:
    Result(T value) : data_(std::move(value)) {}
    Result(EonError error) : data_(std::move(error)) {}

    bool HasValue() const noexcept { return std::holds_alternative<T>(data_); }
    explicit operator bool() const noexcept { return HasValue(); }

    const T& Value() const { return std::get<T>(data_); }
    T& Value() { return std::get<T>(data_); }

    const EonError& Error() const { return std::get<EonError>(data_); }

private:
    std::variant<T, EonError> data_;
};

// Void specialization
template <>
class Result<void> {
public:
    Result() : has_value_(true) {}
    Result(EonError error) : has_value_(false), error_(std::move(error)) {}

    bool HasValue() const noexcept { return has_value_; }
    explicit operator bool() const noexcept { return has_value_; }

    const EonError& Error() const { return error_; }

private:
    bool has_value_;
    EonError error_;
};

} // namespace eon
```

---

## 3. Client and Lifecycle Contracts

### 3.1 Client Options and Connection Contract

```cpp
namespace eon::client {

struct ClientOptions {
    std::string endpoint_uri = "ipc:///tmp/eon.sock"; // Unix domain socket or named pipe
    std::string client_name = "robot_client";
    uint32_t connection_timeout_ms = 5000;
    uint32_t heartbeat_interval_ms = 1000;
    size_t worker_threads = 2;
    size_t default_queue_capacity = 256;
};

class EonClient {
public:
    explicit EonClient(ClientOptions options);
    ~EonClient();

    // Connection lifecycle
    Result<void> Connect();
    Result<void> Disconnect();
    bool IsConnected() const noexcept;

    // Subsystem handles
    events::EventPublisher& Publisher();
    events::EventSubscriber& Subscriber();
    context::ContextHandle& Context();
    lifecycle::LifecycleMonitor& Lifecycle();
};

} // namespace eon::client
```

### 3.2 Operational Health State Enum

In strict conformance with Phase 2.4 reconciliation (`EON-ARCH-LIFE-001` v2.0.0):

```cpp
namespace eon::lifecycle {

enum class EngineState : uint8_t {
    UNINITIALIZED = 0,
    INITIALIZING  = 1,
    ACTIVE        = 2,
    PAUSED        = 3,
    DEGRADED      = 4,
    STOPPED       = 5,
    FAULTED       = 6
};

inline const char* ToString(EngineState state) noexcept {
    switch (state) {
        case EngineState::UNINITIALIZED: return "UNINITIALIZED";
        case EngineState::INITIALIZING:  return "INITIALIZING";
        case EngineState::ACTIVE:        return "ACTIVE";
        case EngineState::PAUSED:        return "PAUSED";
        case EngineState::DEGRADED:      return "DEGRADED";
        case EngineState::STOPPED:       return "STOPPED";
        case EngineState::FAULTED:       return "FAULTED";
        default:                         return "UNKNOWN";
    }
}

struct EngineHealthReport {
    std::string engine_id;
    EngineState state;
    uint64_t uptime_ms;
    double error_rate_per_sec;
    std::string last_error_message;
};

class LifecycleMonitor {
public:
    virtual ~LifecycleMonitor() = default;
    virtual Result<EngineHealthReport> GetEngineHealth(const std::string& engine_id) const = 0;
    virtual Result<std::vector<EngineHealthReport>> GetAllEnginesHealth() const = 0;
    virtual void RegisterStateChangeCallback(
        std::function<void(const std::string& engine_id, EngineState old_state, EngineState new_state)> callback
    ) = 0;
};

} // namespace eon::lifecycle
```

---

## 4. Event Publication and Subscription Contracts

```cpp
namespace eon::events {

enum class Priority : uint8_t {
    LOW = 0,
    NORMAL = 1,
    HIGH = 2,
    CRITICAL = 3
};

struct EventEnvelope {
    std::string event_id;
    std::string topic;
    std::string source_engine;
    uint64_t timestamp_ns;
    Priority priority = Priority::NORMAL;
    std::vector<uint8_t> payload;
    std::string schema_version;
};

class EventPublisher {
public:
    virtual ~EventPublisher() = default;
    virtual Result<void> Publish(const EventEnvelope& event) = 0;
    virtual Result<void> PublishAsync(
        EventEnvelope event,
        std::function<void(Result<void>)> completion_callback
    ) = 0;
};

class EventSubscriber {
public:
    virtual ~EventSubscriber() = default;
    using Handler = std::function<void(const EventEnvelope&)>;

    virtual Result<uint64_t> Subscribe(const std::string& topic_filter, Handler handler) = 0;
    virtual Result<void> Unsubscribe(uint64_t subscription_id) = 0;
};

} // namespace eon::events
```

---

## 5. Non-Authoritative Robot Motion Proposal Contract

```cpp
namespace eon::robot {

struct MotionProposal {
    std::string proposal_id;
    std::string source_engine = "erg";
    uint64_t generated_at_ns;
    uint32_t ttl_ms;

    // Mandatory Architectural Non-Authoritative Invariant
    static constexpr bool is_authoritative = false;

    // Proposed kinematics for social signaling (head nod, gaze shift, gesture)
    struct GazeVector { double pitch; double yaw; double roll; } target_gaze;
    struct GestureRequest { std::string gesture_name; double speed_scale; } gesture;

    std::string rationale; // Inferred social context reason
};

} // namespace eon::robot
```
