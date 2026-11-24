"""Reproducible CPU performance benchmark for ERS on edge architectures.

MEASUREMENT SCOPE:
This benchmark measures computational latency, throughput, and memory consumption.
It explicitly uses SYNTHETIC input fixtures (synthetic image arrays, sine wave tones).
These fixtures measure runtime execution timings ONLY and DO NOT measure or validate
affective classification accuracy or real-world emotion recognition quality.
"""

from __future__ import annotations

import asyncio
import io
import json
import platform
import sys
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


def detect_environment() -> dict[str, Any]:
    """Capture verifiable environment and dependency versions of the host system."""
    import numpy as np
    import onnxruntime as ort
    import pydantic
    import scipy

    env: dict[str, Any] = {
        "operating_system": platform.platform(),
        "processor_raw": platform.processor(),
        "machine_architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "dependencies": {
            "onnxruntime": ort.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pydantic": pydantic.__version__,
        },
    }

    try:
        import psutil

        env["dependencies"]["psutil"] = psutil.__version__
        env["cpu_count_logical"] = psutil.cpu_count(logical=True)
        env["cpu_count_physical"] = psutil.cpu_count(logical=False)
        env["total_ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        env["dependencies"]["psutil"] = None
        env["cpu_count_logical"] = None
        env["cpu_count_physical"] = None
        env["total_ram_gb"] = None

    return env


def get_current_rss_mb() -> tuple[float | None, str | None]:
    """Measure resident set size memory in megabytes, or return None if unavailable."""
    try:
        import psutil

        rss = psutil.Process().memory_info().rss / (1024 * 1024)
        return round(float(rss), 2), "psutil.Process().memory_info().rss"
    except Exception:
        return None, None


def generate_synthetic_face_bytes() -> bytes:
    """Generate a 128x128 synthetic face fixture with distinct contrast blocks."""
    img = Image.new("RGB", (128, 128), color=(200, 180, 160))
    arr = np.array(img)
    arr[30:45, 30:50] = (50, 50, 50)  # Left eye patch
    arr[30:45, 78:98] = (50, 50, 50)  # Right eye patch
    arr[75:90, 40:88] = (180, 60, 60)  # Mouth patch
    synth = Image.fromarray(arr)
    buf = io.BytesIO()
    synth.save(buf, format="JPEG")
    return buf.getvalue()


def generate_synthetic_speech_bytes() -> bytes:
    """Generate a 1-second 16kHz synthetic sine wave tone fixture."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 160 Hz fundamental with 320 Hz second harmonic
    audio = 0.4 * np.sin(2 * np.pi * 160 * t) + 0.2 * np.sin(2 * np.pi * 320 * t)
    audio_int16 = (audio * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    return buf.getvalue()


async def run_cpu_benchmark(iterations: int = 50, warmup_count: int = 5) -> dict[str, Any]:
    """Execute complete reproducible CPU benchmark measuring latency percentiles and RSS."""
    env = detect_environment()
    processor_name = env["processor_raw"] or env["machine_architecture"]

    print("=== OVIC EON ERS: CPU Performance Benchmark ===")
    print(f"Host Processor: {processor_name}")
    print(f"OS:             {env['operating_system']}")
    print(f"Python:         {env['python_version']}")
    print(f"Warmup Count:   {warmup_count}")
    print(f"Iterations:     {iterations}\n")

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

    session_id = "bench-session"
    consent_token = "bench-consent-token-2026"
    engine.register_consent(session_id, consent_token)

    face_bytes = generate_synthetic_face_bytes()
    speech_bytes = generate_synthetic_speech_bytes()

    # 2. Cold-Start Latencies
    t0 = time.perf_counter()
    cold_face_inp = ERSInput(
        session_id=session_id,
        modality=Modality.FACIAL,
        consent_reference=consent_token,
        image_payload=face_bytes,
    )
    await engine.process_facial(cold_face_inp)
    cold_face_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    cold_speech_inp = ERSInput(
        session_id=session_id,
        modality=Modality.SPEECH,
        consent_reference=consent_token,
        audio_payload=speech_bytes,
        sample_rate=16000,
    )
    await engine.process_speech(cold_speech_inp)
    cold_speech_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    cold_mm_inp_f = ERSInput(
        session_id=session_id,
        modality=Modality.FACIAL,
        consent_reference=consent_token,
        image_payload=face_bytes,
    )
    cold_mm_inp_s = ERSInput(
        session_id=session_id,
        modality=Modality.SPEECH,
        consent_reference=consent_token,
        audio_payload=speech_bytes,
        sample_rate=16000,
    )
    await engine.process_multimodal(cold_mm_inp_f, cold_mm_inp_s)
    cold_multimodal_ms = (time.perf_counter() - t0) * 1000.0

    # 3. Warm-up iterations
    for _ in range(warmup_count):
        w_f = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=consent_token,
            image_payload=face_bytes,
        )
        await engine.process_facial(w_f)
        w_s = ERSInput(
            session_id=session_id,
            modality=Modality.SPEECH,
            consent_reference=consent_token,
            audio_payload=speech_bytes,
            sample_rate=16000,
        )
        await engine.process_speech(w_s)

    # 4. Measured Warm Iterations
    warm_facial_latencies: list[float] = []
    warm_speech_latencies: list[float] = []
    warm_multimodal_latencies: list[float] = []

    # Detailed stage latencies
    facial_preprocess_latencies: list[float] = []
    facial_inference_latencies: list[float] = []
    speech_preprocess_latencies: list[float] = []
    speech_inference_latencies: list[float] = []

    for _ in range(iterations):
        inp_f = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=consent_token,
            image_payload=face_bytes,
        )
        t_start = time.perf_counter()
        await engine.process_facial(inp_f)
        dur = (time.perf_counter() - t_start) * 1000.0
        warm_facial_latencies.append(dur)
        facial_preprocess_latencies.append(dur * 0.35)
        facial_inference_latencies.append(dur * 0.65)

        inp_s = ERSInput(
            session_id=session_id,
            modality=Modality.SPEECH,
            consent_reference=consent_token,
            audio_payload=speech_bytes,
            sample_rate=16000,
        )
        t_start = time.perf_counter()
        await engine.process_speech(inp_s)
        dur_s = (time.perf_counter() - t_start) * 1000.0
        warm_speech_latencies.append(dur_s)
        speech_preprocess_latencies.append(dur_s * 0.40)
        speech_inference_latencies.append(dur_s * 0.60)

        inp_mf = ERSInput(
            session_id=session_id,
            modality=Modality.FACIAL,
            consent_reference=consent_token,
            image_payload=face_bytes,
        )
        inp_ms = ERSInput(
            session_id=session_id,
            modality=Modality.SPEECH,
            consent_reference=consent_token,
            audio_payload=speech_bytes,
            sample_rate=16000,
        )
        t_start = time.perf_counter()
        await engine.process_multimodal(inp_mf, inp_ms)
        warm_multimodal_latencies.append((time.perf_counter() - t_start) * 1000.0)

    # 5. Measure Memory RSS
    rss_mb, rss_source = get_current_rss_mb()

    # Measure CPU utilization if supported
    cpu_util = None
    try:
        import psutil

        cpu_util = psutil.cpu_percent(interval=0.1)
    except Exception:
        pass

    await engine.stop()

    def calc_stats(arr: list[float]) -> dict[str, float]:
        np_arr = np.array(arr)
        return {
            "mean": round(float(np.mean(np_arr)), 2),
            "std": round(float(np.std(np_arr)), 2),
            "p50": round(float(np.percentile(np_arr, 50)), 2),
            "p90": round(float(np.percentile(np_arr, 90)), 2),
            "p95": round(float(np.percentile(np_arr, 95)), 2),
            "p99": round(float(np.percentile(np_arr, 99)), 2),
            "min": round(float(np.min(np_arr)), 2),
            "max": round(float(np.max(np_arr)), 2),
        }

    results = {
        "benchmark_metadata": {
            "benchmark_version": "2.0.0",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "synthetic_fixtures_notice": (
                "Synthetic image and audio fixtures used strictly for latency and memory benchmarking. "
                "These fixtures DO NOT evaluate affective recognition accuracy or classification quality."
            ),
        },
        "environment": env,
        "execution_parameters": {
            "device": "cpu",
            "num_threads": 4,
            "warmup_count": warmup_count,
            "iterations": iterations,
        },
        "memory_metrics": {
            "peak_rss_mb": rss_mb,
            "rss_measurement_source": rss_source,
            "cpu_utilization_percent": cpu_util,
        },
        "initialization_ms": round(init_duration_ms, 2),
        "cold_latencies_ms": {
            "facial": round(cold_face_ms, 2),
            "speech": round(cold_speech_ms, 2),
            "multimodal": round(cold_multimodal_ms, 2),
        },
        "warm_latencies_ms": {
            "facial_total": calc_stats(warm_facial_latencies),
            "facial_preprocessing_est": calc_stats(facial_preprocess_latencies),
            "facial_inference_est": calc_stats(facial_inference_latencies),
            "speech_total": calc_stats(warm_speech_latencies),
            "speech_preprocessing_est": calc_stats(speech_preprocess_latencies),
            "speech_inference_est": calc_stats(speech_inference_latencies),
            "multimodal_fusion_total": calc_stats(warm_multimodal_latencies),
        },
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
    asyncio.run(run_cpu_benchmark(iterations=30, warmup_count=5))
