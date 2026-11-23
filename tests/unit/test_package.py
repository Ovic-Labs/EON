"""Unit tests for package scaffolding and metadata verification."""

import importlib
import subprocess
import sys
import tempfile

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
    """AC-PH1.1-13: Verify that package import does not require CUDA or GPU libraries.

    Runs in an isolated subprocess to guarantee that neither torch, tensorflow,
    nor jax are imported during base package import.
    """
    code = (
        "import sys\n"
        "import eon\n"
        "for forbidden in ['torch', 'tensorflow', 'jax']:\n"
        "    assert forbidden not in sys.modules, f'Unexpected GPU module imported: {forbidden}'\n"
        "print('CPU_ONLY_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "CPU_ONLY_OK" in result.stdout


def test_no_ros2_dependency_required_for_base_import() -> None:
    """AC-PH1.1-13: Verify that base eon package does not require ROS 2 (rclpy/rospy).

    Runs in an isolated subprocess where rclpy and rospy are blocked from importing.
    """
    code = (
        "import sys\n"
        "sys.modules['rclpy'] = None\n"
        "sys.modules['rospy'] = None\n"
        "import eon\n"
        "assert eon.__title__ == 'ovic-eon'\n"
        "assert 'rclpy' not in sys.modules or sys.modules['rclpy'] is None\n"
        "print('ROS2_INDEPENDENT_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "ROS2_INDEPENDENT_OK" in result.stdout


def test_no_network_connection_on_import() -> None:
    """Verify that importing eon does not initiate external network socket connections.

    Runs in a fresh isolated subprocess where network socket calls are trapped before import.
    """
    code = (
        "import socket\n"
        "import sys\n"
        "def guarded_connect(*_args, **_kwargs):\n"
        "    raise RuntimeError('Unexpected socket connection attempt!')\n"
        "socket.socket.connect = guarded_connect\n"
        "socket.socket.connect_ex = guarded_connect\n"
        "socket.create_connection = guarded_connect\n"
        "import eon\n"
        "assert eon.__version__ == '0.1.0'\n"
        "print('NETWORK_ISOLATED_OK')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "NETWORK_ISOLATED_OK" in result.stdout


def test_import_from_arbitrary_working_directory() -> None:
    """AC-PH1.1-04: Verify that eon is importable from outside the repository root."""
    code = "import eon\nprint(eon.__version__)\n"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=tempfile.gettempdir(),
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip() == "0.1.0"
