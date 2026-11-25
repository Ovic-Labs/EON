# ERS Installation Guide (CPU-First)

## Prerequisites
- **Python:** 3.11 or 3.12 (`>=3.11,<3.13`, required by `onnxruntime>=1.23.0` for shipped IR-14 ONNX graphs)
- **OS:** Linux (`x86_64`), Windows 10/11, or macOS (CPU-only compatible)
- **RAM:** >= 512 MB available (~162 MB host benchmark RSS observed)

## Install from Source

```bash
git clone https://github.com/Ovic-Labs/EON.git
cd EON
python -m pip install --upgrade pip "setuptools>=84.1.0"
pip install -e "packages/ers[ml,live,dev]"
```

## Verify Installation

```bash
python packages/ers/examples/quickstart.py
python -m pytest packages/ers/tests -q
```

## Optional Container Installation

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for the non-root `Dockerfile` and `docker-compose.yml` TLS deployment stack.
