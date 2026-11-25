# ERS Developer and Integration Guide

## Overview

OVIC EON ERS operates CPU-first across Python 3.11 and 3.12 using `ERSEngine`, REST/WebSocket endpoints, or `eon_ers.sdk.ERSClient`.

## Key Engineering Guarantees
- **Epistemic Modesty:** Every `EmotionObservation`, `FusionResult`, and `VideoAnalysisJobResult` enforces `is_definitive_claim = False`.
- **Consent & Scrubbing:** Consent tokens are SHA-256 hashed (`ConsentManager`); raw buffers are scrubbed on success, consent rejection, and error paths via `scrub_media_payload()`.
- **Validation Isolation:** Unvalidated models stay marked `MODEL_UNVALIDATED` and cannot promote into classification weights or registry activation.
- **No Actuation:** `CoreEventBusAdapter` and `eon_ers.safety.actuator_isolation` block any physical robot motion keys.

## Using the Python SDK (`ERSClient`)

```python
import asyncio
from eon_ers.config import ERSConfig
from eon_ers.sdk import ERSClient


async def main() -> None:
    async with ERSClient(config=ERSConfig()) as client:
        await client.register_consent("dev-sess-1", "consent-token-xyz")
        obs = await client.analyze_text("dev-sess-1", "consent-token-xyz", "I feel glad today.")
        print(obs.modality.value, obs.status.value, obs.is_definitive_claim)
        await client.revoke_consent("dev-sess-1")


asyncio.run(main())
```

## Ed25519 Signing Key Provisioning (Institutional Training Runs)

Never store private `.pem` files in Git. Set environment variables outside source control:

```bash
export EON_ERS_SIGNING_KEY_ID="institution-ers-key-2026"
export EON_ERS_SIGNING_PRIVATE_KEY_PATH="/secure/path/private_ed25519.pem"
```

## Verification Gates

```bash
ruff check .
ruff format --check .
mypy packages/ers/src
python -m pytest packages/ers/tests -v --cov=eon_ers --cov-report=term-missing
pip-audit --desc
```
