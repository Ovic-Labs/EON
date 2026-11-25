"""Real ONNX graph export, strict dimension validation, and parity verification.

Implements genuine ONNX export:
- Enforces exact input/output tensor shapes and class dimensions (no silent padding or truncation).
- Constructs valid ONNX protobuf graphs matching manifest input/output tensor contracts.
- Embeds optimal temperature scaling directly into classifier weights.
- Validates ONNX graph topology with onnx.checker.
- Verifies CPU numerical parity against reference NumPy predictions within documented tolerances.
- Performs atomic file serialization so failed parity/contract checks leave no broken artifact.
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from eon_ers.models.loader import ModelLoader
from eon_ers.models.manifest import ModelManifest
from eon_ers.training.trainer import TrainedModelArtifact

logger = logging.getLogger("eon_ers.training.export")

ONNX_LOGIT_PARITY_ATOL = 1e-4
ONNX_LOGIT_PARITY_RTOL = 1e-4
ONNX_PROB_PARITY_ATOL = 1e-5
ONNX_PROB_PARITY_RTOL = 1e-4


class ONNXExportMetadata(BaseModel):
    """Auditable metadata and telemetry from genuine ONNX export execution."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    model_id: str = Field(..., description="Target model identifier.")
    artifact_path: str = Field(..., description="Path to exported ONNX model weights.")
    artifact_sha256: str = Field(
        ..., min_length=64, max_length=64, description="Computed SHA-256 digest."
    )
    input_name: str = Field(..., description="Name of input tensor.")
    input_shape: list[int] = Field(..., description="Expected input tensor shape.")
    output_name: str = Field(..., description="Name of output tensor.")
    output_shape: list[int] = Field(..., description="Expected output tensor shape.")
    classes: list[str] = Field(..., description="Ordered emotion class labels.")
    exported_at: str = Field(..., description="ISO 8601 export timestamp.")
    graph_verified: bool = Field(default=True, description="Whether onnx.checker passed.")
    inference_verified: bool = Field(
        default=True, description="Whether onnxruntime test inference passed."
    )
    parity_verified: bool = Field(
        default=True,
        description="Whether ONNX outputs matched reference NumPy outputs within tolerance.",
    )
    max_logit_diff: float = Field(
        default=0.0, ge=0.0, description="Max absolute logit difference vs reference."
    )
    max_prob_diff: float = Field(
        default=0.0, ge=0.0, description="Max absolute probability difference vs reference."
    )
    parity_atol: float = Field(
        default=ONNX_LOGIT_PARITY_ATOL, description="Absolute tolerance used for logit parity."
    )


