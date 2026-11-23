# OVIC EON — Developer Installation and Setup Guide

**Document ID:** EON-DEV-INST-001  
**Product:** OVIC EON  
**Tagline:** Emotional Intelligence Infrastructure for Robotics  
**Organization:** OVIC Labs  
**Target Milestone:** Phase 1 — Engineering Infrastructure & Core Runtime Foundation  
**Version:** 0.1.0  
**Last Verified:** 2026-11-23  

---

## 1. Overview and Prerequisites

OVIC EON uses a modern PEP 621-compliant `pyproject.toml` configuration with the `src-layout` packaging architecture. The base installation is lightweight and CPU-first; it requires no GPU drivers, CUDA libraries, ROS 2 middleware, or cloud dependencies.

### Supported Python Versions
- **Primary Supported Versions:** Python 3.10, 3.11, 3.12 (`>=3.10,<3.13`).
- **Operating Systems Supported:**
  - Ubuntu Linux 22.04 LTS / 24.04 LTS.
  - Windows 10 / Windows 11 (PowerShell).
  - Windows Subsystem for Linux (WSL2 Ubuntu).

---

## 2. Environment Setup

### 2.1 Clone Repository
```bash
git clone https://github.com/Ovic-Labs/EON.git
cd EON
```

### 2.2 Windows PowerShell Installation

1. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```

2. If script execution is restricted on Windows, allow current process execution:
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   ```

3. Activate the virtual environment:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Upgrade pip and install package in editable mode with development dependencies:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```

### 2.3 Linux / WSL Ubuntu Installation

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```

2. Activate the virtual environment:
   ```bash
   source .venv/bin/activate
   ```

3. Upgrade pip and install package in editable mode with development dependencies:
   ```bash
   python -m pip install --upgrade pip
   python -m pip install -e ".[dev]"
   ```

---

## 3. Developer Quality and Verification Workflow

Execute the full verification and linting suite using these verified commands:

### 3.1 Execute Test Suite
Run the test runner with strict markers and coverage analysis:
```bash
python -m pytest
```

Generate detailed line-by-line coverage reports:
```bash
python -m pytest --cov=eon --cov-report=term-missing
```

### 3.2 Linting and Formatting with Ruff
Check code style and lint rules (configured for 100-character line length):
```bash
python -m ruff check .
```

Verify formatting without modifying files:
```bash
python -m ruff format --check .
```

Automatically apply formatting fixes:
```bash
python -m ruff format .
python -m ruff check --fix .
```

### 3.3 Strict Static Type Checking with Mypy
Validate that all implemented Python modules comply with strict type rules:
```bash
python -m mypy src/eon
```

### 3.4 Build Distribution Packages
Build source distribution (`.tar.gz`) and standard binary wheel (`.whl`):
```bash
python -m build
```
Built artifacts are placed in the `dist/` directory (ignored by `.gitignore`).

### 3.5 Security Audit with pip-audit
Verify that no installed runtime or development dependencies have known vulnerabilities:
```bash
python -m pip_audit
```
Note: `ovic-eon` itself will be reported as skipped because it is a local package not yet published on PyPI.

### 3.6 Governance and Documentation Audit
Run the automated documentation qualification suite:
```bash
python scripts/validate_docs.py
npx --yes markdownlint-cli2 "**/*.md"
```

---

## 4. Troubleshooting and Common Errors

### 4.1 Python Version Mismatch
- **Symptom:** `ERROR: Package 'ovic-eon' requires a different Python: ... not in '<3.13,>=3.10'`
- **Cause:** The current Python interpreter is outside the declared `>=3.10,<3.13` support range.
- **Resolution:** Use a supported Python 3.10–3.12 interpreter, or if testing experimental builds on newer Python interpreters, pass the pip flag:
  ```bash
  python -m pip install --ignore-requires-python -e ".[dev]"
  ```

### 4.2 PowerShell Script Execution Disabled
- **Symptom:** `.venv\Scripts\Activate.ps1 cannot be loaded because running scripts is disabled on this system.`
- **Resolution:** Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process` in the current PowerShell terminal session before activating.

### 4.3 Missing Build Backend
- **Symptom:** `ModuleNotFoundError: No module named 'hatchling'`
- **Resolution:** Ensure pip is up to date (`python -m pip install --upgrade pip`). Modern pip will automatically fetch `hatchling` in an isolated build environment during installation.

### 4.4 Import Verification Outside Source Directory
To verify that the editable install registered properly with Python site-packages:
```powershell
# Change directory outside repo
cd $env:TEMP
python -c "import eon; print('Loaded', eon.__title__, eon.__version__)"
```
Expected output:
```text
Loaded ovic-eon 0.1.0
```
