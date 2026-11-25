"""Authenticated Ed25519 execution proof and trusted public-key management for ERS.

Replaces unauthenticated SHA-256 proof hashes with asymmetric Ed25519 digital signatures
over canonical evaluation payloads, verified strictly against registered trusted public keys.
"""

from __future__ import annotations

import hmac
import json
import os
import time
from pathlib import Path
from typing import Literal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator

from eon_ers.evaluation.dataset import is_valid_sha256_digest

_PROOF_DOMAIN_SEPARATOR = b"EON-ERS-EXECUTION-PROOF-V2\x00"


def _is_valid_hex(value: str, expected_len: int) -> bool:
    c = value.strip().lower()
    return len(c) == expected_len and all(ch in "0123456789abcdef" for ch in c)


class SigningKeyPair:
    """Encapsulates an Ed25519 signing key with an explicit key identifier."""

    def __init__(self, key_id: str, private_key: Ed25519PrivateKey) -> None:
        cleaned_id = key_id.strip()
        if not cleaned_id:
            raise ValueError("Signing key_id must be a non-empty string.")
        self._key_id = cleaned_id
        self._private_key = private_key

    @property
    def key_id(self) -> str:
        """Explicit key identifier used during verification lookup."""
        return self._key_id

    @property
    def public_key(self) -> Ed25519PublicKey:
        """Corresponding Ed25519 public verification key."""
        return self._private_key.public_key()

    def public_key_pem(self) -> bytes:
        """Serialize the public key in PEM SubjectPublicKeyInfo format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )

    def sign(self, payload: bytes) -> str:
        """Sign canonical payload bytes and return a lowercase 128-char hex Ed25519 signature."""
        sig_bytes = self._private_key.sign(payload)
        return sig_bytes.hex().lower()

    @classmethod
    def generate(cls, key_id: str = "ers-eval-key-v1") -> SigningKeyPair:
        """Generate a fresh Ed25519 signing key pair."""
        return cls(key_id=key_id, private_key=Ed25519PrivateKey.generate())

    @classmethod
    def from_pem(
        cls,
        key_id: str,
        pem_data: bytes | str,
        password: bytes | None = None,
    ) -> SigningKeyPair:
        """Load an Ed25519 signing key pair from PEM-encoded private key material."""
        raw = pem_data.encode("utf-8") if isinstance(pem_data, str) else pem_data
        loaded = serialization.load_pem_private_key(raw, password=password)
        if not isinstance(loaded, Ed25519PrivateKey):
            raise ValueError("Provided private key is not an Ed25519 private key.")
        return cls(key_id=key_id, private_key=loaded)

    @classmethod
    def from_pem_file(
        cls,
        key_id: str,
        path: str | Path,
        password: bytes | None = None,
    ) -> SigningKeyPair:
        """Load an Ed25519 signing key pair from a PEM file."""
        p = Path(path)
        if not p.is_file():
            raise FileNotFoundError(f"Signing private key file not found: {p}")
        pem_bytes = p.read_bytes()
        if not pem_bytes.strip():
            raise ValueError(f"Signing private key file is empty: {p}")
        return cls.from_pem(key_id=key_id, pem_data=pem_bytes, password=password)

    @classmethod
    def from_env(cls) -> SigningKeyPair | None:
        """Load signing key pair from environment configuration, if present.

        Reads `EON_ERS_SIGNING_KEY_ID` and either `EON_ERS_SIGNING_PRIVATE_KEY_PEM`
        or `EON_ERS_SIGNING_PRIVATE_KEY_PATH`. Returns None if completely unconfigured.
        Raises ValueError if partially configured or malformed.
        """
        key_id = os.environ.get("EON_ERS_SIGNING_KEY_ID", "").strip()
        pem_inline = os.environ.get("EON_ERS_SIGNING_PRIVATE_KEY_PEM", "").strip()
        pem_path = os.environ.get("EON_ERS_SIGNING_PRIVATE_KEY_PATH", "").strip()
        if not key_id and not pem_inline and not pem_path:
            return None
        if not key_id:
            raise ValueError(
                "Environment key provisioning incomplete: EON_ERS_SIGNING_KEY_ID is required."
            )
        if pem_inline:
            return cls.from_pem(key_id=key_id, pem_data=pem_inline)
        if pem_path:
            return cls.from_pem_file(key_id=key_id, path=pem_path)
        raise ValueError(
            "Environment key provisioning incomplete: set EON_ERS_SIGNING_PRIVATE_KEY_PEM or EON_ERS_SIGNING_PRIVATE_KEY_PATH."
        )

    def __repr__(self) -> str:
        return f"SigningKeyPair(key_id={self._key_id!r}, algorithm='Ed25519')"


class TrustedKeyRegistry:
    """Registry of trusted Ed25519 public keys indexed by explicit key_id with rotation & revocation."""

    def __init__(self) -> None:
        self._keys: dict[str, Ed25519PublicKey] = {}
        self._revoked_keys: set[str] = set()

    def register_public_key(self, key_id: str, public_key: Ed25519PublicKey) -> None:
        """Register a trusted Ed25519 public key for a non-empty key identifier."""
        cleaned_id = key_id.strip()
        if not cleaned_id:
            raise ValueError("Trusted key_id must be a non-empty string.")
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Trusted public key must be an Ed25519PublicKey instance.")
        if cleaned_id in self._revoked_keys:
            raise ValueError(
                f"Cannot re-register revoked key_id '{cleaned_id}'; use a new key identifier."
            )
        self._keys[cleaned_id] = public_key

    def register_public_key_pem(self, key_id: str, pem_data: bytes | str) -> None:
        """Load and register a trusted Ed25519 public key from PEM data."""
        raw = pem_data.encode("utf-8") if isinstance(pem_data, str) else pem_data
        if not raw.strip():
            raise ValueError("Public key PEM payload cannot be empty.")
        loaded = serialization.load_pem_public_key(raw)
        if not isinstance(loaded, Ed25519PublicKey):
            raise ValueError("Provided public key is not an Ed25519 public key.")
        self.register_public_key(key_id, loaded)

    def register_keypair(self, keypair: SigningKeyPair) -> None:
        """Register ONLY the public verification key from a SigningKeyPair."""
        self.register_public_key(keypair.key_id, keypair.public_key)

    def revoke_key(self, key_id: str) -> bool:
        """Permanently revoke a key identifier so it can no longer verify execution proofs."""
        cleaned = key_id.strip()
        existed = self._keys.pop(cleaned, None) is not None
        if cleaned:
            self._revoked_keys.add(cleaned)
        return existed

    def rotate_key(
        self,
        old_key_id: str,
        new_key_id: str,
        new_public_key: Ed25519PublicKey | SigningKeyPair,
        *,
        revoke_old: bool = True,
    ) -> None:
        """Rotate signing authority from old_key_id to new_key_id safely."""
        clean_old = old_key_id.strip()
        clean_new = new_key_id.strip()
        if not clean_new or clean_new == clean_old:
            raise ValueError("Key rotation requires a distinct, non-empty new_key_id.")
        pub = (
            new_public_key.public_key
            if isinstance(new_public_key, SigningKeyPair)
            else new_public_key
        )
        self.register_public_key(clean_new, pub)
        if revoke_old and clean_old:
            self.revoke_key(clean_old)

    def is_revoked(self, key_id: str) -> bool:
        """Return True if key_id has been explicitly revoked."""
        return key_id.strip() in self._revoked_keys

    def is_trusted(self, key_id: str) -> bool:
        """Check whether key_id is currently active and trusted."""
        cleaned = key_id.strip()
        return cleaned in self._keys and cleaned not in self._revoked_keys

    def get_public_key(self, key_id: str) -> Ed25519PublicKey | None:
        """Retrieve the trusted Ed25519 public key for key_id, or None."""
        cleaned = key_id.strip()
        if cleaned in self._revoked_keys:
            return None
        return self._keys.get(cleaned)

    @property
    def trusted_key_ids(self) -> list[str]:
        """List all currently trusted key identifiers."""
        return sorted(self._keys.keys())

    @property
    def revoked_key_ids(self) -> list[str]:
        """List all revoked key identifiers."""
        return sorted(self._revoked_keys)


class EvaluationExecutionProof(BaseModel):
    """Cryptographically authenticated Ed25519 proof binding evaluation execution to evidence."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    proof_version: Literal["2.0.0"] = Field(
        default="2.0.0", description="Execution proof schema version."
    )
    signature_algorithm: Literal["Ed25519"] = Field(
        default="Ed25519", description="Asymmetric signature algorithm."
    )
    key_id: str = Field(..., min_length=1, description="Explicit signing key identifier.")
    model_id: str = Field(..., min_length=1, description="Target model identifier.")
    artifact_sha256: str = Field(
        ..., min_length=64, max_length=64, description="Model artifact SHA-256."
    )
    dataset_archive_sha256: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="Verified empirical dataset archive SHA-256.",
    )
    dataset_name: str = Field(..., min_length=1, description="Dataset name.")
    dataset_provenance: str = Field(
        ..., min_length=1, description="Verified dataset provenance / license."
    )
    subject_count: int = Field(
        ..., ge=1, description="Distinct subject count in evaluation partition."
    )
    sample_count: int = Field(..., ge=1, description="Sample count in evaluation partition.")
    evaluation_script_version: str = Field(
        default="1.0.0", min_length=1, description="Evaluation script version."
    )
    execution_timestamp: str = Field(..., min_length=1, description="ISO 8601 execution timestamp.")
    inference_hardware: str = Field(
        default="Intel Core Ultra 5 225U (CPU)",
        min_length=1,
        description="Execution hardware environment.",
    )
    proof_signature: str = Field(
        ...,
        min_length=128,
        max_length=128,
        description="Hex-encoded 64-byte Ed25519 signature over canonical execution proof payload.",
    )

    @field_validator(
        "key_id",
        "model_id",
        "dataset_name",
        "dataset_provenance",
        "evaluation_script_version",
        "execution_timestamp",
        "inference_hardware",
    )
    @classmethod
    def _reject_blank_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Execution proof string fields cannot be blank.")
        return stripped

    @field_validator("artifact_sha256", "dataset_archive_sha256")
    @classmethod
    def _validate_digest(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not is_valid_sha256_digest(cleaned):
            raise ValueError(f"Invalid or placeholder SHA-256 digest in execution proof: {value!r}")
        return cleaned

    @field_validator("proof_signature")
    @classmethod
    def _validate_sig_hex(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not _is_valid_hex(cleaned, 128):
            raise ValueError(
                "Execution proof signature must be a 128-character hex Ed25519 signature."
            )
        return cleaned

    @staticmethod
    def _build_canonical_payload(
        *,
        proof_version: str,
        signature_algorithm: str,
        key_id: str,
        model_id: str,
        artifact_sha256: str,
        dataset_archive_sha256: str,
        dataset_name: str,
        dataset_provenance: str,
        subject_count: int,
        sample_count: int,
        evaluation_script_version: str,
        execution_timestamp: str,
        inference_hardware: str,
    ) -> bytes:
        payload = {
            "proof_version": proof_version,
            "signature_algorithm": signature_algorithm,
            "key_id": key_id,
            "model_id": model_id,
            "artifact_sha256": artifact_sha256.lower(),
            "dataset_archive_sha256": dataset_archive_sha256.lower(),
            "dataset_name": dataset_name,
            "dataset_provenance": dataset_provenance,
            "subject_count": subject_count,
            "sample_count": sample_count,
            "evaluation_script_version": evaluation_script_version,
            "execution_timestamp": execution_timestamp,
            "inference_hardware": inference_hardware,
        }
        serialized = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode("utf-8")
        return _PROOF_DOMAIN_SEPARATOR + serialized

    def canonical_payload_bytes(self) -> bytes:
        """Return deterministic domain-separated bytes signed by the Ed25519 key."""
        return self._build_canonical_payload(
            proof_version=self.proof_version,
            signature_algorithm=self.signature_algorithm,
            key_id=self.key_id,
            model_id=self.model_id,
            artifact_sha256=self.artifact_sha256,
            dataset_archive_sha256=self.dataset_archive_sha256,
            dataset_name=self.dataset_name,
            dataset_provenance=self.dataset_provenance,
            subject_count=self.subject_count,
            sample_count=self.sample_count,
            evaluation_script_version=self.evaluation_script_version,
            execution_timestamp=self.execution_timestamp,
            inference_hardware=self.inference_hardware,
        )

    @classmethod
    def generate_proof(
        cls,
        model_id: str,
        artifact_sha256: str,
        dataset_archive_sha256: str,
        dataset_name: str,
        dataset_provenance: str,
        subject_count: int,
        sample_count: int,
        signing_key: SigningKeyPair,
        evaluation_script_version: str = "1.0.0",
        inference_hardware: str = "Intel Core Ultra 5 225U (CPU)",
        execution_timestamp: str | None = None,
    ) -> EvaluationExecutionProof:
        """Construct and cryptographically sign an Ed25519 execution proof."""
        if not isinstance(signing_key, SigningKeyPair):
            raise TypeError("signing_key must be a valid SigningKeyPair instance.")

        clean_artifact_sha = artifact_sha256.strip().lower()
        clean_dataset_sha = dataset_archive_sha256.strip().lower()
        if not is_valid_sha256_digest(clean_artifact_sha):
            raise ValueError("Cannot sign execution proof: invalid or placeholder artifact_sha256.")
        if not is_valid_sha256_digest(clean_dataset_sha):
            raise ValueError(
                "Cannot sign execution proof: invalid or placeholder dataset_archive_sha256."
            )

        ts = execution_timestamp or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        canonical_bytes = cls._build_canonical_payload(
            proof_version="2.0.0",
            signature_algorithm="Ed25519",
            key_id=signing_key.key_id,
            model_id=model_id.strip(),
            artifact_sha256=clean_artifact_sha,
            dataset_archive_sha256=clean_dataset_sha,
            dataset_name=dataset_name.strip(),
            dataset_provenance=dataset_provenance.strip(),
            subject_count=subject_count,
            sample_count=sample_count,
            evaluation_script_version=evaluation_script_version.strip(),
            execution_timestamp=ts.strip(),
            inference_hardware=inference_hardware.strip(),
        )
        signature = signing_key.sign(canonical_bytes)

        return cls(
            proof_version="2.0.0",
            signature_algorithm="Ed25519",
            key_id=signing_key.key_id,
            model_id=model_id,
            artifact_sha256=clean_artifact_sha,
            dataset_archive_sha256=clean_dataset_sha,
            dataset_name=dataset_name,
            dataset_provenance=dataset_provenance,
            subject_count=subject_count,
            sample_count=sample_count,
            evaluation_script_version=evaluation_script_version,
            execution_timestamp=ts,
            inference_hardware=inference_hardware,
            proof_signature=signature,
        )

    def verify_detailed(
        self,
        expected_artifact_sha256: str,
        key_registry: TrustedKeyRegistry | None = None,
        expected_dataset_archive_sha256: str | None = None,
    ) -> tuple[bool, str]:
        """Verify proof integrity, payload bounds, and Ed25519 signature against trusted public keys."""
        proof_ver: str = str(self.proof_version)
        if proof_ver != "2.0.0":
            return False, f"Unsupported execution proof version: '{proof_ver}'."

        sig_alg: str = str(self.signature_algorithm)
        if sig_alg != "Ed25519":
            return (
                False,
                f"Algorithm confusion rejected: expected 'Ed25519', got '{sig_alg}'.",
            )

        if key_registry is None:
            return False, "No trusted public-key registry provided for proof verification."

        if key_registry.is_revoked(self.key_id):
            return False, f"Execution proof signed by revoked key_id: '{self.key_id}'."

        if not self.key_id or not key_registry.is_trusted(self.key_id):
            return False, f"Untrusted or unknown execution proof key_id: '{self.key_id}'."

        expected_art = expected_artifact_sha256.strip().lower()
        if not is_valid_sha256_digest(expected_art):
            return False, "Expected artifact SHA-256 is invalid or a placeholder."

        if not hmac.compare_digest(self.artifact_sha256.lower(), expected_art):
            return False, "Proof artifact SHA-256 does not match target model artifact."

        if not is_valid_sha256_digest(self.dataset_archive_sha256):
            return False, "Proof dataset_archive_sha256 is invalid or a placeholder."

        if expected_dataset_archive_sha256 is not None:
            expected_ds = expected_dataset_archive_sha256.strip().lower()
            if not is_valid_sha256_digest(expected_ds) or not hmac.compare_digest(
                self.dataset_archive_sha256.lower(), expected_ds
            ):
                return False, "Proof dataset_archive_sha256 does not match verified archive digest."

        if self.sample_count < 10 or self.subject_count < 2:
            return (
                False,
                f"Insufficient evaluation scope in proof (samples={self.sample_count}, subjects={self.subject_count}).",
            )

        public_key = key_registry.get_public_key(self.key_id)
        if public_key is None:
            return False, f"Public key missing for key_id '{self.key_id}'."

        try:
            sig_bytes = bytes.fromhex(self.proof_signature)
        except ValueError:
            return False, "Malformed hex signature in execution proof."

        if len(sig_bytes) != 64:
            return (
                False,
                f"Invalid Ed25519 signature length: expected 64 bytes, got {len(sig_bytes)}.",
            )

        try:
            public_key.verify(sig_bytes, self.canonical_payload_bytes())
        except InvalidSignature:
            return False, "Ed25519 signature verification failed: payload tampered or key mismatch."
        except Exception as exc:
            return False, f"Execution proof cryptographic verification error: {exc}"

        return (
            True,
            f"Execution proof verified (key_id={self.key_id}, alg={self.signature_algorithm}).",
        )

    def verify(
        self,
        expected_artifact_sha256: str,
        key_registry: TrustedKeyRegistry | None = None,
        expected_dataset_archive_sha256: str | None = None,
    ) -> bool:
        """Verify proof integrity and Ed25519 signature against trusted public keys."""
        ok, _ = self.verify_detailed(
            expected_artifact_sha256=expected_artifact_sha256,
            key_registry=key_registry,
            expected_dataset_archive_sha256=expected_dataset_archive_sha256,
        )
        return ok
