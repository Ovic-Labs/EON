# Contributing to OVIC EON

Thank you for contributing to OVIC EON and the Emotion Recognition System (ERS).

## Core Engineering & Scientific Rules

1. **CPU-First Edge Execution:** Every pipeline must execute locally on standard x86_64/ARM CPUs without mandatory GPUs or external cloud AI APIs.
2. **Epistemic Modesty:** Emotion outputs reflect observable behavioural signals, never definitive truths about inner psychological feelings (`is_definitive_claim = False` must remain strictly frozen).
3. **Fail-Closed Integrity:** Never fabricate confidence scores, mock model inference outputs in production paths, or bypass SHA-256 / Ed25519 / consent checks.
4. **No Actuator Control:** `eon_ers.safety.actuator_isolation` strictly prohibits emitting robot motion or actuator keys (`cmd_vel`, `actuator`, `motor`, `torque`, etc.).
5. **No Secrets or Restricted Datasets in Git:** Keep `.pem` private signing keys, API keys, and unredistributable datasets (`AffectNet`, `RAF-DB`, `RAVDESS`, `CREMA-D`) out of version control.

## Local Verification Before Committing

```bash
ruff check .
ruff format --check .
mypy packages/ers/src
python -m pytest packages/ers/tests -v --cov=eon_ers
pip-audit --desc
```
