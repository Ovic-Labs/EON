"""Complete cryptographic model registry managing discovery, qualification, activation, and revocation."""

from __future__ import annotations

import copy
import json
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from eon_ers.evaluation.proof import EvaluationExecutionProof, TrustedKeyRegistry
from eon_ers.exceptions import ERSModelIntegrityError
from eon_ers.models.compatibility import check_manifest_compatibility
from eon_ers.models.manifest import ModelManifest
from eon_ers.models.validation_record import ModelValidationRecord
from eon_ers.safety.policy import ensure_model_activation_allowed
from eon_ers.types import Modality, ModelQualificationState


@dataclass
class RegisteredModelEntry:
    """Internal registry entry combining manifest, validation record, proof, and lifecycle state."""

    manifest: ModelManifest
    manifest_path: Path | None = None
    validation_record: ModelValidationRecord | None = None
    qualification_state: ModelQualificationState = ModelQualificationState.MODEL_DISCOVERED
    execution_proof: EvaluationExecutionProof | None = None
    activated: bool = False
    revocation_reason: str | None = None
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.manifest.model_id,
            "name": self.manifest.name,
            "version": self.manifest.version,
            "modality": self.manifest.modality.value,
            "framework": self.manifest.framework,
            "artifact_path": self.manifest.artifact_path,
            "sha256_checksum": self.manifest.sha256_checksum,
            "provenance_status": self.manifest.provenance_status,
            "license": self.manifest.license,
            "commercial_use_allowed": self.manifest.commercial_use_allowed,
            "qualification_state": self.qualification_state.value,
            "is_validated": self.qualification_state == ModelQualificationState.MODEL_VALIDATED,
            "activated": self.activated,
            "activation_eligible": self.qualification_state
            == ModelQualificationState.MODEL_VALIDATED,
            "revocation_reason": self.revocation_reason,
            "rejection_reasons": list(self.rejection_reasons),
            "validation_record": self.validation_record.model_dump()
            if self.validation_record
            else None,
            "known_limitations": list(self.manifest.known_limitations),
        }


