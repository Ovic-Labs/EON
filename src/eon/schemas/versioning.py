"""Schema versioning contracts and Semantic Versioning compatibility policies."""

import re
from typing import Final

from eon.schemas.base import EonBaseModel

SEMVER_PATTERN: Final[str] = (
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)
_SEMVER_REGEX = re.compile(SEMVER_PATTERN)

CURRENT_SCHEMA_VERSION: Final[str] = "1.0.0"
SUPPORTED_SCHEMA_VERSIONS: Final[frozenset[str]] = frozenset({"1.0.0"})


class SchemaVersion(EonBaseModel):
    """Semantic Versioning (SemVer 2.0.0) representation for EON schema contracts."""

    version_str: str

    @property
    def major(self) -> int:
        """Extract major version integer."""
        match = _SEMVER_REGEX.match(self.version_str)
        if not match:
            raise ValueError(f"Invalid SemVer string: {self.version_str}")
        return int(match.group(1))

    @property
    def minor(self) -> int:
        """Extract minor version integer."""
        match = _SEMVER_REGEX.match(self.version_str)
        if not match:
            raise ValueError(f"Invalid SemVer string: {self.version_str}")
        return int(match.group(2))

    @property
    def patch(self) -> int:
        """Extract patch version integer."""
        match = _SEMVER_REGEX.match(self.version_str)
        if not match:
            raise ValueError(f"Invalid SemVer string: {self.version_str}")
        return int(match.group(3))

    def is_compatible_with(self, expected: "SchemaVersion") -> bool:
        """Check if this version can be consumed by an engine expecting `expected`.

        For post-1.0.0 releases, major versions must match exactly, and this version
        must have minor >= expected.minor.
        For 0.x.y releases, major and minor must match exactly.
        """
        if self.major != expected.major:
            return False
        if self.major == 0:
            return self.minor == expected.minor
        return self.minor >= expected.minor

    def is_breaking_change(self, target: "SchemaVersion") -> bool:
        """Return True if transitioning from this version to target is breaking."""
        return not target.is_compatible_with(self)


def validate_schema_version(version_str: str) -> None:
    """Validate that a schema version string is well-formed SemVer and supported."""
    if not _SEMVER_REGEX.match(version_str):
        raise ValueError(
            f"Schema version '{version_str}' is not a valid Semantic Version (MAJOR.MINOR.PATCH)."
        )
    if version_str not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported schema version: '{version_str}'. "
            f"Supported versions: {sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
