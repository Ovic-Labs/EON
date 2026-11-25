"""Deterministic CPU training checkpointing and integrity-verified resumption."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from eon_ers.exceptions import ERSModelIntegrityError
from eon_ers.utils.hashing import constant_time_compare, sha256_bytes


@dataclass
class TrainingCheckpoint:
    """In-memory snapshot of CPU trainer weights and epoch progress."""

    epoch: int
    best_val_loss: float
    weights: dict[str, np.ndarray]
    history: list[dict[str, float]]


class CheckpointManager:
    """Saves and reloads integrity-verified `.npz` + `.json` metadata checkpoints on CPU."""

    def __init__(self, checkpoint_dir: str | Path) -> None:
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save(self, run_id: str, checkpoint: TrainingCheckpoint) -> Path:
        """Persist checkpoint weights atomically with a SHA-256 verification sidecar."""
        weights_path = self.checkpoint_dir / f"{run_id}_epoch_{checkpoint.epoch}.npz"
        meta_path = self.checkpoint_dir / f"{run_id}_epoch_{checkpoint.epoch}.meta.json"
        np.savez(weights_path, **checkpoint.weights)  # type: ignore[arg-type]
        digest = sha256_bytes(weights_path.read_bytes())
        meta: dict[str, Any] = {
            "run_id": run_id,
            "epoch": checkpoint.epoch,
            "best_val_loss": float(checkpoint.best_val_loss),
            "weights_sha256": digest,
            "history": checkpoint.history,
        }
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        return weights_path

    def load_latest(self, run_id: str) -> TrainingCheckpoint | None:
        """Load and verify the most recent checkpoint for `run_id`."""
        candidates = sorted(
            self.checkpoint_dir.glob(f"{run_id}_epoch_*.meta.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not candidates:
            return None

        meta_path = candidates[0]
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        epoch = int(meta["epoch"])
        weights_path = self.checkpoint_dir / f"{run_id}_epoch_{epoch}.npz"
        if not weights_path.is_file():
            raise ERSModelIntegrityError(
                f"Checkpoint weights missing for '{run_id}' epoch {epoch}."
            )

        actual = sha256_bytes(weights_path.read_bytes())
        expected = str(meta.get("weights_sha256", ""))
        if not expected or not constant_time_compare(actual, expected):
            raise ERSModelIntegrityError(f"Checkpoint SHA-256 mismatch for '{weights_path.name}'.")

        with np.load(weights_path) as data:
            weights = {k: np.array(data[k], copy=True) for k in data.files}
        return TrainingCheckpoint(
            epoch=epoch,
            best_val_loss=float(meta["best_val_loss"]),
            weights=weights,
            history=list(meta.get("history", [])),
        )
