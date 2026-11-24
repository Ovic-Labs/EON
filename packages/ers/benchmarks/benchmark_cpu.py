"""Reproducible CPU performance benchmark for ERS on Intel Core Ultra 5 architectures."""

from __future__ import annotations

import asyncio
import io
import json
import os
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np
from eon_ers.config import ERSConfig
from eon_ers.contracts import ERSInput
from eon_ers.engine import ERSEngine
from eon_ers.types import DeviceType, Modality
from PIL import Image


def generate_synthetic_face_bytes() -> bytes:
    """Generate a clean synthetic facial image fixture."""
    img = Image.new("RGB", (128, 128), color=(200, 180, 160))
    # Draw simple facial feature contrast patches
    arr = np.array(img)
    arr[30:45, 30:50] = (50, 50, 50)  # Left eye
    arr[30:45, 78:98] = (50, 50, 50)  # Right eye
    arr[75:90, 40:88] = (180, 60, 60)  # Mouth
    synth = Image.fromarray(arr)
    buf = io.BytesIO()
    synth.save(buf, format="JPEG")
    return buf.getvalue()


def generate_synthetic_speech_bytes() -> bytes:
    """Generate a 1-second 16kHz speech tone fixture."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # Fundamental frequency at 160 Hz with harmonics
    audio = 0.4 * np.sin(2 * np.pi * 160 * t) + 0.2 * np.sin(2 * np.pi * 320 * t)
    audio_int16 = (audio * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


async def run_cpu_benchmark(iterations: int = 50) -> dict[str, Any]:
    """Execute complete reproducible CPU benchmark measuring latency percentiles and RSS."""
    print("=== OVIC EON ERS: CPU Performance Benchmark ===")
    print("Hardware Target: Intel Core Ultra 5 225U (CPU Execution)")
    print(f"Benchmark Iterations: {iterations}\n")

    # 1. Startup & Initialization Time
    t_init_start = time.perf_counter()
    config = ERSConfig(
        device=DeviceType.CPU,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
        num_threads=4,
    )
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()
    init_duration_ms = (time.perf_counter() - t_init_start) * 1000.0

    face_bytes = generate_synthetic_face_bytes()
    speech_bytes = generate_synthetic_speech_bytes()

    # 2. Cold-Start Latencies
    t0 = time.perf_counter()
    cold_face_inp = ERSInput(
        session_id="bench-session",
        modality=Modality.FACIAL,
        consent_reference="bench-consent-token-2026",
        image_payload=face_bytes,
    )
    await engine.process_facial(cold_face_inp)
    cold_face_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    cold_speech_inp = ERSInput(
        session_id="bench-session",
        modality=Modality.SPEECH,
        consent_reference="bench-consent-token-2026",
        audio_payload=speech_bytes,
        sample_rate=16000,
    )
    await engine.process_speech(cold_speech_inp)
    cold_speech_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    cold_mm_inp_f = ERSInput(
        session_id="bench-session",
        modality=Modality.FACIAL,
        consent_reference="bench-consent-token-2026",
        image_payload=face_bytes,
    )
    cold_mm_inp_s = ERSInput(
        session_id="bench-session",
        modality=Modality.SPEECH,
        consent_reference="bench-consent-token-2026",
        audio_payload=speech_bytes,
        sample_rate=16000,
    )
    await engine.process_multimodal(cold_mm_inp_f, cold_mm_inp_s)
    cold_multimodal_ms = (time.perf_counter() - t0) * 1000.0

    # 3. Warm Iterations
    warm_facial_latencies: list[float] = []
    warm_speech_latencies: list[float] = []
    warm_multimodal_latencies: list[float] = []

    for _ in range(iterations):
        inp_f = ERSInput(
            session_id="bench-session",
            modality=Modality.FACIAL,
            consent_reference="bench-consent-token-2026",
            image_payload=face_bytes,
        )
        t_start = time.perf_counter()
        await engine.process_facial(inp_f)
        warm_facial_latencies.append((time.perf_counter() - t_start) * 1000.0)

        inp_s = ERSInput(
            session_id="bench-session",
            modality=Modality.SPEECH,
            consent_reference="bench-consent-token-2026",
            audio_payload=speech_bytes,
            sample_rate=16000,
        )
        t_start = time.perf_counter()
        await engine.process_speech(inp_s)
        warm_speech_latencies.append((time.perf_counter() - t_start) * 1000.0)

        inp_mf = ERSInput(
            session_id="bench-session",
            modality=Modality.FACIAL,
            consent_reference="bench-consent-token-2026",
            image_payload=face_bytes,
        )
        inp_ms = ERSInput(
            session_id="bench-session",
            modality=Modality.SPEECH,
            consent_reference="bench-consent-token-2026",
            audio_payload=speech_bytes,
            sample_rate=16000,
        )
        t_start = time.perf_counter()
        await engine.process_multimodal(inp_mf, inp_ms)
        warm_multimodal_latencies.append((time.perf_counter() - t_start) * 1000.0)

    # 4. Memory RSS
    rss_mb = 0.0
    try:
        import psutil  # type: ignore

        rss_mb = round(psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024), 2)
    except Exception:
        pass

    await engine.stop()

    def calc_stats(arr: list[float]) -> dict[str, float]:
        np_arr = np.array(arr)
        return {
            "mean": round(float(np.mean(np_arr)), 2),
            "p50": round(float(np.percentile(np_arr, 50)), 2),
            "p90": round(float(np.percentile(np_arr, 90)), 2),
            "p95": round(float(np.percentile(np_arr, 95)), 2),
            "p99": round(float(np.percentile(np_arr, 99)), 2),
            "min": round(float(np.min(np_arr)), 2),
            "max": round(float(np.max(np_arr)), 2),
        }

    results = {
        "hardware_target": "Intel Core Ultra 5 225U",
        "device": "cpu",
        "num_threads": 4,
        "iterations": iterations,
        "initialization_ms": round(init_duration_ms, 2),
        "peak_rss_mb": rss_mb,
        "cold_latencies_ms": {
            "facial": round(cold_face_ms, 2),
            "speech": round(cold_speech_ms, 2),
            "multimodal": round(cold_multimodal_ms, 2),
        },
        "warm_facial_latency_ms": calc_stats(warm_facial_latencies),
        "warm_speech_latency_ms": calc_stats(warm_speech_latencies),
        "warm_multimodal_latency_ms": calc_stats(warm_multimodal_latencies),
    }

    # Save to disk
    out_path = Path("packages/ers/benchmarks/cpu_benchmark_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))
    print(f"\nBenchmark results saved to: {out_path.resolve()}")
    return results


if __name__ == "__main__":
    asyncio.run(run_cpu_benchmark(iterations=30))
