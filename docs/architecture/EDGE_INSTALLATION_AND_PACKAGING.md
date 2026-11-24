# OVIC EON — Edge Installation and Packaging Specification

**Document ID:** `EON-SPEC-EDGE-002`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Release Engineers, Devops Engineers  
**Traceability:** `EON-ARCH-EDGE-001`, ADR-023  

---

## 1. Packaging Formats

To accommodate diverse commercial robotics deployment environments, EON supports three standardized distribution artifacts:

1. **Native Debian / RPM Packages (`.deb` / `.rpm`):**
   - Optimized for Ubuntu 22.04 / 24.04 and Debian 12 edge images.
   - Installs binaries to `/opt/ovic/eon/bin/`, libraries to `/opt/ovic/eon/lib/`, and default configurations to `/etc/ovic/eon/`.
   - Registers system users `eon` and groups `eon-clients`.
2. **OCI Container Images (Docker / Podman):**
   - Multi-architecture container images (`linux/amd64`, `linux/arm64`).
   - Minimal distroless or Alpine/Ubuntu-based base images with zero unnecessary shell utilities.
3. **Standalone Tarball (`.tar.gz`):**
   - Self-contained portable distribution with vendored C++ runtime dependencies for isolated air-gapped robot installations.

---

## 2. Directory Layout on Edge Storage

```text
/opt/ovic/eon/
├── bin/
│   ├── eond                     # Core runtime daemon
│   └── eon-cli                  # Local diagnostic and management CLI
├── lib/
│   ├── libeonsdk.so             # C++ SDK runtime library
│   └── adapters/                # Dynamic model adapter plugins
├── share/
│   └── models/                  # Base ONNX INT8 quantized model weights
/etc/ovic/eon/
│   ├── eon.yaml                 # Main configuration file
│   └── security/                # Device credentials and certificates
/var/lib/ovic/eon/
│   ├── context.db               # Encrypted SQLite context database
│   └── wal/                     # Database WAL directory
/var/run/ovic/eon/
│   ├── eon.sock                 # Unix domain IPC socket
│   └── eon.pid                  # Process lock file
```