class ModelRegistry:
    """Thread-safe model registry enforcing fail-closed qualification and activation guards."""

    def __init__(self, key_registry: TrustedKeyRegistry | None = None) -> None:
        self._lock = threading.Lock()
        self._manifests: dict[str, ModelManifest] = {}
        self._entries: dict[str, RegisteredModelEntry] = {}
        self.key_registry = key_registry

    def register(
        self,
        manifest: ModelManifest,
        *,
        validation_record: ModelValidationRecord | None = None,
        manifest_path: Path | None = None,
        proof: EvaluationExecutionProof | None = None,
    ) -> RegisteredModelEntry:
        """Register a model manifest and classify its qualification state fail-closed."""
        compat_ok, compat_reasons = check_manifest_compatibility(manifest)
        state = ModelQualificationState.MODEL_DISCOVERED
        rejection_reasons: list[str] = []

        if not compat_ok:
            state = ModelQualificationState.MODEL_REJECTED
            rejection_reasons.extend(compat_reasons)
        elif validation_record is not None:
            binding_ok = validation_record.verify_artifact_binding(manifest.artifact_path)
            if not binding_ok:
                state = ModelQualificationState.MODEL_REJECTED
                rejection_reasons.append(
                    "Validation record SHA-256 artifact binding verification failed."
                )
            elif validation_record.is_validated:
                if proof is None or self.key_registry is None:
                    state = ModelQualificationState.MODEL_LOADED_UNVALIDATED
                    rejection_reasons.append("Trusted evaluation proof required.")
                elif (
                    not validation_record.is_approved_for(manifest)
                    or proof.model_id != manifest.model_id
                    or validation_record.execution_proof_key_id != proof.key_id
                    or validation_record.execution_proof_signature != proof.proof_signature
                ):
                    state = ModelQualificationState.MODEL_REJECTED
                    rejection_reasons.append("Evaluation proof or deployment approval mismatch.")
                else:
                    verified, proof_msg = proof.verify_detailed(
                        expected_artifact_sha256=validation_record.artifact_sha256,
                        key_registry=self.key_registry,
                        expected_dataset_archive_sha256=validation_record.dataset_archive_sha256,
                    )
                    if verified:
                        state = ModelQualificationState.MODEL_VALIDATED
                    else:
                        state = ModelQualificationState.MODEL_REJECTED
                        rejection_reasons.append(f"Ed25519 proof verification failed: {proof_msg}")
            else:
                state = ModelQualificationState.MODEL_LOADED_UNVALIDATED
        else:
            state = ModelQualificationState.MODEL_LOADED_UNVALIDATED

        entry = RegisteredModelEntry(
            manifest=manifest,
            manifest_path=manifest_path,
            validation_record=validation_record,
            qualification_state=state,
            execution_proof=proof,
            activated=False,
            rejection_reasons=rejection_reasons,
        )
        with self._lock:
            existing = self._entries.get(manifest.model_id)
            if existing and existing.qualification_state == ModelQualificationState.MODEL_REVOKED:
                return copy.deepcopy(existing)
            self._manifests[manifest.model_id] = manifest.model_copy(deep=True)
            self._entries[manifest.model_id] = copy.deepcopy(entry)
        return entry

    def discover_directory(self, models_dir: str | Path) -> list[RegisteredModelEntry]:
        """Discover manifests and paired `.validation.json` records in a model directory."""
        root = Path(models_dir)
        discovered: list[RegisteredModelEntry] = []
        if not root.is_dir():
            return discovered
        for mf_path in sorted(root.glob("*.json")):
            if mf_path.name.endswith(".validation.json"):
                continue
            try:
                manifest = ModelManifest.model_validate(
                    json.loads(mf_path.read_text(encoding="utf-8"))
                )
            except Exception:
                continue
            val_path = mf_path.with_suffix(".validation.json")
            val_rec: ModelValidationRecord | None = None
            if val_path.is_file():
                try:
                    val_rec = ModelValidationRecord.load_from_file(val_path)
                except Exception:
                    val_rec = None
            discovered.append(
                self.register(manifest, validation_record=val_rec, manifest_path=mf_path)
            )
        return discovered

    def get(self, model_id: str) -> ModelManifest | None:
        """Retrieve model manifest by identifier."""
        with self._lock:
            return self._manifests.get(model_id)

    def get_entry(self, model_id: str) -> RegisteredModelEntry | None:
        """Retrieve full qualification entry by identifier."""
        with self._lock:
            return copy.deepcopy(self._entries.get(model_id))

    def list_models(self, modality: Modality | None = None) -> list[ModelManifest]:
        """List registered model manifests, optionally filtered by modality."""
        with self._lock:
            if modality is None:
                return list(self._manifests.values())
            return [m for m in self._manifests.values() if m.modality == modality]

    def list_entries(self, modality: Modality | None = None) -> list[RegisteredModelEntry]:
        """List full registry entries, optionally filtered by modality."""
        with self._lock:
            entries = copy.deepcopy(list(self._entries.values()))
            if modality is None:
                return entries
            return [e for e in entries if e.manifest.modality == modality]

    def activate_model(self, model_id: str) -> RegisteredModelEntry:
        """Activate a model ONLY if empirically validated (`MODEL_VALIDATED`); fail closed otherwise."""
        with self._lock:
            entry = self._entries.get(model_id)
            if entry is None:
                raise ERSModelIntegrityError(f"Unknown model '{model_id}' in registry.")
            is_val = entry.qualification_state == ModelQualificationState.MODEL_VALIDATED
            if is_val:
                record, proof = entry.validation_record, entry.execution_proof
                is_val = bool(
                    record
                    and proof
                    and self.key_registry
                    and record.is_approved_for(entry.manifest)
                    and proof.verify_detailed(
                        expected_artifact_sha256=record.artifact_sha256,
                        expected_dataset_archive_sha256=record.dataset_archive_sha256,
                        key_registry=self.key_registry,
                    )[0]
                )
                if not is_val:
                    entry.activated = False
                    entry.qualification_state = ModelQualificationState.MODEL_REJECTED
                    entry.rejection_reasons.append("Deployment approval or trusted proof expired.")
            ensure_model_activation_allowed(model_id, entry.qualification_state, is_val)
            entry.activated = True
            return copy.deepcopy(entry)

    def revoke_model(self, model_id: str, reason: str) -> RegisteredModelEntry:
        """Revoke a model immediately and disable activation."""
        with self._lock:
            entry = self._entries.get(model_id)
            if entry is None:
                raise ERSModelIntegrityError(f"Unknown model '{model_id}' in registry.")
            entry.qualification_state = ModelQualificationState.MODEL_REVOKED
            entry.activated = False
            entry.revocation_reason = reason.strip() or "Revoked by administrator."
            return copy.deepcopy(entry)
