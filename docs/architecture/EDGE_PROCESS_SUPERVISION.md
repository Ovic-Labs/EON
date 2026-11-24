# OVIC EON — Edge Process Supervision Specification

**Document ID:** `EON-SPEC-EDGE-003`  
**Phase:** Phase 2 — System Architecture and Engineering Design (Sub-phase 2.14)  
**Status:** `DESIGNED — NOT IMPLEMENTED (Phase 2 Architecture Baseline)`  
**Target Audience:** Systems Software Engineers, Reliability Engineers  
**Traceability:** `EON-ARCH-EDGE-001`, ADR-023, ADR-028  

---

## 1. Systemd Service Specification

The production edge service is managed via `systemd`:

```ini
[Unit]
Description=OVIC EON Emotional Intelligence Core Service
After=network.target local-fs.target
Wants=systemd-udev-settle.service

[Service]
Type=notify
ExecStart=/opt/ovic/eon/bin/eond --config /etc/ovic/eon/eon.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=2s
StartLimitIntervalSec=60s
StartLimitBurst=5

# Sandboxing and Security Restrictions
User=eon
Group=eon
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ovic/eon /var/run/ovic/eon /dev/shm
PrivateTmp=true
CapabilityBoundingSet=CAP_SYS_NICE
AmbientCapabilities=CAP_SYS_NICE
NoNewPrivileges=true

# Watchdog Integration
WatchdogSec=5s

[Install]
WantedBy=multi-user.target
```

---

## 2. Hardware and Software Watchdogs

1. **Systemd Watchdog (`sd_notify("WATCHDOG=1")`):** EON Core pets the systemd watchdog every 2.0 seconds. If a deadlock occurs in the core event loop, systemd terminates and restarts the process.
2. **Hardware Watchdog (/dev/watchdog):** For critical robot platforms, EON registers health signals with the robot's main supervisory microcontroller.
