"""Measure local SDK processing and camera-read-to-result latency on a target device."""

from __future__ import annotations

import argparse
import asyncio
import json
import platform
import time
from statistics import median, quantiles
from uuid import uuid4

from ovic_eon.ers import ERSClient, ERSConfig
from ovic_eon.studio import analyze, camera_frames


async def measure(index: int, frames: int, model: str | None) -> dict[str, object]:
    config = ERSConfig(
        face_detector="opencv",
        facial_model_path=model,
        enable_speech=False,
        enable_text=False,
        enable_video=False,
        enable_multimodal_fusion=False,
    )
    roundtrip: list[float] = []
    processing: list[float] = []
    session = uuid4().hex
    async with ERSClient(config=config) as sdk:
        await sdk.register_consent(session, session)
        try:
            with camera_frames(index) as camera:
                for frame_index in range(frames + 5):
                    start = time.perf_counter()
                    frame = next(camera)
                    frame.thumbnail((config.max_image_dimension, config.max_image_dimension))
                    result = await analyze(sdk, session, session, frame)
                    if frame_index >= 5:
                        roundtrip.append((time.perf_counter() - start) * 1000)
                        processing.append(result.processing_latency_ms)
        finally:
            await sdk.revoke_consent(session)

    def stats(samples: list[float]) -> dict[str, float]:
        return {
            "median": round(median(samples), 2),
            "p95": round(quantiles(samples, n=100, method="inclusive")[94], 2),
        }

    return {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "camera_index": index,
        "frames": frames,
        "camera_read_to_result_ms": stats(roundtrip),
        "sdk_processing_ms": stats(processing),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--frames", type=int, default=100)
    parser.add_argument("--facial-model", help="Optional approved local model artifact")
    parser.add_argument("--consent-confirmed", action="store_true", help="Visible people opted in")
    args = parser.parse_args()
    if not args.consent_confirmed:
        parser.error("Confirm that any visible people consented before testing.")
    if args.frames < 2:
        parser.error("At least two frames are required.")
    try:
        print(
            json.dumps(asyncio.run(measure(args.camera, args.frames, args.facial_model)), indent=2)
        )
    except RuntimeError as exc:
        parser.exit(1, f"Camera test could not finish: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
