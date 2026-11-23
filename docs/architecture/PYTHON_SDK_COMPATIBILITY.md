# EON Python SDK Compatibility and Versioning Specification

**Document ID:** `EON-SPEC-SDK-004`  
**Version:** `1.0.0`  
**Status:** `APPROVED`  
**Classification:** `TECHNICAL SPECIFICATION`  
**Layer:** Layer 1 (Public Developer & Client Layer)  
**Parent Document:** `docs/architecture/PYTHON_SDK_ARCHITECTURE.md` (`EON-ARCH-SDK-001`)  
**Cross-References:**  
- `docs/architecture/API_VERSIONING_AND_COMPATIBILITY.md` (`EON-SPEC-API-003`)  
- `docs/architecture/PYTHON_SDK_PACKAGE_STRUCTURE.md` (`EON-SPEC-SDK-001`)  

---

## 1. Scope & Objective

This document defines the runtime environment compatibility matrix, operating system support tiers, hardware CPU architecture constraints, and API version negotiation protocols for the EON Python SDK.

---

## 2. Python Version Support Matrix

The EON Python SDK aligns with the official Python Software Foundation (PSF) lifecycle and prioritizes long-term support (LTS) distributions standard in robotics (Ubuntu 22.04 LTS / 24.04 LTS):

| Python Version | Support Level | CI Validation | Deprecation Roadmap |
| :--- | :--- | :--- | :--- |
| **Python 3.10** | **Tier 1 (Supported)** | Full test matrix | Supported through Oct 2026 (Ubuntu 22.04 baseline) |
| **Python 3.11** | **Tier 1 (Primary / Recommended)** | Full test matrix & lint | Supported through Oct 2027 (Active development baseline) |
| **Python 3.12** | **Tier 1 (Supported)** | Full test matrix | Supported through Oct 2028 |
| **Python 3.13** | **Tier 2 (Experimental)** | Build smoke tests | Full Tier 1 support upon ecosystem package maturity |
| **Python <= 3.9** | **Unsupported** | None (blocked in setup) | End-of-Life |

---

## 3. Operating System & Architecture Support

| Operating System | Architectures | Target Environment | Tier |
| :--- | :--- | :--- | :--- |
| **Ubuntu Linux 22.04 / 24.04 LTS** | `x86_64`, `aarch64` (ARM64) | Robot Onboard (Jetson, Industrial PCs), Workstations | **Tier 1 (Primary)** |
| **Debian 12 (Bookworm)** | `x86_64`, `aarch64` | Edge Gateways & Containerized Deployments | **Tier 1** |
| **macOS 13+ (Ventura / Sonoma / Sequoia)** | `Apple Silicon (arm64)`, `x86_64` | Developer Laptops & HRI Experimentation | **Tier 1** |
| **Windows 11 / Windows Server 2022** | `x86_64` | Simulation Environments & Developer Stations | **Tier 1** |

---

## 4. API Version Negotiation & Handshake Protocol

When operating in **Remote Client Mode**, the SDK conducts an automated compatibility handshake with the EON API Gateway upon connection initialization:

1. **Handshake Probe:** Upon calling `client.connect()`, the SDK queries the gateway version endpoint: `GET /api/v1/version`.
2. **Version Evaluation:**
   - Server returns semantic version metadata: `{"api_version": "1.4.0", "min_client_version": "0.1.0"}`.
   - The SDK compares its built-in client version against the server's minimum supported version.
3. **Compatibility Outcomes:**
   - **Compatible:** Client version matches within major version boundary (`^1.0.0` or `0.1.x` pre-release). Connection proceeds.
   - **Incompatible (Server Too Old):** Server version lacks features required by SDK; SDK raises `EonIncompatibleServerVersionError`.
   - **Incompatible (Client Too Old):** Server requires newer client due to deprecation; SDK raises `EonOutdatedClientVersionError` with an actionable upgrade message.
4. **Header Advertising:** Every subsequent outgoing HTTP/WebSocket request includes the SDK version header: `X-EON-Client-Version: 0.1.0` and `X-EON-Python-Version: 3.11.9`.

---

## 5. Wire Protocol & Serialization Compatibility

The SDK enforces strict backward and forward compatibility rules for wire serialization:
- **JSON Serialization:** Uses fast standard library / Pydantic JSON serializers. Unknown incoming fields in response payloads are ignored by default (`extra = "ignore"`) to prevent minor server schema expansions from breaking existing client versions.
- **Protobuf Serialization (gRPC):** Utilizes Protocol Buffers proto3 with field tags, ensuring backward-compatible field addition.
- **Date & Time Formats:** All timestamps on the wire are encoded as ISO 8601 strings in UTC (`YYYY-MM-DDTHH:MM:SS.ffffffZ`).
