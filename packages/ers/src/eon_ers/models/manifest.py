"""Model manifest metadata specification and cryptographic integrity verification."""

from __future__ import annotations

import hashlib
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.types import Modality


class ModelManifest(BaseModel):
    """Cryptographically verifiable specification for local model artifacts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(..., min_length=1, description="Unique model identifier.")
    name: str = Field(..., min_length=1, description="Human-readable model name.")
    version: str = Field(..., min_length=1, description="Semantic version string.")
    modality: Modality = Field(..., description="Target sensory modality.")
    framework: str = Field(default="onnx", description="Runtime framework ('onnx', 'openvino').")
    artifact_path: str = Field(..., description="Relative or absolute path to model weights.")
    sha256_checksum: str = Field(
        ..., min_length=64, max_length=64, description="SHA-256 digest of weights file."
    )
    license: str = Field(..., description="Open source or commercial software license.")
    commercial_use_allowed: bool = Field(..., description="Whether commercial use is permissible.")
    source: str = Field(..., description="Originating repository, lab, or trained architecture.")
    input_specification: dict[str, Any] = Field(
        ..., description="Expected input tensor shape and dtype."
    )
    output_specification: dict[str, Any] = Field(
        ..., description="Expected output tensor shape and classes."
    )
    cpu_supported: bool = Field(default=True, description="Whether CPU inference is supported.")
    accelerator_support: list[str] = Field(
        default_factory=list, description="Optional acceleration providers."
    )
    known_limitations: list[str] = Field(
        default_factory=list, description="Documented operational constraints."
    )

    def verify_integrity(self, base_dir: str | None = None) -> bool:
        """Verify that the model file exists and its SHA-256 matches the manifest digest."""
        path = self.artifact_path
        if base_dir and not os.path.isabs(path):
            path = os.path.join(base_dir, path)

        if not os.path.isfile(path):
            return False

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

        computed = hasher.hexdigest().lower()
        return computed == self.sha256_checksum.lower()
