"""Integration tests for package distribution archives, metadata, and installation."""

import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def dist_directory() -> Path:
    """Ensure wheel and sdist exist in dist/, building them if necessary."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    dist_dir = repo_root / "dist"
    wheel_files = list(dist_dir.glob("*.whl")) if dist_dir.exists() else []
    sdist_files = list(dist_dir.glob("*.tar.gz")) if dist_dir.exists() else []

    if not wheel_files or not sdist_files:
        dist_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "build", "--outdir", str(dist_dir)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=True,
        )
    return dist_dir


def test_built_wheel_archive_contains_py_typed(dist_directory: Path) -> None:
    """AC-PH1.1-12: Verify that built wheel contains the PEP 561 py.typed marker."""
    wheels = list(dist_directory.glob("*.whl"))
    assert len(wheels) > 0, "No built wheel found in dist directory"
    wheel_path = wheels[0]

    with zipfile.ZipFile(wheel_path) as zf:
        namelist = zf.namelist()
        assert "eon/py.typed" in namelist


def test_built_wheel_contains_all_architectural_subpackages(dist_directory: Path) -> None:
    """AC-PH1.1-01: Verify that built wheel contains all seven architectural boundaries."""
    wheels = list(dist_directory.glob("*.whl"))
    assert len(wheels) > 0
    wheel_path = wheels[0]

    expected_files = [
        "eon/__init__.py",
        "eon/py.typed",
        "eon/core/__init__.py",
        "eon/interfaces/__init__.py",
        "eon/safety/__init__.py",
        "eon/schemas/__init__.py",
        "eon/sdk/__init__.py",
        "eon/transports/__init__.py",
    ]
    with zipfile.ZipFile(wheel_path) as zf:
        namelist = zf.namelist()
        for expected in expected_files:
            assert expected in namelist, f"Missing architectural package file in wheel: {expected}"


def test_built_wheel_metadata_matches_specification(dist_directory: Path) -> None:
    """AC-PH1.1-02, AC-PH1.1-05: Verify wheel METADATA adheres to package specifications."""
    wheels = list(dist_directory.glob("*.whl"))
    assert len(wheels) > 0
    wheel_path = wheels[0]

    with zipfile.ZipFile(wheel_path) as zf:
        metadata_entry = next((name for name in zf.namelist() if name.endswith("/METADATA")), None)
        assert metadata_entry is not None, "METADATA not found in wheel archive"
        metadata_text = zf.read(metadata_entry).decode("utf-8")

        assert "Name: ovic-eon" in metadata_text
        assert "Version: 0.1.0" in metadata_text
        assert (
            "Requires-Python: <3.13,>=3.10" in metadata_text
            or "Requires-Python: >=3.10,<3.13" in metadata_text
        )
        assert "Summary: Emotional Intelligence Infrastructure for Robotics." in metadata_text
        assert "Requires-Dist: pydantic>=2.0.0" in metadata_text


def test_built_wheel_excludes_unwanted_files(dist_directory: Path) -> None:
    """Verify that development files, tests, and caches are strictly excluded from wheel."""
    wheels = list(dist_directory.glob("*.whl"))
    assert len(wheels) > 0
    wheel_path = wheels[0]

    forbidden_patterns = [
        "tests/",
        "docs/",
        "scripts/",
        ".github",
        ".ruff_cache",
        ".pytest_cache",
        "__pycache__",
        ".pyc",
        ".git",
    ]
    with zipfile.ZipFile(wheel_path) as zf:
        for name in zf.namelist():
            for forbidden in forbidden_patterns:
                assert forbidden not in name, (
                    f"Forbidden file or pattern '{forbidden}' found in wheel entry '{name}'"
                )


def test_built_sdist_archive_contents(dist_directory: Path) -> None:
    """AC-PH1.1-12: Verify sdist contains required build files and excludes caches."""
    sdists = list(dist_directory.glob("*.tar.gz"))
    assert len(sdists) > 0, "No built sdist found in dist directory"
    sdist_path = sdists[0]

    with tarfile.open(sdist_path, "r:gz") as tf:
        names = tf.getnames()
        # Look for essential files under the top-level sdist directory
        assert any(n.endswith("pyproject.toml") for n in names)
        assert any(n.endswith("README.md") for n in names)
        assert any(n.endswith("src/eon/py.typed") for n in names)
        assert not any(".pytest_cache" in n or ".ruff_cache" in n or ".pyc" in n for n in names)


def test_wheel_installation_and_isolated_import(dist_directory: Path) -> None:
    """AC-PH1.1-03, AC-PH1.1-04: Test isolated installation and importation of built wheel."""
    wheels = list(dist_directory.glob("*.whl"))
    assert len(wheels) > 0
    wheel_path = wheels[0]

    with tempfile.TemporaryDirectory() as target_dir:
        # Install wheel into isolated target directory without touching global packages
        install_cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--target",
            target_dir,
            str(wheel_path),
        ]
        if sys.version_info >= (3, 13):
            install_cmd.append("--ignore-requires-python")

        install_res = subprocess.run(install_cmd, capture_output=True, text=True, check=True)
        assert install_res.returncode == 0

        # Import eon strictly from the isolated target directory in a fresh subprocess
        import_cmd = [
            sys.executable,
            "-c",
            f"import sys; sys.path.insert(0, {repr(target_dir)}); "
            "import eon; "
            "assert eon.__title__ == 'ovic-eon'; "
            "assert eon.__version__ == '0.1.0'; "
            "print('ISOLATED_WHEEL_IMPORT_OK')",
        ]
        import_res = subprocess.run(
            import_cmd,
            cwd=tempfile.gettempdir(),
            capture_output=True,
            text=True,
            check=True,
        )
        assert "ISOLATED_WHEEL_IMPORT_OK" in import_res.stdout
