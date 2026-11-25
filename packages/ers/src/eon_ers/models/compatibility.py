"""Semantic version, modality, and CPU runtime compatibility checks for ERS models."""

from __future__ import annotations

import platform

from eon_ers.models.manifest import ModelManifest
from eon_ers.types import Modality


def check_manifest_compatibility(
    manifest: ModelManifest,
    *,
    expected_modality: Modality | None = None,
    supported_major_versions: set[int] | None = None,
) -> tuple[bool, list[str]]:
    """Verify semantic version, modality, framework, and CPU execution support."""
    reasons: list[str] = []
    if manifest.framework.lower() != "onnx":
        reasons.append(f"Unsupported framework '{manifest.framework}'; expected 'onnx'.")
    if expected_modality is not None and manifest.modality != expected_modality:
        reasons.append(
            f"Modality mismatch: manifest '{manifest.modality.value}' != '{expected_modality.value}'."
        )
    if not manifest.cpu_supported:
        reasons.append("Model manifest declares cpu_supported=False; CPU support is mandatory.")
    if "CPUExecutionProvider" not in manifest.accelerator_support:
        reasons.append("CPUExecutionProvider missing from manifest.accelerator_support.")

    allowed = supported_major_versions or {1}
    try:
        major = int(manifest.version.split(".")[0])
    except (ValueError, IndexError):
        reasons.append(f"Malformed semantic version '{manifest.version}'.")
    else:
        if major not in allowed:
            reasons.append(
                f"Incompatible model major version {major}; supported {sorted(allowed)}."
            )

    return len(reasons) == 0, reasons


def get_runtime_compatibility_report() -> dict[str, str]:
    """Return host runtime compatibility summary for registry and API diagnostics."""
    return {
        "python": platform.python_version(),
        "architecture": platform.machine() or "unknown",
        "required_provider": "CPUExecutionProvider",
    }
