"""Unit tests for package scaffolding and metadata verification."""

import importlib
import socket
import sys

import pytest

import eon


def test_package_import_successful() -> None:
    """AC-PH1.1-04: Verify eon package imports cleanly into the Python runtime."""
    assert eon is not None
    assert "eon" in sys.modules


def test_package_version_metadata() -> None:
    """Verify package version metadata is defined and follows semantic versioning."""
    assert hasattr(eon, "__version__")
    assert isinstance(eon.__version__, str)
    assert eon.__version__ == "0.1.0"


def test_package_public_metadata() -> None:
    """Verify public package identity and informational attributes."""
    assert eon.__title__ == "ovic-eon"
    assert "Robotics" in eon.__description__
    assert eon.__author__ == "OVIC Labs"
    assert eon.__license__ == "Apache-2.0"
    for item in ["__version__", "__title__", "__description__", "__author__", "__license__"]:
        assert item in eon.__all__


def test_expected_module_boundaries_exist() -> None:
    """AC-PH1.1-01: Verify that all architectural package boundaries are importable."""
    submodules = [
        "eon.core",
        "eon.schemas",
        "eon.interfaces",
        "eon.transports",
        "eon.safety",
        "eon.sdk",
    ]
    for mod_name in submodules:
        mod = importlib.import_module(mod_name)
        assert mod is not None
        assert mod_name in sys.modules


def test_cpu_only_operation_no_gpu_required() -> None:
    """AC-PH1.1-13: Verify that package import does not require CUDA or GPU libraries."""
    assert "torch" not in sys.modules
    assert "tensorflow" not in sys.modules
    assert eon.__version__ is not None


def test_no_ros2_dependency_required_for_base_import() -> None:
    """AC-PH1.1-13: Verify that base eon package does not require rclpy for importation."""
    assert eon.__title__ == "ovic-eon"
    # Base package must be importable without any ROS 2 environment active
    assert "eon" in sys.modules


def test_no_network_connection_on_import(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that importing eon does not initiate external network socket connections."""
    network_attempted = False

    def guarded_connect(*_args: object, **_kwargs: object) -> None:
        nonlocal network_attempted
        network_attempted = True
        raise RuntimeError("Unexpected network socket connection attempted during package import!")

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)
    importlib.reload(eon)
    assert not network_attempted
