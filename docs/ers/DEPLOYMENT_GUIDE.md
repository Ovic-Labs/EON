# Production CPU-First Deployment Guide

## Container Stack (`Dockerfile` & `docker-compose.yml`)
OVIC EON ERS ships with a hardened non-root Python 3.11 CPU container (`Dockerfile`) and an Nginx TLS reverse proxy stack (`docker-compose.yml` + `deploy/nginx.conf`).

### Security Highlights
- Runs as unprivileged `ersuser` inside `python:3.11-slim`.
- Upgrades `pip` and `setuptools>=84.1.0` during image build.
- Compose enforces `read_only: true`, `tmpfs` `/tmp`, CPU (`4.0`) and RAM (`1024M`) resource limits, TLS 1.2/1.3 termination, rate limiting (`limit_req`), and WebSocket timeouts.
- Models are mounted read-only (`/app/packages/ers/models:ro`).

### Quick Start with Docker Compose
1. Place TLS certificate/key in `./deploy/certs/server.crt` and `./deploy/certs/server.key`.
2. Configure secrets from [deploy/env.example](../../deploy/env.example) outside version control.
3. Build and start:

```bash
docker compose up -d --build
```

4. Verify probes:

```bash
curl -k https://localhost/health
curl -k https://localhost/ready
```
