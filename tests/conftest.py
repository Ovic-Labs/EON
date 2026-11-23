"""Test configuration and shared fixtures for OVIC EON test suites."""

import sys
from pathlib import Path

# Ensure src directory is present in sys.path for local discovery
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
