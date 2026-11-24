"""Runnable script for launching the OVIC EON ERS Live Demonstration.

Usage:
    python packages/ers/examples/live_demo.py
    python packages/ers/examples/live_demo.py --port 8080 --open-browser
"""

from __future__ import annotations

import sys

from eon_ers.live.cli import main

if __name__ == "__main__":
    sys.exit(main())
