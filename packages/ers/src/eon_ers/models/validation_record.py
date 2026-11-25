"""Auditable scientific model validation record specification.

In accordance with Phase 3.1.3 requirements, a manifest claiming 'VERIFIED' is not
sufficient by itself to establish scientific validation. Every validated model must
be accompanied by an auditable validation record cryptographically bound to the artifact
SHA-256 and backed by empirical evaluation metrics.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from eon_ers.types import is_valid_sha256_digest


class ModelValidationRecord(BaseModel):
    """Auditable empirical validation record for a machine learning model artifact."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str = Field(..., description="Unique validation record identifier.")
    model_id: str = Field(..., description="Model identifier matching manifest.")
    model_version: str = Field(..., description="Exact semantic model version.")
    artifact_sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 digest of verified weights artifact.",
    )
    is_validated: bool = Field(
        ..., description="Whether this model has passed empirical accuracy qualification."
    )
    training_dataset: str = Field(..., description="Exact training dataset identifier and origin.")
    training_dataset_version: str = Field(default="1.0.0", description="Dataset release version.")
    dataset_license: str = Field(..., description="Dataset software/data license.")
    commercial_use_allowed: bool = Field(
        default=False, description="Whether training data permits commercial derivation."
    )
    commercial_use_restrictions: list[str] = Field(
        default_factory=list, description="Specific commercial or ethical constraints."
    )
    preprocessing_specification: dict[str, Any] = Field(
        default_factory=dict,
        description="Image/audio normalization, input dimensions, and framing.",
    )
    label_mapping: list[str] = Field(
        ..., description="Exact ordered list of supported emotion categories."
    )
    evaluation_dataset: str = Field(..., description="Benchmark evaluation dataset name.")
    evaluation_split: str = Field(
        ..., description="Evaluation partition (e.g. 'test', 'validation')."
    )
    evaluation_script: str = Field(..., description="Path or module name of evaluation script.")
    evaluation_script_version: str = Field(
        default="1.0.0", description="Evaluation script version."
    )
    evaluation_metrics: dict[str, float] = Field(
        ..., description="Macro metrics: accuracy, balanced_accuracy, macro_f1, precision, recall."
    )
    per_class_metrics: dict[str, dict[str, float]] = Field(
        default_factory=dict, description="Per-class precision, recall, and F1 scores."
    )
    calibration_metrics: dict[str, float] = Field(
        default_factory=dict, description="Calibration metrics (e.g., ECE, Brier score)."
    )
    confidence_distribution: dict[str, float] = Field(
        default_factory=dict,
        description="Percentiles of prediction confidence (p25, p50, p75, p95).",
    )
    abstention_rate: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Proportion of samples where classifier abstained."
    )
    evaluator: str = Field(..., description="Entity, lab, or engineer who executed evaluation.")
    validation_timestamp: str = Field(..., description="ISO 8601 evaluation timestamp.")
    validation_notes: list[str] = Field(
        default_factory=list, description="Limitations, operational bounds, and caveats."
    )
    dataset_archive_sha256: str = Field(
        default="", description="Verified SHA-256 digest of empirical dataset archive."
    )
    execution_proof_key_id: str = Field(
        default="", description="Explicit key identifier used to sign the execution proof."
    )
    execution_proof_algorithm: str = Field(
        default="", description="Authenticated signature algorithm for the execution proof."
    )
    execution_proof_signature: str = Field(
        default="", description="Authenticated signature of trusted pipeline execution."
    )

    def verify_artifact_binding(self, artifact_path: str) -> bool:
        """Cryptographically verify that this validation record binds to the target artifact."""
        expected = self.artifact_sha256.strip().lower()
        if not is_valid_sha256_digest(expected):
            return False
        if not os.path.isfile(artifact_path) or os.path.getsize(artifact_path) == 0:
            return False

        hasher = hashlib.sha256()
        with open(artifact_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)

        computed = hasher.hexdigest().lower()
        return hmac.compare_digest(computed, expected)

    @classmethod
    def load_from_file(cls, path: str | Path) -> ModelValidationRecord:
        """Load and validate record from a JSON file."""
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def save_to_file(self, path: str | Path) -> None:
        """Persist record as formatted JSON."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))
