"""Model loader and runtime session builder with mandatory integrity and weight validation."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import numpy as np

from eon_ers.exceptions import (
    ERSModelExecutionError,
    ERSModelIntegrityError,
    ERSModelUnavailableError,
)
from eon_ers.models.manifest import ModelManifest


def _resolve_onnx_numpy_dtype(tensor_type: str) -> np.dtype[Any]:
    mapping: dict[str, np.dtype[Any]] = {
        "tensor(float)": np.dtype(np.float32),
        "tensor(float32)": np.dtype(np.float32),
        "tensor(double)": np.dtype(np.float64),
        "tensor(float64)": np.dtype(np.float64),
        "tensor(int64)": np.dtype(np.int64),
        "tensor(int32)": np.dtype(np.int32),
        "tensor(uint8)": np.dtype(np.uint8),
    }
    if tensor_type not in mapping:
        raise ERSModelIntegrityError(f"Unsupported ONNX tensor dtype: '{tensor_type}'.")
    return mapping[tensor_type]


class ModelLoader:
    """Safely loads model artifacts after validating weights, checksums, and tensor contracts."""

    @staticmethod
    def validate_and_load_onnx_weights(
        artifact_path: str | Path,
        manifest: ModelManifest | None = None,
        num_threads: int = 1,
        expected_classes: list[str] | None = None,
        verify_manifest_checksum: bool = True,
    ) -> tuple[Any, dict[str, Any]]:
        """Actually load ONNX weights, verify protobuf structure, initializers, contracts, and smoke inference.

        Rejects empty, corrupted, incompatible, or partially loaded weights.

        Raises:
            ERSModelUnavailableError: If the model file is missing.
            ERSModelIntegrityError: If weights are empty, corrupted, partially loaded, or fail contracts.
            ERSModelExecutionError: If ONNX Runtime session creation or smoke execution fails.
        """
        path = Path(artifact_path)
        if not path.is_file():
            raise ERSModelUnavailableError(f"Model weights file '{path}' does not exist.")

        file_size = path.stat().st_size
        if file_size == 0:
            raise ERSModelIntegrityError(f"Model weights file '{path}' is empty (0 bytes).")

        # Compute file SHA-256
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        computed_sha256 = hasher.hexdigest().lower()

        if manifest is not None and verify_manifest_checksum:
            if not manifest.verify_integrity(
                base_dir=str(path.parent) if not os.path.isabs(manifest.artifact_path) else None
            ):
                raise ERSModelIntegrityError(
                    f"Model integrity verification failed for '{manifest.model_id}'. "
                    f"SHA-256 digest mismatch against manifest!"
                )

        if manifest is not None and expected_classes is not None:
            valid_classes, class_err = manifest.validate_class_ordering(expected_classes)
            if not valid_classes:
                raise ERSModelIntegrityError(
                    f"Model '{manifest.model_id}' class ordering violation: {class_err}"
                )

        # Structural protobuf & initializer verification via onnx (detects corrupted / partially loaded weights)
        initializer_count = 0
        try:
            import onnx
            from onnx import TensorProto, numpy_helper

            onnx_model = onnx.load(str(path), load_external_data=False)
            onnx.checker.check_model(onnx_model)

            if len(onnx_model.graph.node) == 0:
                raise ERSModelIntegrityError(
                    f"ONNX model '{path}' contains an empty computation graph (0 nodes)."
                )

            for tensor in onnx_model.graph.initializer:
                initializer_count += 1
                if tensor.data_location == TensorProto.EXTERNAL:
                    ext_entries = {kv.key: kv.value for kv in tensor.external_data}
                    ext_loc = ext_entries.get("location", "")
                    ext_file = path.parent / ext_loc
                    if not ext_loc or not ext_file.is_file() or ext_file.stat().st_size == 0:
                        raise ERSModelIntegrityError(
                            f"Partially loaded ONNX weights: external tensor '{tensor.name}' missing or empty at '{ext_file}'."
                        )
                    onnx.external_data_helper.load_external_data_for_tensor(
                        tensor, str(path.parent)
                    )

                arr = numpy_helper.to_array(tensor)
                if arr.size == 0:
                    raise ERSModelIntegrityError(
                        f"ONNX weight initializer '{tensor.name}' is empty (0 elements)."
                    )
                if np.issubdtype(arr.dtype, np.floating) and not np.isfinite(arr).all():
                    raise ERSModelIntegrityError(
                        f"ONNX weight initializer '{tensor.name}' contains non-finite values (NaN/Inf)."
                    )
        except ERSModelIntegrityError:
            raise
        except ImportError:
            # onnx package optional when only runtime loading is required, OR session loading below validates binary
            pass
        except Exception as exc:
            raise ERSModelIntegrityError(
                f"Corrupted or invalid ONNX weights artifact '{path}': {exc}"
            ) from exc

        # Initialize ONNX Runtime session on CPU
        try:
            import onnxruntime as ort

            so = ort.SessionOptions()
            so.intra_op_num_threads = num_threads
            so.inter_op_num_threads = 1
            so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            session = ort.InferenceSession(
                str(path), sess_options=so, providers=["CPUExecutionProvider"]
            )
        except Exception as exc:
            raise ERSModelIntegrityError(
                f"Failed to load ONNX weights into runtime session from '{path}': {exc}"
            ) from exc

        inputs = session.get_inputs()
        outputs = session.get_outputs()
        if not inputs or not outputs:
            raise ERSModelIntegrityError(
                f"Loaded ONNX model '{path}' lacks required input or output tensors."
            )

        if manifest is not None:
            valid_tensors, tensor_err = manifest.validate_tensor_contracts(session)
            if not valid_tensors:
                raise ERSModelIntegrityError(
                    f"Model '{manifest.model_id}' tensor contract violation: {tensor_err}"
                )

        # Smoke inference test verifying architecture execution compatibility
        actual_in = inputs[0]
        actual_out = outputs[0]
        in_shape = [dim if isinstance(dim, int) and dim > 0 else 1 for dim in list(actual_in.shape)]
        if not in_shape:
            raise ERSModelIntegrityError("ONNX input tensor shape is scalar/empty.")

        np_dtype = _resolve_onnx_numpy_dtype(actual_in.type)
        probe = np.zeros(in_shape, dtype=np_dtype)
        try:
            res = session.run(None, {actual_in.name: probe})
        except Exception as exc:
            raise ERSModelExecutionError(f"ONNX smoke inference failed on '{path}': {exc}") from exc

        if not res or len(res) == 0:
            raise ERSModelIntegrityError(
                "ONNX model returned empty output during smoke validation."
            )

        out_arr = np.asarray(res[0])
        if out_arr.size == 0 or not np.isfinite(out_arr).all():
            raise ERSModelIntegrityError(
                "ONNX smoke inference produced empty or non-finite output values."
            )

        if expected_classes is not None and (
            out_arr.ndim == 0 or out_arr.shape[-1] != len(expected_classes)
        ):
            raise ERSModelIntegrityError(
                f"ONNX output class dimension mismatch: expected {len(expected_classes)}, got shape {list(out_arr.shape)}."
            )

        audit = {
            "artifact_path": str(path.resolve()),
            "artifact_size_bytes": file_size,
            "sha256_checksum": computed_sha256,
            "initializer_count": initializer_count,
            "input_name": actual_in.name,
            "input_shape": list(actual_in.shape),
            "input_type": actual_in.type,
            "output_name": actual_out.name,
            "output_shape": list(actual_out.shape),
            "output_type": actual_out.type,
        }
        return session, audit

    @staticmethod
    def load_onnx_session(
        manifest: ModelManifest,
        base_dir: str | None = None,
        num_threads: int = 4,
        expected_classes: list[str] | None = None,
    ) -> Any:
        """Load an ONNX Runtime InferenceSession with verified SHA-256 integrity, weights, and tensor contracts."""
        path = manifest.artifact_path
        if base_dir and not os.path.isabs(path):
            path = os.path.join(base_dir, path)

        if not os.path.isfile(path):
            raise ERSModelUnavailableError(
                f"Model file '{path}' for model '{manifest.model_id}' does not exist."
            )

        # Mandatory cryptographic integrity check
        if not manifest.verify_integrity(base_dir):
            raise ERSModelIntegrityError(
                f"Model integrity verification failed for '{manifest.model_id}'. "
                f"SHA-256 digest mismatch against manifest!"
            )

        session, _ = ModelLoader.validate_and_load_onnx_weights(
            artifact_path=path,
            manifest=manifest,
            num_threads=num_threads,
            expected_classes=expected_classes,
            verify_manifest_checksum=False,  # already verified above with base_dir
        )
        return session