class ONNXModelExporter:
    """Exports in-memory trained weights into validated, parity-checked ONNX model files."""

    @staticmethod
    def _validate_export_dimensions(
        artifact: TrainedModelArtifact,
        manifest: ModelManifest,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Validate weight arrays and manifest tensor specifications with zero padding/truncation."""
        if artifact.W1.ndim != 2 or artifact.W2.ndim != 2:
            return False, "Model weight matrices W1 and W2 must be 2-dimensional.", {}
        if artifact.b1.ndim != 1 or artifact.b2.ndim != 1:
            return False, "Model bias vectors b1 and b2 must be 1-dimensional.", {}
        if (
            artifact.W1.shape[1] != artifact.b1.shape[0]
            or artifact.b1.shape[0] != artifact.W2.shape[0]
        ):
            return (
                False,
                f"Hidden layer dimension mismatch: W1={artifact.W1.shape}, b1={artifact.b1.shape}, W2={artifact.W2.shape}.",
                {},
            )
        if artifact.W2.shape[1] != artifact.b2.shape[0]:
            return (
                False,
                f"Output layer dimension mismatch: W2={artifact.W2.shape}, b2={artifact.b2.shape}.",
                {},
            )
        if artifact.W2.shape[1] != len(artifact.class_labels):
            return (
                False,
                f"Weight output dimension {artifact.W2.shape[1]} != class_labels length {len(artifact.class_labels)}.",
                {},
            )

        for name, arr in (
            ("W1", artifact.W1),
            ("b1", artifact.b1),
            ("W2", artifact.W2),
            ("b2", artifact.b2),
        ):
            if arr.size == 0 or not np.isfinite(arr).all():
                return (
                    False,
                    f"Model parameter '{name}' is empty or contains non-finite values.",
                    {},
                )

        input_spec = manifest.input_specification
        output_spec = manifest.output_specification

        input_name = str(input_spec.get("name", "input")).strip()
        output_name = str(output_spec.get("name", "logits")).strip()
        if not input_name or not output_name:
            return False, "Manifest input and output tensor names must be non-empty.", {}

        in_dtype = str(input_spec.get("dtype", "float32")).strip().lower()
        if in_dtype not in ("float", "float32"):
            return False, f"Unsupported export input dtype '{in_dtype}'; expected float32.", {}

        out_dtype = str(output_spec.get("dtype", "float32")).strip().lower()
        if out_dtype not in ("float", "float32"):
            return False, f"Unsupported export output dtype '{out_dtype}'; expected float32.", {}

        input_shape = input_spec.get("shape", [1, artifact.config.input_dim])
        output_shape = output_spec.get("shape", [1, artifact.config.num_classes])

        if (
            not isinstance(input_shape, list)
            or len(input_shape) < 2
            or not all(isinstance(d, int) and d > 0 for d in input_shape)
        ):
            return (
                False,
                f"Invalid manifest input_specification.shape: {input_shape}. Expected list of positive ints with rank >= 2.",
                {},
            )

        if (
            not isinstance(output_shape, list)
            or len(output_shape) != 2
            or not all(isinstance(d, int) and d > 0 for d in output_shape)
        ):
            return (
                False,
                f"Invalid manifest output_specification.shape: {output_shape}. Expected [batch, num_classes] of positive ints.",
                {},
            )

        if input_shape[0] != output_shape[0]:
            return (
                False,
                f"Batch dimension mismatch between input_shape {input_shape} and output_shape {output_shape}.",
                {},
            )

        flat_dim = int(np.prod(input_shape[1:]))
        if flat_dim != artifact.W1.shape[0]:
            return (
                False,
                f"Input feature dimension mismatch: manifest expects {flat_dim} features "
                f"(shape={input_shape}), but trained weights expect {artifact.W1.shape[0]}. "
                "Silent padding and truncation are prohibited.",
                {},
            )

        if output_shape[-1] != artifact.W2.shape[1]:
            return (
                False,
                f"Output dimension mismatch: manifest expects {output_shape[-1]} outputs, "
                f"but trained weights have {artifact.W2.shape[1]} outputs.",
                {},
            )

        manifest_classes = output_spec.get("classes")
        if manifest_classes is not None and list(manifest_classes) != list(artifact.class_labels):
            return (
                False,
                f"Manifest output class ordering {manifest_classes} != artifact class_labels {artifact.class_labels}.",
                {},
            )

        return (
            True,
            "Dimensions verified.",
            {
                "input_name": input_name,
                "input_shape": list(input_shape),
                "output_name": output_name,
                "output_shape": list(output_shape),
            },
        )

    def export(
        self,
        artifact: TrainedModelArtifact,
        manifest: ModelManifest,
        output_path: str | Path,
        temperature: float = 1.0,
        logit_atol: float = ONNX_LOGIT_PARITY_ATOL,
        logit_rtol: float = ONNX_LOGIT_PARITY_RTOL,
        prob_atol: float = ONNX_PROB_PARITY_ATOL,
        prob_rtol: float = ONNX_PROB_PARITY_RTOL,
        reference_fn: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> tuple[bool, ONNXExportMetadata | None, str]:
        """Export trained model weights into a validated, parity-checked ONNX model protobuf."""
        try:
            import onnx
            from onnx import TensorProto, helper, numpy_helper
        except ImportError as exc:
            return False, None, f"ONNX export requires 'onnx' package: {exc}"

        if not np.isfinite(temperature) or float(temperature) <= 0.0:
            return False, None, f"Invalid calibration temperature: {temperature}."

        dim_ok, dim_msg, dims = self._validate_export_dimensions(artifact, manifest)
        if not dim_ok:
            return False, None, dim_msg

        input_name: str = dims["input_name"]
        input_shape: list[int] = dims["input_shape"]
        output_name: str = dims["output_name"]
        output_shape: list[int] = dims["output_shape"]
        input_rank = len(input_shape)

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = out_path.with_suffix(".onnx.tmp")

        temp = float(temperature)
        W1 = artifact.W1.astype(np.float32).copy()
        b1 = artifact.b1.astype(np.float32).copy()
        W2 = (artifact.W2 / temp).astype(np.float32)
        b2 = (artifact.b2 / temp).astype(np.float32)

        t_W1 = numpy_helper.from_array(W1, name=f"{manifest.model_id}_W1")
        t_b1 = numpy_helper.from_array(b1, name=f"{manifest.model_id}_b1")
        t_W2 = numpy_helper.from_array(W2, name=f"{manifest.model_id}_W2")
        t_b2 = numpy_helper.from_array(b2, name=f"{manifest.model_id}_b2")

        in_info = helper.make_tensor_value_info(input_name, TensorProto.FLOAT, input_shape)
        out_info = helper.make_tensor_value_info(output_name, TensorProto.FLOAT, output_shape)

        nodes: list[Any] = []
        feed_input = input_name
        if input_rank > 2:
            flatten_node = helper.make_node(
                "Flatten", [input_name], [f"{manifest.model_id}_flattened"], axis=1
            )
            nodes.append(flatten_node)
            feed_input = f"{manifest.model_id}_flattened"

        gemm1 = helper.make_node(
            "Gemm",
            [feed_input, t_W1.name, t_b1.name],
            [f"{manifest.model_id}_z1"],
            alpha=1.0,
            beta=1.0,
        )
        relu = helper.make_node("Relu", [f"{manifest.model_id}_z1"], [f"{manifest.model_id}_a1"])
        gemm2 = helper.make_node(
            "Gemm",
            [f"{manifest.model_id}_a1", t_W2.name, t_b2.name],
            [output_name],
            alpha=1.0,
            beta=1.0,
        )
        nodes.extend([gemm1, relu, gemm2])

        graph = helper.make_graph(
            nodes,
            name=f"{manifest.model_id}_graph",
            inputs=[in_info],
            outputs=[out_info],
            initializer=[t_W1, t_b1, t_W2, t_b2],
        )

        onnx_model = helper.make_model(graph, producer_name="eon_ers")

        # 1. Validate ONNX Graph with onnx.checker
        try:
            onnx.checker.check_model(onnx_model)
        except Exception as exc:
            return False, None, f"ONNX checker validation failed: {exc}"

        try:
            # 2. Write to temporary path first (atomic commit after parity verification)
            with open(tmp_path, "wb") as f:
                f.write(onnx_model.SerializeToString())

            # 3. Load and verify tensor contracts & initializers via ModelLoader
            sess, _ = ModelLoader.validate_and_load_onnx_weights(
                artifact_path=tmp_path,
                manifest=manifest,
                num_threads=1,
                expected_classes=artifact.class_labels,
                verify_manifest_checksum=False,
            )

            # 4. Numerical Parity Verification against Reference NumPy Implementation on CPU
            rng = np.random.RandomState(42)
            probes: list[np.ndarray] = [
                np.zeros(input_shape, dtype=np.float32),
                *[rng.randn(*input_shape).astype(np.float32) for _ in range(4)],
            ]

            max_logit_diff = 0.0
            max_prob_diff = 0.0

            for probe in probes:
                flat_probe = probe.reshape(input_shape[0], -1)
                if reference_fn is not None:
                    ref_logits = np.asarray(reference_fn(flat_probe), dtype=np.float32)
                else:
                    ref_logits = (artifact.predict_logits(flat_probe) / temp).astype(np.float32)

                onnx_res = sess.run(None, {input_name: probe})
                onnx_logits = np.asarray(onnx_res[0], dtype=np.float32)

                if list(onnx_logits.shape) != output_shape:
                    return (
                        False,
                        None,
                        f"Inference output shape mismatch: expected {output_shape}, got {list(onnx_logits.shape)}.",
                    )
                if not np.isfinite(onnx_logits).all():
                    return False, None, "Inference output contains non-finite values."

                logit_diff = float(np.max(np.abs(onnx_logits - ref_logits)))
                max_logit_diff = max(max_logit_diff, logit_diff)

                if not np.allclose(onnx_logits, ref_logits, rtol=logit_rtol, atol=logit_atol):
                    return (
                        False,
                        None,
                        f"ONNX logit parity check failed: max diff {logit_diff:.6e} exceeds tolerance "
                        f"(atol={logit_atol}, rtol={logit_rtol}).",
                    )

                # Compare softmax probability parity as well
                ref_exp = np.exp(ref_logits - np.max(ref_logits, axis=1, keepdims=True))
                ref_probs = ref_exp / np.sum(ref_exp, axis=1, keepdims=True)
                onnx_exp = np.exp(onnx_logits - np.max(onnx_logits, axis=1, keepdims=True))
                onnx_probs = onnx_exp / np.sum(onnx_exp, axis=1, keepdims=True)

                prob_diff = float(np.max(np.abs(onnx_probs - ref_probs)))
                max_prob_diff = max(max_prob_diff, prob_diff)

                if not np.allclose(onnx_probs, ref_probs, rtol=prob_rtol, atol=prob_atol):
                    return (
                        False,
                        None,
                        f"ONNX probability parity check failed: max diff {prob_diff:.6e} exceeds tolerance "
                        f"(atol={prob_atol}, rtol={prob_rtol}).",
                    )

            # Release ORT session before atomic rename on Windows
            del sess
            os.replace(tmp_path, out_path)
        except Exception as exc:
            return False, None, f"ONNX Runtime parity/export verification failed: {exc}"
        finally:
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except OSError:
                    pass

        # 5. Compute SHA-256 digest of final exported artifact
        hasher = hashlib.sha256()
        with open(out_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        artifact_sha256 = hasher.hexdigest().lower()

        meta = ONNXExportMetadata(
            model_id=manifest.model_id,
            artifact_path=str(out_path),
            artifact_sha256=artifact_sha256,
            input_name=input_name,
            input_shape=input_shape,
            output_name=output_name,
            output_shape=output_shape,
            classes=artifact.class_labels,
            exported_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            graph_verified=True,
            inference_verified=True,
            parity_verified=True,
            max_logit_diff=max_logit_diff,
            max_prob_diff=max_prob_diff,
            parity_atol=logit_atol,
        )

        return (
            True,
            meta,
            f"ONNX export & parity verified at {out_path} (SHA-256: {artifact_sha256[:16]}..., max_logit_diff={max_logit_diff:.2e}).",
        )
