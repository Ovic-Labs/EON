"""Unit tests for Critical Issues 3 & 4: Real-World Evaluation Framework and 15-Stage Pipeline.

Verifies:
1. Detection and prevention of subject/speaker data leakage across partitions.
2. Subject-independent splitting algorithm.
3. Dataset provenance and commercial licensing registers.
4. Execution of the 15-stage reproducible training and validation workflow.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from eon_ers.evaluation.dataset import (
    AFFECTNET_METADATA,
    CREMA_D_METADATA,
    RAF_DB_METADATA,
    RAVDESS_METADATA,
    DatasetMetadata,
    EvaluationPartition,
    EvaluationSample,
    create_subject_independent_partition,
)
from eon_ers.models.manifest import ModelManifest
from eon_ers.training.pipeline import (
    ModelTrainingPipeline,
    TrainingPipelineStage,
)


def test_subject_leakage_detector_raises_error() -> None:
    """EvaluationPartition must raise ValueError if train, val, or test share subjects."""
    train = [
        EvaluationSample(sample_id="s1", subject_id="Actor_01", label="happiness"),
        EvaluationSample(sample_id="s2", subject_id="Actor_02", label="neutral"),
    ]
    val = [
        EvaluationSample(sample_id="s3", subject_id="Actor_03", label="sadness"),
    ]
    # Leaked subject: Actor_01 is in both train and test!
    test_leaked = [
        EvaluationSample(sample_id="s4", subject_id="Actor_01", label="happiness"),
    ]

    with pytest.raises(ValueError, match="Subject leakage detected"):
        EvaluationPartition(train_samples=train, val_samples=val, test_samples=test_leaked)


def test_create_subject_independent_partition_zero_leakage() -> None:
    """create_subject_independent_partition must split unique subjects with zero leakage."""
    samples = []
    # 10 subjects, 5 samples each
    for i in range(1, 11):
        subj = f"Speaker_{i:02d}"
        for j in range(5):
            samples.append(
                EvaluationSample(
                    sample_id=f"{subj}_{j}",
                    subject_id=subj,
                    label="happiness" if j % 2 == 0 else "neutral",
                )
            )

    partition = create_subject_independent_partition(
        samples, test_subject_ratio=0.20, val_subject_ratio=0.20, seed=42
    )

    # Disjointness checks
    assert len(partition.train_subjects & partition.test_subjects) == 0
    assert len(partition.train_subjects & partition.val_subjects) == 0
    assert len(partition.val_subjects & partition.test_subjects) == 0

    assert partition.total_samples == len(samples)
    assert partition.total_subjects == 10


def test_dataset_provenance_and_licensing_registers() -> None:
    """Real dataset registers must reflect academic non-commercial licensing constraints."""
    for meta in (AFFECTNET_METADATA, RAF_DB_METADATA, RAVDESS_METADATA, CREMA_D_METADATA):
        assert isinstance(meta, DatasetMetadata)
        assert len(meta.name) > 0
        assert len(meta.source) > 0
        # All academic benchmarks are restricted for commercial use:
        assert meta.commercial_allowed is False
        assert meta.is_commercially_usable() is False
        # External unacquired datasets must have empty checksum (no placeholder hashes)
        assert meta.checksum == ""
        assert meta.is_valid_checksum() is False


def test_15_stage_training_pipeline_execution(tmp_path: Path) -> None:
    """The 15-stage training pipeline must execute sequentially and record each stage."""
    dummy_weights = tmp_path / "model.onnx"
    dummy_weights.write_bytes(b"dummy onnx weights bytes for pipeline")

    manifest = ModelManifest(
        model_id="test-train-v1",
        name="Test Pipeline Model",
        version="1.0.0",
        modality="facial",
        artifact_path=str(dummy_weights),
        sha256_checksum="0" * 64,
        license="OVIC Internal Testing",
        source="OVIC Labs",
        input_specification={"name": "input", "shape": [1, 1, 64, 64]},
        output_specification={"name": "logits", "shape": [1, 7]},
    )

    pipeline = ModelTrainingPipeline(
        dataset_metadata=AFFECTNET_METADATA,
        model_manifest=manifest,
        output_dir=str(tmp_path),
    )

    # Generate synthetic samples with 5 distinct subjects (without data payloads)
    samples = []
    for i in range(1, 6):
        subj = f"Subject_{i:02d}"
        for j in range(4):
            samples.append(
                EvaluationSample(
                    sample_id=f"{subj}_{j}",
                    subject_id=subj,
                    label="neutral",
                )
            )

    success, stage_results, record = pipeline.run_pipeline(
        raw_samples=samples,
        model_weights_path=str(dummy_weights),
    )

    # Stages must be 15
    assert len(stage_results) == 15
    stage_names = [r.stage.value for r in stage_results]
    assert stage_names[0] == TrainingPipelineStage.STAGE_1_DATASET_INGESTION.value
    assert stage_names[-1] == TrainingPipelineStage.STAGE_15_VALIDATION_RECORD_GENERATION.value

    # Since AffectNet has commercial_allowed = False and mock predictions are uncalibrated:
    assert record is not None
    assert record.is_validated is False
    assert success is False

    # Check that stage 11 reported BLOCKED because sample data was missing
    stage_11 = next(
        r for r in stage_results if r.stage == TrainingPipelineStage.STAGE_11_TEST_EVALUATION
    )
    assert stage_11.success is False
    assert stage_11.details.get("status") == "BLOCKED"
