# EON Python SDK Authentication and Security Specification

**Document ID:** `EON-POL-SDK-001`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `SECURITY POLICY & ARCHITECTURE`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/PYTHON_SDK_ARCHITECTURE.md` (`EON-ARCH-SDK-001`)  
**Cross-References:**  
- `docs/architecture/API_AUTHENTICATION_AND_AUTHORIZATION.md` (`EON-SPEC-API-002`)  
- `docs/architecture/API_SECURITY.md` (`EON-POL-API-001`)  
- `docs/architecture/EVENT_SECURITY_AND_PRIVACY.md` (`EON-POL-COMM-001`)  
- `docs/architecture/CONTEXT_ACCESS_CONTROL.md` (`EON-POL-CTX-001`)  

---

## 1. Scope & Objective

This document defines the security architecture, credential handling procedures, authentication flows, and cryptographic verification mechanisms implemented in the EON Python SDK. The SDK must guarantee strong isolation of client credentials, support zero-trust transport encryption, enforce least-privilege scoping, and ensure secure inter-process communication both on embedded robot platforms and across external networks.

---

## 2. Authentication Mechanisms Supported

The SDK supports three distinct authentication modalities corresponding to the EON API Gateway security profile (`EON-SPEC-API-002`):

```text
+-----------------------------------------------------------------------------+
|                           SDK Authentication Schemes                        |
+-----------------------------------------------------------------------------+
        |                                   |                              |
        v                                   v                              v
+------------------+              +-------------------+          +-------------------+
|  Static API Key  |              |  JWT Bearer Token |          |       mTLS        |
|  (Developer/CLI) |              |  (Services/Users) |          | (Robot Onboard)   |
+------------------+              +-------------------+          +-------------------+
| Header:          |              | Header:           |          | Hardware/OS X.509 |
| X-API-Key        |              | Authorization:    |          | Client Cert Auth  |
| Hashed verification             | Bearer <token>    |          | Transport Layer   |
| Scoped role keys |              | Auto-refresh hook |          | Zero shared secret|
+------------------+              +-------------------+          +-------------------+
```

### 2.1 API Key Authentication

Static API keys are suited for local development, CLI tooling, and simple script integrations:
- Keys are transmitted via the standard `X-API-Key` HTTP header or WebSocket initial handshake query/header.
- The SDK never persists API keys to disk or caches them in plaintext log files.
- Keys can be injected directly or loaded automatically from the `EON_API_KEY` environment variable.

### 2.2 JWT Bearer Token Authentication & Automated Renewal

For user sessions, external microservices, and dynamic operator consoles, the SDK provides OAuth 2.0 / OIDC-compatible JWT handling:
- **Token Injection:** Transmitted via `Authorization: Bearer <token>`.
- **Automated Lifecycle Management:** The SDK provides a pluggable `TokenProvider` callable. When a token is within 60 seconds of expiration, the SDK automatically invokes the provider or refresh endpoint (`/api/v1/auth/refresh`) to obtain a new token without interrupting inflight asynchronous requests.
- **Clock Drift Tolerance:** The SDK incorporates a configurable clock-skew window (default: 15 seconds) when evaluating `exp` and `nbf` claims.

### 2.3 Mutual TLS (mTLS) for On-Robot Hardware

In robotics deployments, hardware nodes authenticate via mutual TLS (mTLS):
- The SDK configures a strictly validated Python `ssl.SSLContext` using TLS 1.3.
- Requires client certificate (`client.pem`), private key (`client.key`), and root Certificate Authority (`ca.pem`).
- Private keys can be protected via passphrase or interfaced via hardware security modules (PKCS#11 / TPM 2.0) using standard OS cryptographic providers.

---

## 3. Secure Credential Management & Zero-Leakage Policies

### 3.1 Credential Precedence Hierarchy

The SDK resolves credentials using a deterministic, safe precedence chain:

1. **Explicit Constructor Argument:** `AsyncEonClient(api_key="...", ...)`
2. **Environment Variable:** `EON_API_KEY`, `EON_BEARER_TOKEN`, `EON_CLIENT_CERT`
3. **Configuration File:** Read from protected local config (`~/.config/eon/credentials.yaml`, permissions `0600`)
4. **Credential Helper / Secret Service:** Platform keyring or AWS/GCP instance metadata (if configured)

### 3.2 In-Memory Protection & Log Sanitization

To prevent accidental exposure in stack traces, debug logs, and crash reports:
- The SDK wraps secrets in a `SecretStr` class that suppresses `__repr__` and `__str__` outputs, replacing values with `**********`.
- Sockets and HTTP debug logs automatically sanitize headers matching `Authorization`, `X-API-Key`, `Cookie`, and `Set-Cookie`.
- Sensitive token strings stored in memory are eligible for deterministic clearing upon client shutdown.

---

## 4. Local IPC vs. Remote Transport Security

```text
+-----------------------------------------------------------------------------+
|                          Transport Security Matrix                          |
+-----------------------------------------------------------------------------+
| Mode       | Transport     | Encryption         | Auth Mechanism            |
| :---       | :---          | :---               | :---                      |
| Local Mode | Shared Memory | OS File Perms 0600 | POSIX UID/GID Check       |
| Local Mode | Unix Domain S | OS Socket Perms    | SO_PEERCRED Authentication|
| Remote     | HTTPS (REST)  | TLS 1.3 / AES-GCM  | API Key / JWT / mTLS      |
| Remote     | WSS (Stream)  | TLS 1.3 / WSS      | Handshake Token + mTLS    |
| Remote     | gRPC          | TLS 1.3 (HTTP/2)   | CallCredentials / mTLS    |
+-----------------------------------------------------------------------------+
```

### 4.1 Local In-Process Security

When operating in **Local In-Process Mode** on the robot host:
- Communication occurs via direct memory or Unix Domain Sockets (UDS).
- The SDK verifies the peer's POSIX credentials (`SO_PEERCRED`) ensuring only processes running under the authorized `eon` system group can access core control endpoints.
- Avoids loopback TCP socket hijacking vulnerabilities.

### 4.2 Remote Transport Security

When communicating across external networks:
- Enforces TLS 1.3 minimum standard (disallows TLS 1.0, 1.1, and 1.2 legacy ciphers).
- Strict certificate hostname verification enabled by default.
- Pinning support for edge robot root CAs to eliminate public CA compromise vectors.

---

## 5. Least-Privilege Scoping in SDK Calls

All client calls emit metadata reflecting the required capability scope (`EON-SPEC-API-002`):
- `engine:read` / `engine:write`: Restricted to engine lifecycle modifications.
- `context:read` / `context:write`: Scoped per user domain and data retention tag.
- `events:publish` / `events:subscribe`: Enforces topic ACL matching.

If a caller invokes an endpoint or subscribes to a topic without the requisite scope, the SDK traps the 403 Forbidden response and raises a descriptive `EonAccessDeniedError` detailing the missing scope.
