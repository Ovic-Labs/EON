"""Per-session ephemeral IoU/centroid face tracker without biometric identity retention."""

from __future__ import annotations

from dataclasses import dataclass

from eon_ers.facial.detection import BoundingBox


@dataclass
class TrackedFace:
    """Session-local Spatial track for an ephemeral face bounding box."""

    track_id: str
    bbox: BoundingBox
    last_seen_timestamp: float
    frames_seen: int = 1


class SessionFaceTracker:
    """Tracks faces across video frames purely by spatial IoU without facial embeddings."""

    def __init__(self, iou_threshold: float = 0.3, ttl_seconds: float = 2.0) -> None:
        self.iou_threshold = iou_threshold
        self.ttl_seconds = ttl_seconds
        self._tracks: dict[str, TrackedFace] = {}
        self._next_id = 0

    @staticmethod
    def _iou(a: BoundingBox, b: BoundingBox) -> float:
        ix1 = max(a.x_min, b.x_min)
        iy1 = max(a.y_min, b.y_min)
        ix2 = min(a.x_max, b.x_max)
        iy2 = min(a.y_max, b.y_max)
        inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
        if inter <= 0.0:
            return 0.0
        union = a.area + b.area - inter
        return inter / union if union > 1e-8 else 0.0

    def update(self, detections: list[BoundingBox], timestamp: float) -> list[TrackedFace]:
        """Match current detections against active spatial tracks and prune expired tracks."""
        expired = [
            tid
            for tid, tr in self._tracks.items()
            if (timestamp - tr.last_seen_timestamp) > self.ttl_seconds
        ]
        for tid in expired:
            del self._tracks[tid]

        assigned: list[TrackedFace] = []
        used_tracks: set[str] = set()

        for box in detections:
            best_tid: str | None = None
            best_iou = self.iou_threshold
            for tid, tr in self._tracks.items():
                if tid in used_tracks:
                    continue
                iou = self._iou(box, tr.bbox)
                if iou >= best_iou:
                    best_iou = iou
                    best_tid = tid

            if best_tid is not None:
                used_tracks.add(best_tid)
                tr = self._tracks[best_tid]
                tr.bbox = BoundingBox(
                    x_min=box.x_min,
                    y_min=box.y_min,
                    x_max=box.x_max,
                    y_max=box.y_max,
                    confidence=box.confidence,
                    face_id=best_tid,
                    is_partial_boundary=box.is_partial_boundary,
                )
                tr.last_seen_timestamp = timestamp
                tr.frames_seen += 1
                assigned.append(tr)
            else:
                tid = f"track-{self._next_id}"
                self._next_id += 1
                used_tracks.add(tid)
                tr = TrackedFace(
                    track_id=tid,
                    bbox=BoundingBox(
                        x_min=box.x_min,
                        y_min=box.y_min,
                        x_max=box.x_max,
                        y_max=box.y_max,
                        confidence=box.confidence,
                        face_id=tid,
                        is_partial_boundary=box.is_partial_boundary,
                    ),
                    last_seen_timestamp=timestamp,
                )
                self._tracks[tid] = tr
                assigned.append(tr)

        return assigned

    def reset(self) -> None:
        self._tracks.clear()
        self._next_id = 0
