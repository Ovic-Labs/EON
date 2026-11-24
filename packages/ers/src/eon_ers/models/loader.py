"""Model loader and runtime session builder with mandatory integrity verification."""

from __future__ import annotations

import os
from typing import Any

from eon_ers.exceptions import ERSModelExecutionError, ERSModelUnavailableError
from eon_ers.models.manifest import ModelManifest


class ModelLoader:
    """Safely loads model artifacts after validating cryptographic integrity."""

    @staticmethod
    def load_onnx_session(
        manifest: ModelManifest,
        base_dir: str | None = None,
        num_threads: int = 4,
    ) -> Any:
        """Load an ONNX Runtime InferenceSession with verified SHA-256 integrity."""
        path = manifest.artifact_path
        if base_dir and not os.path.isabs(path):
            path = os.path.join(base_dir, path)

        if not os.path.isfile(path):
            raise ERSModelUnavailableError(
                f"Model file '{path}' for model '{manifest.model_id}' does not exist."
            )

        # Cryptographic integrity check
        if not manifest.verify_integrity(base_dir):
            raise ERSModelExecutionError(
                f"Model integrity verification failed for '{manifest.model_id}'. SHA-256 mismatch!"
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
            return session
        except Exception as exc:
            raise ERSModelExecutionError(
                f"Failed to initialize ONNX Runtime session for '{manifest.model_id}': {exc}"
            ) from exc
