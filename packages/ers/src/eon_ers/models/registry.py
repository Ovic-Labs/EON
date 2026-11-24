"""Model registry for ERS model discovery, governance, and registration."""

from __future__ import annotations

import threading

from eon_ers.models.manifest import ModelManifest
from eon_ers.types import Modality


class ModelRegistry:
    """Thread-safe registry of verified model manifests."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._manifests: dict[str, ModelManifest] = {}

    def register(self, manifest: ModelManifest) -> None:
        """Register a verified model manifest."""
        with self._lock:
            self._manifests[manifest.model_id] = manifest

    def get(self, model_id: str) -> ModelManifest | None:
        """Retrieve model manifest by identifier."""
        with self._lock:
            return self._manifests.get(model_id)

    def list_models(self, modality: Modality | None = None) -> list[ModelManifest]:
        """List registered model manifests, optionally filtered by modality."""
        with self._lock:
            if modality is None:
                return list(self._manifests.values())
            return [m for m in self._manifests.values() if m.modality == modality]
