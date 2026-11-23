"""Integration tests for package scaffolding and module imports."""

import importlib
import sys


def test_full_package_tree_importable() -> None:
    """Verify that the full package tree can be navigated and reloaded cleanly."""
    package_names = [
        "eon",
        "eon.core",
        "eon.schemas",
        "eon.interfaces",
        "eon.transports",
        "eon.safety",
        "eon.sdk",
    ]
    for name in package_names:
        mod = importlib.import_module(name)
        assert mod is not None
        assert name in sys.modules
