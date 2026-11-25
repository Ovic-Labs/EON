"""Real-world dataset provenance, metadata specification, and zero-leakage partitioning.

Defines schemas and verification utilities for real-world affective datasets:
AffectNet, RAF-DB, RAVDESS, CREMA-D. Enforces strict subject/speaker-independent
partitioning to prevent subject leakage during training and scientific evaluation.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import json
import random
import shutil
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from eon_ers.types import (
    EMPTY_BYTES_SHA256,
    KNOWN_PLACEHOLDER_CHECKSUMS,
    is_valid_sha256_digest,
)

__all__ = [
    "AFFECTNET_METADATA",
    "CREMA_D_METADATA",
    "EMPTY_BYTES_SHA256",
    "KNOWN_PLACEHOLDER_CHECKSUMS",
    "RAF_DB_METADATA",
    "RAVDESS_METADATA",
    "DatasetMetadata",
    "EvaluationPartition",
    "EvaluationSample",
    "create_subject_independent_partition",
    "is_valid_sha256_digest",
]


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
    manifest_checksum: str = Field(
        default="", description="Checksum of the extracted manifest file, if applicable."
    )
    acquisition_status: str = Field(
        default="UNAVAILABLE_UNVERIFIED",
        description="Dataset acquisition and verification status (e.g., 'ACQUIRED_VERIFIED', 'UNAVAILABLE_UNVERIFIED').",
    )
    download_url: str = Field(default="", description="Official acquisition URL.")
    subject_ids: list[str] = Field(
        default_factory=list, description="List of unique subject or actor identifiers."
    )

    @field_validator("name", "source", "version", "license", "partition_strategy")
    @classmethod
    def _reject_blank_metadata(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Dataset metadata string fields cannot be empty or whitespace-only.")
        return stripped

    def is_commercially_usable(self) -> bool:
        """Check if dataset can be legally used for commercial models."""
        return self.commercial_allowed

    def is_valid_checksum(self) -> bool:
        """Syntactic validation only: check if the registered checksum is a 64-char non-placeholder hex SHA-256.

        IMPORTANT: Syntactic validity does NOT constitute verification of archive bytes.
        Actual verification requires verify_archive() on the physical file.
        """
        return is_valid_sha256_digest(self.checksum)

    def verify_archive(
        self,
        archive_path: str | Path | None,
        expected_sha256: str | None = None,
        return_audit: bool = False,
    ) -> tuple[bool, str] | tuple[bool, str, dict[str, Any]]:
        """Verify the integrity of a dataset archive file against a trusted SHA-256 checksum.

        Requires physical archive bytes, recomputes SHA-256, and rejects missing,
        empty, malformed, placeholder, or mismatched archives and metadata.
        """
        empty_audit: dict[str, Any] = {}
        target_expected = (
            (expected_sha256 if expected_sha256 is not None else self.checksum).strip().lower()
        )
        if not is_valid_sha256_digest(target_expected):
            msg = (
                f"Dataset '{self.name}' has missing, malformed, or placeholder expected SHA-256 "
                f"checksum (value: '{target_expected}')."
            )
            return (False, msg, empty_audit) if return_audit else (False, msg)

        if archive_path is None or not str(archive_path).strip():
            msg = f"Dataset archive path is missing for '{self.name}'; actual archive bytes are required."
            return (False, msg, empty_audit) if return_audit else (False, msg)

        path = Path(archive_path)
        if not path.is_file():
            msg = f"Dataset archive file not found: {path}"
            return (False, msg, empty_audit) if return_audit else (False, msg)

        file_size = path.stat().st_size
        if file_size == 0:
            msg = f"Dataset archive file is empty (0 bytes): {path}"
            return (False, msg, empty_audit) if return_audit else (False, msg)

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        computed = hasher.hexdigest().lower()

        if not hmac.compare_digest(computed, target_expected):
            msg = (
                f"Checksum mismatch for '{self.name}': expected {target_expected}, got {computed}."
            )
            return (False, msg, empty_audit) if return_audit else (False, msg)

        audit_record: dict[str, Any] = {
            "dataset_name": self.name,
            "dataset_version": self.version,
            "acquisition_source": self.source,
            "archive_path": str(path.resolve()),
            "archive_size_bytes": file_size,
            "sha256_checksum": computed,
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "verification_status": "ACQUIRED_VERIFIED",
        }
        msg = f"Dataset archive integrity verified ({computed[:16]}...)."
        return (True, msg, audit_record) if return_audit else (True, msg)

    def verify_manifest(
        self, manifest_path: str | Path | None, expected_sha256: str | None = None
    ) -> tuple[bool, str, dict[str, Any]]:
        """Verify the integrity and non-emptiness of a dataset manifest against a trusted digest."""
        empty_audit: dict[str, Any] = {}
        target_expected = (
            (expected_sha256 if expected_sha256 is not None else self.manifest_checksum)
            .strip()
            .lower()
        )
        if not is_valid_sha256_digest(target_expected):
            return (
                False,
                f"Manifest expected SHA-256 is missing, malformed, or placeholder: '{target_expected}'.",
                empty_audit,
            )

        if manifest_path is None or not str(manifest_path).strip():
            return False, "Dataset manifest path is missing.", empty_audit

        path = Path(manifest_path)
        if not path.is_file():
            return False, f"Dataset manifest not found: {path}", empty_audit

        size = path.stat().st_size
        if size == 0:
            return False, f"Dataset manifest file is empty (0 bytes): {path}", empty_audit

        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        computed = hasher.hexdigest().lower()

        if not hmac.compare_digest(computed, target_expected):
            return (
                False,
                f"Manifest checksum mismatch: expected {target_expected}, got {computed}.",
                empty_audit,
            )

        # Structured manifest format validation (JSON / CSV)
        suffix = path.suffix.lower()
        try:
            if suffix == ".json":
                parsed = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(parsed, (dict, list)):
                    return (
                        False,
                        "JSON dataset manifest must decode to an object or array.",
                        empty_audit,
                    )
                if (
                    isinstance(parsed, dict)
                    and "samples" in parsed
                    and isinstance(parsed["samples"], list)
                ):
                    seen_ids: set[str] = set()
                    for item in parsed["samples"]:
                        if isinstance(item, dict) and "sample_id" in item:
                            sid = str(item["sample_id"]).strip()
                            if not sid or sid in seen_ids:
                                return (
                                    False,
                                    f"Duplicate or blank sample_id '{sid}' in JSON manifest.",
                                    empty_audit,
                                )
                            seen_ids.add(sid)
            elif suffix == ".csv":
                with open(path, encoding="utf-8", newline="") as cf:
                    reader = csv.DictReader(cf)
                    fieldnames = set(reader.fieldnames or [])
                    required_cols = {"sample_id", "subject_id", "label"}
                    if not required_cols.issubset(fieldnames):
                        return (
                            False,
                            f"CSV manifest missing required columns: {sorted(required_cols - fieldnames)}.",
                            empty_audit,
                        )
                    seen_csv_ids: set[str] = set()
                    for row in reader:
                        sid = str(row.get("sample_id", "")).strip()
                        subj = str(row.get("subject_id", "")).strip()
                        lbl = str(row.get("label", "")).strip()
                        if not sid or not subj or not lbl:
                            return (
                                False,
                                "CSV manifest contains blank sample_id, subject_id, or label.",
                                empty_audit,
                            )
                        if sid in seen_csv_ids:
                            return (
                                False,
                                f"Duplicate sample_id '{sid}' detected in CSV manifest.",
                                empty_audit,
                            )
                        seen_csv_ids.add(sid)
        except Exception as exc:
            return False, f"Malformed dataset manifest ({suffix}): {exc}", empty_audit

        audit = {
            "dataset_name": self.name,
            "manifest_path": str(path.resolve()),
            "manifest_sha256": computed,
            "manifest_size_bytes": size,
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        return True, f"Dataset manifest verified ({computed[:16]}...).", audit

    def safe_extract_archive(
        self,
        archive_path: str | Path,
        dest_dir: str | Path,
        *,
        expected_sha256: str | None = None,
        max_archive_bytes: int = 2 * 1024 * 1024 * 1024,
        max_extracted_bytes: int = 4 * 1024 * 1024 * 1024,
        max_files: int = 100_000,
        max_compression_ratio: float = 100.0,
    ) -> tuple[bool, str, dict[str, Any]]:
        """Safely verify and extract a dataset archive with traversal and decompression-bomb limits."""
        empty_audit: dict[str, Any] = {}
        ok, msg, archive_audit = self.verify_archive(
            archive_path, expected_sha256=expected_sha256, return_audit=True
        )  # type: ignore[misc]
        if not ok:
            return False, msg, empty_audit

        src = Path(archive_path)
        archive_size = src.stat().st_size
        if archive_size > max_archive_bytes:
            return (
                False,
                f"Archive size ({archive_size} bytes) exceeds limit ({max_archive_bytes} bytes).",
                empty_audit,
            )

        dest = Path(dest_dir).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        name_lower = src.name.lower()

        def _validate_rel_member(member_name: str) -> Path:
            normalized = member_name.replace("\\", "/")
            if not normalized or normalized.startswith("/") or ":" in normalized.split("/")[0]:
                raise ValueError(
                    f"Unsafe absolute or drive-qualified archive path: {member_name!r}"
                )
            parts = [p for p in normalized.split("/") if p]
            if any(part == ".." for part in parts):
                raise ValueError(f"Path traversal detected in archive member: {member_name!r}")
            target = (dest / Path(*parts)).resolve() if parts else dest
            if target != dest and dest not in target.parents:
                raise ValueError(f"Archive member escapes extraction root: {member_name!r}")
            return target

        extracted_files = 0
        total_uncompressed = 0

        try:
            if name_lower.endswith(".zip"):
                if not zipfile.is_zipfile(src):
                    return False, f"Invalid or corrupted ZIP archive format: {src}", empty_audit
                with zipfile.ZipFile(src, "r") as zf:
                    infos = zf.infolist()
                    if len(infos) > max_files:
                        return (
                            False,
                            f"Archive entry count ({len(infos)}) exceeds max_files ({max_files}).",
                            empty_audit,
                        )
                    for info in infos:
                        # Reject symlinks encoded in Unix external_attr (S_IFLNK = 0o120000)
                        if (info.external_attr >> 16) & 0o170000 == 0o120000:
                            return (
                                False,
                                f"Symlink member rejected in ZIP archive: {info.filename!r}",
                                empty_audit,
                            )
                        target = _validate_rel_member(info.filename)
                        if info.is_dir():
                            target.mkdir(parents=True, exist_ok=True)
                            continue
                        total_uncompressed += max(0, info.file_size)
                        if total_uncompressed > max_extracted_bytes:
                            return (
                                False,
                                f"Uncompressed size exceeds max_extracted_bytes ({max_extracted_bytes}).",
                                empty_audit,
                            )
                        if (
                            archive_size > 0
                            and (total_uncompressed / archive_size) > max_compression_ratio
                        ):
                            return (
                                False,
                                f"Decompression ratio exceeds limit ({max_compression_ratio}x); potential zip bomb.",
                                empty_audit,
                            )
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info, "r") as z_in, open(target, "wb") as out_f:
                            written = 0
                            while chunk := z_in.read(65536):
                                written += len(chunk)
                                if (
                                    total_uncompressed - info.file_size + written
                                ) > max_extracted_bytes:
                                    raise ValueError(
                                        "Actual extracted bytes exceed max_extracted_bytes limit."
                                    )
                                out_f.write(chunk)
                        extracted_files += 1
            elif name_lower.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz")):
                with tarfile.open(src, mode="r:*") as tf:
                    members = tf.getmembers()
                    if len(members) > max_files:
                        return (
                            False,
                            f"Archive entry count ({len(members)}) exceeds max_files ({max_files}).",
                            empty_audit,
                        )
                    for member in members:
                        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
                            return (
                                False,
                                f"Unsafe link/device entry rejected in TAR archive: {member.name!r}",
                                empty_audit,
                            )
                        target = _validate_rel_member(member.name)
                        if member.isdir():
                            target.mkdir(parents=True, exist_ok=True)
                            continue
                        if not member.isfile():
                            return (
                                False,
                                f"Unsupported TAR member type rejected: {member.name!r}",
                                empty_audit,
                            )
                        total_uncompressed += max(0, member.size)
                        if total_uncompressed > max_extracted_bytes:
                            return (
                                False,
                                f"Uncompressed size exceeds max_extracted_bytes ({max_extracted_bytes}).",
                                empty_audit,
                            )
                        if (
                            archive_size > 0
                            and (total_uncompressed / archive_size) > max_compression_ratio
                        ):
                            return (
                                False,
                                f"Decompression ratio exceeds limit ({max_compression_ratio}x); potential archive bomb.",
                                empty_audit,
                            )
                        target.parent.mkdir(parents=True, exist_ok=True)
                        src_file = tf.extractfile(member)
                        if src_file is None:
                            return (
                                False,
                                f"Could not extract TAR member {member.name!r}.",
                                empty_audit,
                            )
                        with src_file, open(target, "wb") as out_f:
                            shutil.copyfileobj(src_file, out_f, length=65536)
                        extracted_files += 1
            else:
                return (
                    False,
                    f"Unsupported dataset archive format for '{src.name}'; expected .zip or .tar(.gz/.bz2/.xz).",
                    empty_audit,
                )
        except Exception as exc:
            return False, f"Safe archive extraction failed: {exc}", empty_audit

        audit = {
            **archive_audit,
            "extracted_to": str(dest),
            "extracted_files": extracted_files,
            "extracted_bytes": total_uncompressed,
        }
        return True, f"Dataset archive safely extracted ({extracted_files} files).", audit


class EvaluationSample(BaseModel):
    """A single evaluation or training sample bound to a unique subject."""

    model_config = ConfigDict(extra="allow", frozen=True)

    sample_id: str = Field(..., min_length=1, description="Unique sample identifier.")
    subject_id: str = Field(..., min_length=1, description="Unique speaker or actor identifier.")
    label: str = Field(..., min_length=1, description="Ground-truth emotion label.")
    data: Any = Field(default=None, description="Feature array, tensor, or file reference.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional sample metadata."
    )

    @field_validator("sample_id", "subject_id", "label")
    @classmethod
    def _reject_blank_sample_fields(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("EvaluationSample sample_id, subject_id, and label cannot be blank.")
        return stripped


def validate_samples_collection(samples: list[EvaluationSample]) -> None:
    """Reject empty batches, malformed samples, or duplicate sample_ids."""
    if not samples:
        raise ValueError("Sample list cannot be empty.")
    seen_ids: set[str] = set()
    for idx, sample in enumerate(samples):
        if not isinstance(sample, EvaluationSample):
            raise ValueError(f"Malformed sample entry at index {idx}: expected EvaluationSample.")
        if sample.sample_id in seen_ids:
            raise ValueError(f"Duplicate sample_id detected: '{sample.sample_id}'.")
        seen_ids.add(sample.sample_id)


class EvaluationPartition:
    """Subject/speaker-independent dataset partition with cryptographic leakage validation."""

    def __init__(
        self,
        train_samples: list[EvaluationSample],
        val_samples: list[EvaluationSample],
        test_samples: list[EvaluationSample],
    ) -> None:
        validate_samples_collection(train_samples + val_samples + test_samples)
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
    validate_samples_collection(samples)

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

FER2013_METADATA = DatasetMetadata(
    name="FER2013",
    source="Goodfellow, I. J., et al. (ICML Challenges in Representation Learning, 2013)",
    version="1.0",
    license="Challenge Research Only (verify competition / license terms prior to any use)",
    commercial_allowed=False,
    redistribution_allowed=False,
    partition_strategy="subject_independent_best_effort",
    checksum="",
    download_url="https://www.kaggle.com/competitions/challenges-in-representation-learning-facial-expression-recognition-challenge",
    subject_ids=[],
)

KNOWN_DATASET_PROVENANCE: dict[str, DatasetMetadata] = {
    "affectnet": AFFECTNET_METADATA,
    "raf_db": RAF_DB_METADATA,
    "fer2013": FER2013_METADATA,
    "ravdess": RAVDESS_METADATA,
    "crema_d": CREMA_D_METADATA,
}
