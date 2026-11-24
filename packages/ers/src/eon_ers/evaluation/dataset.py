"""Real-world dataset provenance, metadata specification, and zero-leakage partitioning.

Defines schemas and verification utilities for real-world affective datasets:
AffectNet, RAF-DB, RAVDESS, CREMA-D. Enforces strict subject/speaker-independent
partitioning to prevent subject leakage during training and scientific evaluation.
"""

from __future__ import annotations

import hashlib
import random
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

EMPTY_BYTES_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
KNOWN_PLACEHOLDER_CHECKSUMS: frozenset[str] = frozenset(
    {
        EMPTY_BYTES_SHA256,
        "0" * 64,
        "f" * 64,
        "a" * 64,
        "1" * 64,
    }
)


class DatasetMetadata(BaseModel):
    """Cryptographically auditable metadata and licensing for an emotion dataset."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(..., min_length=1, description="Dataset name.")
    source: str = Field(..., min_length=1, description="Source publication or lab.")
    version: str = Field(..., min_length=1, description="Dataset release version.")
    license: str = Field(..., min_length=1, description="Software or data license.")
    commercial_allowed: bool = Field(
        default=False, description="Whether commercial deployment is permitted."
    )
    redistribution_allowed: bool = Field(
        default=False, description="Whether redistribution of raw media is permitted."
    )
    partition_strategy: str = Field(
        default="subject_independent",
        description="Partitioning strategy (e.g., 'subject_independent', 'predefined').",
    )
    checksum: str = Field(default="", description="Checksum of the dataset manifest or archive.")
    download_url: str = Field(default="", description="Official acquisition URL.")
    subject_ids: list[str] = Field(
        default_factory=list, description="List of unique subject or actor identifiers."
    )

    def is_commercially_usable(self) -> bool:
        """Check if dataset can be legally used for commercial models."""
        return self.commercial_allowed

    def is_valid_checksum(self) -> bool:
        """Verify whether the registered checksum is a valid, non-placeholder 64-char SHA-256."""
        if not self.checksum:
            return False
        c = self.checksum.strip().lower()
        if len(c) != 64:
            return False
        if not all(ch in "0123456789abcdef" for ch in c):
            return False
        if c in KNOWN_PLACEHOLDER_CHECKSUMS:
            return False
        return True

    def verify_archive(self, archive_path: str | Path) -> tuple[bool, str]:
        """Verify the integrity of a dataset archive file against its registered SHA-256 checksum."""
        if not self.is_valid_checksum():
            return (
                False,
                f"Dataset '{self.name}' has no registered valid SHA-256 checksum (value: '{self.checksum}').",
            )

        path = Path(archive_path)
        if not path.is_file():
            return False, f"Dataset archive file not found: {path}"

        if path.stat().st_size == 0:
            return False, f"Dataset archive file is empty (0 bytes): {path}"

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        computed = hasher.hexdigest().lower()

        expected = self.checksum.strip().lower()
        if computed != expected:
            return (
                False,
                f"Checksum mismatch for '{self.name}': expected {expected}, got {computed}.",
            )

        return True, f"Dataset archive integrity verified ({computed[:16]}...)."


class EvaluationSample(BaseModel):
    """A single evaluation or training sample bound to a unique subject."""

    model_config = ConfigDict(extra="allow", frozen=True)

    sample_id: str = Field(..., description="Unique sample identifier.")
    subject_id: str = Field(..., description="Unique speaker or actor identifier.")
    label: str = Field(..., description="Ground-truth emotion label.")
    data: Any = Field(default=None, description="Feature array, tensor, or file reference.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional sample metadata."
    )


class EvaluationPartition:
    """Subject/speaker-independent dataset partition with cryptographic leakage validation."""

    def __init__(
        self,
        train_samples: list[EvaluationSample],
        val_samples: list[EvaluationSample],
        test_samples: list[EvaluationSample],
    ) -> None:
        self.train_samples = train_samples
        self.val_samples = val_samples
        self.test_samples = test_samples

        self.train_subjects = {s.subject_id for s in train_samples}
        self.val_subjects = {s.subject_id for s in val_samples}
        self.test_subjects = {s.subject_id for s in test_samples}

        # Zero-leakage verification:
        self._verify_zero_leakage()

    def _verify_zero_leakage(self) -> None:
        """Verify that subject sets across train, val, and test are strictly disjoint."""
        train_val = self.train_subjects & self.val_subjects
        if train_val:
            raise ValueError(
                f"Subject leakage detected between train and val partitions: subjects {sorted(train_val)}"
            )

        train_test = self.train_subjects & self.test_subjects
        if train_test:
            raise ValueError(
                f"Subject leakage detected between train and test partitions: subjects {sorted(train_test)}"
            )

        val_test = self.val_subjects & self.test_subjects
        if val_test:
            raise ValueError(
                f"Subject leakage detected between val and test partitions: subjects {sorted(val_test)}"
            )

    @property
    def total_samples(self) -> int:
        return len(self.train_samples) + len(self.val_samples) + len(self.test_samples)

    @property
    def total_subjects(self) -> int:
        return len(self.train_subjects | self.val_subjects | self.test_subjects)


def create_subject_independent_partition(
    samples: list[EvaluationSample],
    test_subject_ratio: float = 0.20,
    val_subject_ratio: float = 0.10,
    seed: int = 42,
) -> EvaluationPartition:
    """Partition samples into train/val/test by subject ID to guarantee zero speaker/actor leakage."""
    if not samples:
        raise ValueError("Cannot partition an empty sample list.")

    unique_subjects = sorted({s.subject_id for s in samples})
    if len(unique_subjects) < 3:
        raise ValueError(
            f"Subject-independent partitioning requires at least 3 distinct subjects; got {len(unique_subjects)}."
        )

    rng = random.Random(seed)
    shuffled_subjects = list(unique_subjects)
    rng.shuffle(shuffled_subjects)

    n_total = len(shuffled_subjects)
    n_test = max(1, int(round(n_total * test_subject_ratio)))
    n_val = max(1, int(round(n_total * val_subject_ratio)))
    if n_test + n_val >= n_total:
        n_test = 1
        n_val = 1

    test_subjects = set(shuffled_subjects[:n_test])
    val_subjects = set(shuffled_subjects[n_test : n_test + n_val])
    train_subjects = set(shuffled_subjects[n_test + n_val :])

    train_samples = [s for s in samples if s.subject_id in train_subjects]
    val_samples = [s for s in samples if s.subject_id in val_subjects]
    test_samples = [s for s in samples if s.subject_id in test_subjects]

    return EvaluationPartition(
        train_samples=train_samples,
        val_samples=val_samples,
        test_samples=test_samples,
    )


# Standard benchmark dataset provenance metadata registers
AFFECTNET_METADATA = DatasetMetadata(
    name="AffectNet",
    source="Mollahosseini, A., Hasani, B., & Mahoor, M. H. (IEEE TAC, 2017)",
    version="1.0",
    license="Non-Commercial Research Use Only",
    commercial_allowed=False,
    redistribution_allowed=False,
    partition_strategy="subject_independent",
    checksum="",
    download_url="http://mohammadmahoor.com/affectnet/",
    subject_ids=[],
)

RAF_DB_METADATA = DatasetMetadata(
    name="RAF-DB",
    source="Li, S., Deng, W., & Du, J. (CVPR, 2017)",
    version="1.0",
    license="Academic / Non-Commercial Research License",
    commercial_allowed=False,
    redistribution_allowed=False,
    partition_strategy="predefined_subject_splits",
    checksum="",
    download_url="http://www.whdeng.cn/RAF/model1.html",
    subject_ids=[],
)

RAVDESS_METADATA = DatasetMetadata(
    name="RAVDESS",
    source="Livingstone, S. R., & Russo, F. A. (PLOS ONE, 2018)",
    version="1.0",
    license="Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)",
    commercial_allowed=False,
    redistribution_allowed=True,
    partition_strategy="actor_independent_holdout",
    checksum="",
    download_url="https://zenodo.org/record/1188976",
    subject_ids=[f"Actor_{i:02d}" for i in range(1, 25)],
)

CREMA_D_METADATA = DatasetMetadata(
    name="CREMA-D",
    source="Cao, H., Cooper, D. G., Keutmann, M. K., et al. (IEEE TAC, 2014)",
    version="1.0",
    license="Open Database License (ODbL) / Research",
    commercial_allowed=False,
    redistribution_allowed=True,
    partition_strategy="actor_independent_holdout",
    checksum="",
    download_url="https://github.com/CheyneyComputerScience/CREMA-D",
    subject_ids=[f"Actor_{1000 + i}" for i in range(1, 92)],
)
