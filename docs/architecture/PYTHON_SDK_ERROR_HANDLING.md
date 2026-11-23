# EON Python SDK Error Handling Specification

**Document ID:** `EON-SPEC-SDK-003`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `TECHNICAL SPECIFICATION`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/PYTHON_SDK_ARCHITECTURE.md` (`EON-ARCH-SDK-001`)  
**Cross-References:**  
- `docs/architecture/API_ERROR_AND_RELIABILITY_CONTRACT.md` (`EON-SPEC-API-004`)  
- `docs/architecture/EVENT_DELIVERY_AND_RELIABILITY.md` (`EON-SPEC-COMM-002`)  
- `docs/architecture/EON_CORE_FAILURE_HANDLING.md` (`EON-ARCH-CORE-008`)  

---

## 1. Scope & Objective

This document specifies the exception taxonomy, status code mappings, retry policies, backoff algorithms, connection failover mechanisms, and cancellation handling for the EON Python SDK. The goal is to provide deterministic, predictable, and resilient error handling across both synchronous and asynchronous operations, ensuring robot client applications can gracefully adapt to transient network disruptions, engine restarts, and rate limiting.

---

## 2. Exception Hierarchy

All SDK-generated exceptions derive from the abstract base exception `EonError`, ensuring callers can easily catch library-specific faults without capturing unrelated Python exceptions.

```text
EonError (Base SDK Exception)
├── EonConfigurationError
│   ├── EonInvalidOptionError
│   └── EonMissingCredentialError
├── EonTransportError
│   ├── EonConnectionError
│   │   ├── EonConnectionRefusedError
│   │   └── EonConnectionClosedError
│   ├── EonTimeoutError
│   │   ├── EonConnectTimeoutError
│   │   └── EonReadTimeoutError
│   └── EonProtocolError
│       └── EonSerializationError
├── EonApiError (HTTP 4xx / 5xx & gRPC status codes)
│   ├── EonBadRequestError (HTTP 400)
│   ├── EonAuthenticationError (HTTP 401)
│   ├── EonAccessDeniedError (HTTP 403)
│   ├── EonNotFoundError (HTTP 404)
│   ├── EonConflictError (HTTP 409)
│   │   └── EonContextConflictError
│   ├── EonRateLimitError (HTTP 429)
│   └── EonServerError (HTTP 500)
│       ├── EonServiceUnavailableError (HTTP 503)
│       └── EonGatewayTimeoutError (HTTP 504)
└── EonDomainError
    ├── EonEngineError
    │   ├── EonEngineStateError
    │   └── EonEngineInitializationError
    ├── EonEventError
    │   ├── EonSubscriptionError
    │   └── EonDeliveryRejectedError
    └── EonModelError
        ├── EonModelNotFoundError
        └── EonInferenceTimeoutError
```

---

## 3. API Status Code Mapping

When operating in **Remote Client Mode**, incoming HTTP and gRPC status codes are mapped into SDK exceptions according to the following deterministic rules:

| HTTP Status | gRPC Status Code | SDK Exception Class | Retryable? | Default Action |
| :--- | :--- | :--- | :--- | :--- |
| **400** | `INVALID_ARGUMENT` | `EonBadRequestError` | No | Abort; inspect request payload |
| **401** | `UNAUTHENTICATED` | `EonAuthenticationError` | No (unless token renewed) | Trigger token refresh; abort if persistent |
| **403** | `PERMISSION_DENIED` | `EonAccessDeniedError` | No | Abort; check role scopes |
| **404** | `NOT_FOUND` | `EonNotFoundError` | No | Abort; check resource ID |
| **409** | `ABORTED` / `ALREADY_EXISTS` | `EonConflictError` | Optional | Reload resource or retry with updated version |
| **429** | `RESOURCE_EXHAUSTED` | `EonRateLimitError` | Yes | Exponential backoff using `Retry-After` header |
| **500** | `INTERNAL` | `EonServerError` | No | Abort; notify gateway administrator |
| **502** | `UNAVAILABLE` | `EonConnectionError` | Yes | Retry with backoff |
| **503** | `UNAVAILABLE` | `EonServiceUnavailableError` | Yes | Retry with backoff |
| **504** | `DEADLINE_EXCEEDED` | `EonGatewayTimeoutError` | Yes (for idempotent calls) | Retry with increased timeout |

---

## 4. Retry Policy & Exponential Backoff Algorithm

### 4.1 Decorrelated Jitter Backoff Algorithm

To avoid the "thundering herd" problem across large robot fleets reconnecting to the EON Gateway, the SDK implements the "Full Jitter" exponential backoff algorithm:

$$\Delta t_{\text{wait}} = \text{random}(0, \min(T_{\text{max}}, T_{\text{base}} \times 2^{\text{attempt}}))$$

Where:
- $T_{\text{base}} = 0.2\text{ seconds}$ (initial backoff delay)
- $T_{\text{max}} = 10.0\text{ seconds}$ (maximum backoff ceiling)
- $\text{max\_retries} = 3$ (default retry budget)

### 4.2 Idempotency Rules

The SDK strictly respects HTTP method idempotency:
- `GET`, `HEAD`, `PUT`, `DELETE`, and `OPTIONS` requests are considered idempotent and are eligible for automatic retries upon network or 503 faults.
- `POST` requests are **NOT** retried automatically unless an `Idempotency-Key` header was explicitly supplied by the caller or configured on the client.

---

## 5. WebSocket Reconnection & Streaming Failover

For real-time event streaming (`client.events.subscribe(...)`), the SDK incorporates an automatic background reconnection loop:

1. **Disconnect Detection:** Heartbeat ping/pong frames are evaluated every 10 seconds. If two consecutive pings go unanswered, the connection is marked broken.
2. **Backoff & Reconnect:** The SDK initiates reconnection attempts using the jittered backoff algorithm.
3. **Session Resumption & Subscription Re-registration:** Upon successful reconnect, the SDK re-subscribes to all active topics and passes the last received event ID (`Last-Event-ID` header) to allow the broker to replay dropped events from its ring buffer.
4. **Queue Overflow Protection:** While disconnected, inbound client publish events are buffered up to `buffer_size` (default 1000 items). Exceeding this limit drops oldest events or raises `EonDeliveryRejectedError` based on configured overflow policy.

---

## 6. Timeout & Cancellation Handling

All SDK operations support deterministic timeouts and standard Python cancellation primitives:

- **Connect Timeout:** Maximum duration allowed to establish TCP/TLS connection (default: $3.0\text{ s}$).
- **Read Timeout:** Maximum duration allowed between receiving consecutive response bytes (default: $10.0\text{ s}$).
- **Total Request Timeout:** Absolute timeout for an entire request-response cycle (default: $15.0\text{ s}$).
- **Asyncio Cancellation:** When an `asyncio.Task` calling an SDK method is cancelled, the underlying transport socket/stream is immediately aborted and cleaned up without dangling connections or resource leaks.
