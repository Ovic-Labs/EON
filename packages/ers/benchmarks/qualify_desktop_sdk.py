"""Exercise local ERS image inference on 1,000 deterministic engineering cases."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import platform
import time
from collections import Counter
from collections.abc import Iterator
from itertools import product
from pathlib import Path
from statistics import median, quantiles
from typing import Literal

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from ovic_eon.ers import ERSClient, ERSConfig
from ovic_eon.studio import analyze

Box = tuple[float, float, float, float]
FRAME_SIZE = 384
IOU_THRESHOLD = 0.5


def iou(expected: Box, actual: dict[str, float]) -> float:
    x1, y1, x2, y2 = expected
    a1, b1, a2, b2 = (actual[key] for key in ("x_min", "y_min", "x_max", "y_max"))
    overlap = max(0.0, min(x2, a2) - max(x1, a1)) * max(0.0, min(y2, b2) - max(y1, b1))
    union = (x2 - x1) * (y2 - y1) + (a2 - a1) * (b2 - b1) - overlap
    return overlap / union if union > 0 else 0.0


def variants(image: Image.Image, face: Box | None) -> Iterator[tuple[Image.Image, Box | None]]:
    """Five sizes, five placements per axis, four brightness levels, two orientations."""
    for size, rx, ry, brightness, mirror in product(
        (180, 220, 260, 300, 340),
        (0.0, 0.25, 0.5, 0.75, 1.0),
        (0.0, 0.25, 0.5, 0.75, 1.0),
        (0.65, 0.85, 1.0, 1.2),
        (False, True),
    ):
        thumbnail = ImageOps.contain(image, (size, size))
        if mirror:
            thumbnail = ImageOps.mirror(thumbnail)
        thumbnail = ImageEnhance.Brightness(thumbnail).enhance(brightness)
        width, height = thumbnail.size
        dx, dy = round(rx * (FRAME_SIZE - width)), round(ry * (FRAME_SIZE - height))
        canvas = Image.new("RGB", (FRAME_SIZE, FRAME_SIZE), (88, 91, 96))
        canvas.paste(thumbnail, (dx, dy))
        actual_face = None
        if face is not None:
            x1, y1, x2, y2 = face
            if mirror:
                x1, x2 = 1 - x2, 1 - x1
            actual_face = (
                (dx + x1 * width) / FRAME_SIZE,
                (dy + y1 * height) / FRAME_SIZE,
                (dx + x2 * width) / FRAME_SIZE,
                (dy + y2 * height) / FRAME_SIZE,
            )
        yield canvas, actual_face


def load_rgb(path: Path) -> Image.Image:
    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB")


async def qualify(
    portrait: Path, face_box: Box, background: Path, detector: Literal["heuristic", "opencv"]
) -> dict[str, object]:
    config = ERSConfig(
        face_detector=detector,
        enable_speech=False,
        enable_text=False,
        enable_video=False,
        enable_multimodal_fusion=False,
    )
    start = time.perf_counter()
    counts: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    latencies: list[float] = []
    hashes: set[str] = set()
    rng = np.random.default_rng(20261127)
    groups = (
        ("portrait", variants(load_rgb(portrait), face_box)),
        ("no_face", variants(load_rgb(background), None)),
    )

    async with ERSClient(config=config) as client:
        for group, cases in groups:
            selected = set(rng.choice(1000, size=500, replace=False).tolist())
            for index, (image, expected_box) in enumerate(cases):
                if index not in selected:
                    continue
                hashes.add(hashlib.sha256(image.tobytes()).hexdigest())
                session = f"qualification-{group}-{index}"
                await client.register_consent(session, session)
                try:
                    result = await analyze(client, session, session, image)
                finally:
                    await client.revoke_consent(session)
                statuses[result.status.value] += 1
                latencies.append(result.processing_latency_ms)
                counts[group] += 1
                if result.is_definitive_claim:
                    counts["definitive_claims"] += 1
                if result.dominant_estimate in ("unknown", "insufficient_evidence"):
                    counts["abstentions"] += 1
                if result.is_validated:
                    counts["validated_outputs"] += 1
                if expected_box is None:
                    if result.face_bbox is not None:
                        counts["false_face_boxes"] += 1
                elif result.face_bbox is None:
                    counts["missing_face_boxes"] += 1
                elif iou(expected_box, result.face_bbox) >= IOU_THRESHOLD:
                    counts["face_box_matches"] += 1
                else:
                    counts["misplaced_face_boxes"] += 1

    return {
        "inputs": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (portrait, background)
        },
        "environment": {"python": platform.python_version(), "machine": platform.machine()},
        "detector": detector,
        "cases": sum(statuses.values()),
        "unique_images": len(hashes),
        "counts": {
            key: counts[key]
            for key in (
                "portrait",
                "no_face",
                "face_box_matches",
                "misplaced_face_boxes",
                "missing_face_boxes",
                "false_face_boxes",
                "abstentions",
                "definitive_claims",
                "validated_outputs",
            )
        },
        "status_counts": dict(statuses),
        "iou_threshold": IOU_THRESHOLD,
        "processing_latency_ms": {
            "median": round(median(latencies), 2),
            "p95": round(quantiles(latencies, n=100)[94], 2),
        },
        "elapsed_seconds": round(time.perf_counter() - start, 2),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portrait", type=Path, required=True)
    parser.add_argument(
        "--face-box", nargs=4, type=float, required=True, help="Normalized x1 y1 x2 y2"
    )
    parser.add_argument("--background", type=Path, required=True, help="A face-free photo")
    parser.add_argument("--detector", choices=("heuristic", "opencv"), default="heuristic")
    args = parser.parse_args()
    x1, y1, x2, y2 = args.face_box
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        parser.error("The face box must contain ordered coordinates within 0–1.")
    result = asyncio.run(qualify(args.portrait, (x1, y1, x2, y2), args.background, args.detector))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
