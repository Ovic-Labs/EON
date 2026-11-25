# Production CPU-First Deployment Guide

## Clean Installation & Local Preview (CPU-First)
```bash
python -m pip install --upgrade pip "setuptools>=84.1.0"
pip install -e "packages/ers[dev,ml,live]"
eon-ers-live --host 127.0.0.1 --port 8000
```
Standard local preview URL: `http://127.0.0.1:8000/`.
Note: There is **no** public cloud deployment in this repository release; containerized production deployment runs locally or behind your own TLS reverse proxy (`Dockerfile`, `docker-compose.yml`, `deploy/nginx.conf`).

### Environment Variables
| Variable | Purpose | Default |
| --- | --- | --- |
| `EON_ERS_API_AUTH` | Enforce API key auth & RBAC across `/api/v1/*`, `/api/*`, `/ws/*` | `false` |
| `EON_ERS_BOOTSTRAP_API_KEYS` | Comma-separated `principal_id:role:secret` API keys | unset |
| `EON_ERS_CORS_ORIGINS` | Allowed browser origins (wildcards stripped) | localhost/127.0.0.1 ports `8000,3000,8080` |
| `EON_ERS_SIGNING_KEY_ID` | Ed25519 manifest signing key ID | unset |
| `EON_ERS_SIGNING_PRIVATE_KEY_PATH` | Path to mounted private signing PEM | unset |
| `OMP_NUM_THREADS` | CPU thread bound for runtime inference | `4` |

## Container Stack (`Dockerfile` & `docker-compose.yml`)
OVIC EON ERS ships with a hardened non-root Python 3.11 CPU container (`Dockerfile`) and an Nginx TLS reverse proxy stack (`docker-compose.yml` + `deploy/nginx.conf`).

### Security Highlights
- Runs as unprivileged `ersuser` inside `python:3.11-slim`.
- Upgrades `pip` and `setuptools>=84.1.0` during image build.
- Compose enforces `read_only: true`, `tmpfs` `/tmp`, CPU (`4.0`) and RAM (`1024M`) resource limits, TLS 1.2/1.3 termination, rate limiting (`limit_req`), and WebSocket timeouts.
- Models are mounted read-only (`/app/packages/ers/models:ro`).

### Quick Start with Docker Compose
1. Place TLS certificate/key in `./deploy/certs/server.crt` and `./deploy/certs/server.key`.
2. Configure secrets from [deploy/env.example](../../deploy/env.example) outside version control:
   - `EON_ERS_API_AUTH=true` enables fail-closed RBAC & session-ownership checks on all `/api/v1/*`, legacy `/api/*`, and WebSocket (`/ws/*`) endpoints.
   - `EON_ERS_BOOTSTRAP_API_KEYS` accepts comma-separated `principal_id:role:secret` entries for API key authentication (`X-API-Key` HTTP header or post-connect WebSocket `{"type": "auth", "api_key": "..."}` message; query-string secrets are rejected).
   - `EON_ERS_CORS_ORIGINS` sets explicit comma-separated allowed browser origins (`*` wildcards are stripped).
3. Build and start (`deploy/nginx.conf` disables proxy buffering on WebSocket routes with `proxy_buffering off;` and forwards `X-Forwarded-*` headers):

```bash
docker compose up -d --build
```

4. Verify probes:

```bash
curl -k https://localhost/health
curl -k https://localhost/ready
```
