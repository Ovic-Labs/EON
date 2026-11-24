"""Model manifest metadata specification and cryptographic integrity verification."""

from __future__ import annotations

import hashlib
import os
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.types import Modality


class ModelManifest(BaseModel):
    """Cryptographically verifiable specification for local model artifacts.

    Enforces strict provenance, licensing evidence, input/output tensor contracts,
    and cryptographic SHA-256 integrity verification.
    """

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
    commercial_use_allowed: bool = Field(
        default=False, description="Whether commercial use is permissible."
    )
    commercial_use_status: str = Field(
        default="RESTRICTED",
        description="Commercial qualification status (e.g., 'RESTRICTED', 'UNVERIFIED', 'APPROVED').",
    )
    provenance_status: str = Field(
        default="UNVERIFIED",
        description="Provenance verification status (e.g., 'VERIFIED', 'UNVERIFIED', 'SYNTHETIC').",
    )
    training_dataset_provenance: str = Field(
        default="UNVERIFIED",
        description="Exact dataset name, licensing, and lineage used for training.",
    )
    training_procedure: str = Field(
        default="UNVERIFIED",
        description="Training and optimization methodology, loss function, and epoch count.",
    )
    validation_status: str = Field(
        default="UNVERIFIED",
        description="Independent evaluation status and benchmark qualification evidence.",
    )
    license_evidence: str = Field(
        default="UNVERIFIED",
        description="Documentation or legal proof authorizing model weights distribution.",
    )
    source: str = Field(..., description="Originating repository, lab, or trained architecture.")
    input_specification: dict[str, Any] = Field(
        ..., description="Expected input tensor shape, name, and dtype."
    )
    output_specification: dict[str, Any] = Field(
        ..., description="Expected output tensor shape, name, and classes."
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

    def validate_tensor_contracts(self, session: Any) -> tuple[bool, str]:
        """Validate that the loaded ONNX session inputs and outputs match the manifest."""
        try:
            inputs = session.get_inputs()
            outputs = session.get_outputs()

            # Validate input tensor specification
            if not inputs:
                return False, "ONNX model has no input tensors."

            actual_in = inputs[0]
            expected_in_name = self.input_specification.get("name")
            expected_in_shape = self.input_specification.get("shape")
            expected_in_dtype = self.input_specification.get("dtype")

            if expected_in_name and actual_in.name != expected_in_name:
                return (
                    False,
                    f"Input tensor name mismatch: expected '{expected_in_name}', got '{actual_in.name}'.",
                )

            if expected_in_shape is not None:
                if len(actual_in.shape) != len(expected_in_shape):
                    return (
                        False,
                        f"Input tensor rank mismatch: expected {len(expected_in_shape)}D, got {len(actual_in.shape)}D.",
                    )
                if list(actual_in.shape) != list(expected_in_shape):
                    return (
                        False,
                        f"Input tensor shape mismatch: expected {expected_in_shape}, got {actual_in.shape}.",
                    )

            if expected_in_dtype or hasattr(actual_in, "type"):
                valid_float_types = ("tensor(float)", "tensor(float32)")
                if actual_in.type not in valid_float_types:
                    return (
                        False,
                        f"Input tensor dtype invalid: expected floating point tensor, got '{actual_in.type}'.",
                    )

            # Validate output tensor specification
            if not outputs:
                return False, "ONNX model has no output tensors."

            actual_out = outputs[0]
            expected_out_name = self.output_specification.get("name")
            expected_out_shape = self.output_specification.get("shape")
            expected_classes = self.output_specification.get("classes")

            if expected_out_name and actual_out.name != expected_out_name:
                return (
                    False,
                    f"Output tensor name mismatch: expected '{expected_out_name}', got '{actual_out.name}'.",
                )

            if expected_out_shape is not None:
                if len(actual_out.shape) != len(expected_out_shape):
                    return (
                        False,
                        f"Output tensor rank mismatch: expected {len(expected_out_shape)}D, got {len(actual_out.shape)}D.",
                    )
                if list(actual_out.shape) != list(expected_out_shape):
                    return (
                        False,
                        f"Output tensor shape mismatch: expected {expected_out_shape}, got {actual_out.shape}.",
                    )

            if hasattr(actual_out, "type"):
                valid_float_types = ("tensor(float)", "tensor(float32)")
                if actual_out.type not in valid_float_types:
                    return (
                        False,
                        f"Output tensor dtype invalid: expected floating point tensor, got '{actual_out.type}'.",
                    )

            if expected_classes is not None and expected_out_shape is not None:
                expected_num_classes = len(expected_classes)
                if len(actual_out.shape) > 0 and actual_out.shape[-1] != expected_num_classes:
                    return (
                        False,
                        f"Output class dimension mismatch: expected {expected_num_classes} classes, got dimension {actual_out.shape[-1]}.",
                    )

            return True, "Tensor contracts verified."
        except Exception as exc:
            return False, f"Tensor contract validation exception: {exc}"

    def validate_class_ordering(self, expected_classes: list[str]) -> tuple[bool, str]:
        """Validate that output classes defined in manifest match the required ordering."""
        manifest_classes = self.output_specification.get("classes", [])
        if manifest_classes != expected_classes:
            return (
                False,
                f"Class ordering mismatch: manifest classes {manifest_classes} != expected {expected_classes}",
            )
        return True, "Class ordering verified."
