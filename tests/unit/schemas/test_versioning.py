"""Unit tests for schema versioning and compatibility policies."""

import pytest

from eon.schemas.versioning import (
    CURRENT_SCHEMA_VERSION,
    SchemaVersion,
    validate_schema_version,
)


def test_semver_parsing() -> None:
    """AC-1.2-11: Verify Semantic Versioning component extraction."""
    sv = SchemaVersion(version_str="1.2.3")
    assert sv.major == 1
    assert sv.minor == 2
    assert sv.patch == 3

    sv_pre = SchemaVersion(version_str="2.0.0-alpha.1")
    assert sv_pre.major == 2
    assert sv_pre.minor == 0
    assert sv_pre.patch == 0


def test_semver_invalid_string() -> None:
    """Verify invalid SemVer strings raise ValueError."""
    sv = SchemaVersion(version_str="not_semver")
    with pytest.raises(ValueError):
        _ = sv.major


def test_schema_compatibility_rules() -> None:
    """AC-1.2-11: Verify backward compatibility and breaking change checks."""
    v1_0 = SchemaVersion(version_str="1.0.0")
    v1_1 = SchemaVersion(version_str="1.1.0")
    v2_0 = SchemaVersion(version_str="2.0.0")

    # 1.1.0 can satisfy a consumer expecting 1.0.0
    assert v1_1.is_compatible_with(v1_0)
    # 1.0.0 cannot satisfy a consumer requiring 1.1.0
    assert not v1_0.is_compatible_with(v1_1)

    # Major version change is breaking
    assert not v2_0.is_compatible_with(v1_0)
    assert v1_0.is_breaking_change(v2_0)

    # 0.x.y version compatibility rules
    v0_1_0 = SchemaVersion(version_str="0.1.0")
    v0_1_5 = SchemaVersion(version_str="0.1.5")
    v0_2_0 = SchemaVersion(version_str="0.2.0")

    assert v0_1_0.is_compatible_with(v0_1_5)
    assert not v0_1_0.is_compatible_with(v0_2_0)


def test_validate_schema_version_supported() -> None:
    """AC-1.2-11: Verify CURRENT_SCHEMA_VERSION passes validation."""
    validate_schema_version(CURRENT_SCHEMA_VERSION)


def test_validate_schema_version_unsupported_raises() -> None:
    """Verify unsupported major or future versions raise explicit error."""
    with pytest.raises(ValueError) as exc:
        validate_schema_version("2.0.0")
    assert "Unsupported schema version" in str(exc.value)

    with pytest.raises(ValueError) as exc:
        validate_schema_version("invalid")
    assert "not a valid Semantic Version" in str(exc.value)
