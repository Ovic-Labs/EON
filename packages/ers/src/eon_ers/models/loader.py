"""Model loader and runtime session builder with mandatory integrity verification."""

from __future__ import annotations

import os
from typing import Any

from eon_ers.exceptions import (
    ERSModelExecutionError,
    ERSModelIntegrityError,
    ERSModelUnavailableError,
)
from eon_ers.models.manifest import ModelManifest


class ModelLoader:
    """Safely loads model artifacts after validating cryptographic integrity and tensor contracts."""

    @staticmethod
    def load_onnx_session(
        manifest: ModelManifest,
        base_dir: str | None = None,
        num_threads: int = 4,
        expected_classes: list[str] | None = None,
    ) -> Any:
        """Load an ONNX Runtime InferenceSession with verified SHA-256 integrity and tensor contracts.

        Raises:
            ERSModelUnavailableError: If the model file cannot be found.
            ERSModelIntegrityError: If checksum verification fails or tensor contracts mismatch.
            ERSModelExecutionError: If runtime initialization fails.
        """
        path = manifest.artifact_path
        if base_dir and not os.path.isabs(path):
            path = os.path.join(base_dir, path)

        if not os.path.isfile(path):
            raise ERSModelUnavailableError(
                f"Model file '{path}' for model '{manifest.model_id}' does not exist."
            )

        # 1. Mandatory Cryptographic integrity check
        if not manifest.verify_integrity(base_dir):
            raise ERSModelIntegrityError(
                f"Model integrity verification failed for '{manifest.model_id}'. "
                f"SHA-256 digest mismatch against manifest!"
            )

        # 2. Validate class ordering if expected classes provided
        if expected_classes is not None:
            valid_classes, class_err = manifest.validate_class_ordering(expected_classes)
            if not valid_classes:
                raise ERSModelIntegrityError(
                    f"Model '{manifest.model_id}' class ordering violation: {class_err}"
                )

        try:
            import onnxruntime as ort

            so = ort.SessionOptions()
            so.intra_op_num_threads = num_threads
            so.inter_op_num_threads = 1
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session = ort.InferenceSession(
                path, sess_options=so, providers=["CPUExecutionProvider"]
            )

            # 3. Validate input and output tensor contracts
            valid_tensors, tensor_err = manifest.validate_tensor_contracts(session)
            if not valid_tensors:
                raise ERSModelIntegrityError(
                    f"Model '{manifest.model_id}' tensor contract violation: {tensor_err}"
                )

            return session
        except (ERSModelIntegrityError, ERSModelUnavailableError):
            raise
        except Exception as exc:
            raise ERSModelExecutionError(
                f"Failed to initialize ONNX Runtime session for '{manifest.model_id}': {exc}"
            ) from exc
