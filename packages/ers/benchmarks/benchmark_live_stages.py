"""Fine-grained execution latency benchmark for ERS live streaming stages.

Measures actual wall-clock elapsed time for each discrete stage in the live sensory
processing pipeline using time.perf_counter().

STAGES MEASURED:
1. frame_decode: Ingesting base64 string and decoding JPEG payload into image buffer.
2. face_detect_landmarks: Face detection, bounding box verification, and landmark localization.
3. facial_inference: Facial tensor preprocessing and ONNX model execution.
4. audio_decode: Ingesting base64 audio and parsing WAV PCM stream into float32 array.
5. speech_prosody_inference: F0/energy acoustic feature extraction and ONNX model inference.
6. multimodal_fusion: Weighted Bayesian multimodal fusion and composite uncertainty computation.
7. temporal_smoothing: Temporal exponential moving average and window smoothing.
8. serialization: Pydantic outbound message model validation and JSON serialization.
9. end_to_end_live_stream: Full end-to-end live manager execution per multimodal tick.

NON-NEGOTIABLE BENCHMARK RULES:
- All timings are measured via time.perf_counter() directly on the host hardware.
- No fixed percentages or synthetic latency extrapolations are used.
- Benchmarks run with warm-up cycles to stabilize CPU cache and JIT/runtime caches.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import logging
import platform
import sys
import time
import wave
from pathlib import Path
from typing import Any

import numpy as np
from eon_ers.api.schemas import LiveStreamOutboundMessage
from eon_ers.config import ERSConfig
from eon_ers.contracts import EmotionObservation, FusionResult
from eon_ers.engine import ERSEngine
from eon_ers.live.manager import LiveSessionManager
from eon_ers.types import Modality, ObservationStatus
from PIL import Image

logger = logging.getLogger("eon.ers.benchmarks.live_stages")


def get_environment_info() -> dict[str, Any]:
    """Capture host system architecture, CPU info, and runtime environment."""
    info: dict[str, Any] = {
        "operating_system": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "python_version": sys.version.split()[0],
    }
    try:
        import psutil

        info["cpu_count_physical"] = psutil.cpu_count(logical=False)
        info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        info["total_ram_gb"] = round(psutil.virtual_memory().total / (1024**3), 2)
    except ImportError:
        pass

    try:
        import onnxruntime as ort

        info["onnxruntime_version"] = ort.__version__
        info["onnxruntime_providers"] = ort.get_available_providers()
    except ImportError:
        pass

    return info


def generate_sample_face_base64() -> str:
    """Generate synthetic 128x128 face JPEG as base64 data URI."""
    img = Image.new("RGB", (128, 128), color=(205, 185, 165))
    arr = np.array(img)
    arr[30:45, 30:50] = (50, 50, 50)  # Left eye
    arr[30:45, 78:98] = (50, 50, 50)  # Right eye
    arr[75:90, 40:88] = (180, 60, 60)  # Mouth
    synth = Image.fromarray(arr)
    buf = io.BytesIO()
    synth.save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def generate_sample_speech_base64() -> str:
    """Generate 1-second 16kHz synthetic sine WAV as base64 data URI."""
    sr = 16000
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    audio = 0.35 * np.sin(2 * np.pi * 160 * t) + 0.15 * np.sin(2 * np.pi * 320 * t)
    audio_int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(audio_int16.tobytes())
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{b64}"


def compute_stage_stats(timings_ms: list[float]) -> dict[str, float]:
    """Calculate descriptive statistics for a sequence of millisecond timings."""
    arr = np.array(timings_ms, dtype=np.float64)
    return {
        "iterations": len(arr),
        "mean_ms": round(float(np.mean(arr)), 3),
        "median_ms": round(float(np.median(arr)), 3),
        "std_ms": round(float(np.std(arr)), 3),
        "min_ms": round(float(np.min(arr)), 3),
        "max_ms": round(float(np.max(arr)), 3),
        "p95_ms": round(float(np.percentile(arr, 95)), 3),
        "p99_ms": round(float(np.percentile(arr, 99)), 3),
    }


async def run_stage_benchmarks(
    iterations: int = 40,
    warmup: int = 5,
    output_path: Path = Path("packages/ers/benchmarks/live_benchmark_results.json"),
) -> dict[str, Any]:
    """Execute fine-grained stage measurements with real perf_counter timing."""
    print("=" * 70)
    print("  OVIC EON — ERS Live Processing Stage-by-Stage Latency Benchmark")
    print("=" * 70)
    print(f"Iterations: {iterations} (after {warmup} warm-up rounds)")

    config = ERSConfig(
        enable_facial=True,
        enable_speech=True,
        enable_multimodal_fusion=True,
        facial_model_path="packages/ers/models/facial_emotion_model.onnx",
        speech_model_path="packages/ers/models/speech_emotion_model.onnx",
    )
    engine = ERSEngine(config)
    await engine.initialize()
    await engine.start()

    session_mgr = LiveSessionManager(engine)
    session_id = "bench-stage-session"
    consent_ref = "bench-stage-consent-token"
    session_mgr.register_session_consent(session_id, consent_ref)

    face_b64 = generate_sample_face_base64()
    audio_b64 = generate_sample_speech_base64()

    # Pre-extract components for component-level benchmarking
    facial_pipeline = engine._facial_pipeline
    speech_pipeline = engine._speech_pipeline
    fusion_pipeline = engine._fusion_pipeline
    tracker = engine.tracker

    assert facial_pipeline is not None
    assert speech_pipeline is not None
    assert fusion_pipeline is not None

    stage_timings: dict[str, list[float]] = {
        "frame_decode": [],
        "face_detect_landmarks": [],
        "facial_inference": [],
        "audio_decode": [],
        "speech_prosody_inference": [],
        "multimodal_fusion": [],
        "temporal_smoothing": [],
        "serialization": [],
        "end_to_end_live_stream": [],
    }

    # Warmup runs
    for _ in range(warmup):
        await session_mgr.process_multimodal_live(
            session_id=session_id,
            image_base64=face_b64,
            audio_base64=audio_b64,
            consent_reference=consent_ref,
        )

    print("\nExecuting live stage measurements...")

    for i in range(iterations):
        # 1. Stage: frame_decode
        t0 = time.perf_counter()
        raw_b64 = face_b64.split(",", 1)[1]
        decoded_bytes = base64.b64decode(raw_b64)
        quality, pil_img = facial_pipeline.quality_evaluator.evaluate(decoded_bytes)
        t1 = time.perf_counter()
        stage_timings["frame_decode"].append((t1 - t0) * 1000.0)

        # 2. Stage: face_detect_landmarks
        t0 = time.perf_counter()
        assert pil_img is not None
        detect_res = facial_pipeline.face_detector.detect(pil_img)
        primary_box = detect_res.primary_face
        if primary_box is not None:
            facial_pipeline.landmark_detector.detect_landmarks(pil_img, primary_box)
        evidence_features = facial_pipeline.feature_extractor.extract_features(pil_img)
        t1 = time.perf_counter()
        stage_timings["face_detect_landmarks"].append((t1 - t0) * 1000.0)

        # 3. Stage: facial_inference
        t0 = time.perf_counter()
        tensor = facial_pipeline.preprocessor.preprocess(pil_img)
        probs = facial_pipeline.model_adapter.predict(tensor, evidence_features)
        t1 = time.perf_counter()
        stage_timings["facial_inference"].append((t1 - t0) * 1000.0)

        # 4. Stage: audio_decode
        t0 = time.perf_counter()
        raw_audio_b64 = audio_b64.split(",", 1)[1]
        decoded_audio_bytes = base64.b64decode(raw_audio_b64)
        audio_quality, audio_arr, sr = speech_pipeline.quality_evaluator.evaluate(
            decoded_audio_bytes
        )
        t1 = time.perf_counter()
        stage_timings["audio_decode"].append((t1 - t0) * 1000.0)

        # 5. Stage: speech_prosody_inference
        t0 = time.perf_counter()
        assert audio_arr is not None
        speech_features = speech_pipeline.feature_extractor.extract_features(audio_arr, sr)
        speech_probs = speech_pipeline.model_adapter.predict(audio_arr, sr, speech_features)
        t1 = time.perf_counter()
        stage_timings["speech_prosody_inference"].append((t1 - t0) * 1000.0)

        # Create observation objects for fusion and smoothing
        now_ts = time.time()
        face_obs = EmotionObservation(
            observation_id=f"bench-face-{i}",
            timestamp=now_ts,
            modality=Modality.FACIAL,
            emotion_probabilities=probs,
            dominant_estimate=max(probs, key=probs.get),  # type: ignore[arg-type]
            confidence=0.85,
            uncertainty=0.15,
            quality_score=0.9,
            model_id="facial_onnx",
            model_version="1.0.0",
            processing_latency_ms=10.0,
            status=ObservationStatus.OK,
            is_definitive_claim=False,
        )
        speech_obs = EmotionObservation(
            observation_id=f"bench-speech-{i}",
            timestamp=now_ts,
            modality=Modality.SPEECH,
            emotion_probabilities=speech_probs,
            dominant_estimate=max(speech_probs, key=speech_probs.get),  # type: ignore[arg-type]
            confidence=0.80,
            uncertainty=0.20,
            quality_score=0.9,
            model_id="speech_onnx",
            model_version="1.0.0",
            processing_latency_ms=10.0,
            status=ObservationStatus.OK,
            is_definitive_claim=False,
        )

        # 6. Stage: multimodal_fusion
        t0 = time.perf_counter()
        fusion_res: FusionResult = fusion_pipeline.fuse(face_obs, speech_obs)
        t1 = time.perf_counter()
        stage_timings["multimodal_fusion"].append((t1 - t0) * 1000.0)

        # 7. Stage: temporal_smoothing
        t0 = time.perf_counter()
        tracker.record_observation(f"{session_id}-{i}", face_obs)
        t1 = time.perf_counter()
        stage_timings["temporal_smoothing"].append((t1 - t0) * 1000.0)

        # 8. Stage: serialization
        t0 = time.perf_counter()
        msg = LiveStreamOutboundMessage(
            type="fusion",
            session_id=session_id,
            timestamp=time.time(),
            modality="multimodal",
            data={
                "dominant_estimate": fusion_res.dominant_estimate,
                "emotion_probabilities": fusion_res.fused_probabilities,
                "confidence": fusion_res.confidence,
                "uncertainty": fusion_res.uncertainty,
                "quality_summary": fusion_res.quality_summary,
                "is_definitive_claim": fusion_res.is_definitive_claim,
            },
            latency_ms=10.0,
        )
        _ = msg.model_dump_json()
        t1 = time.perf_counter()
        stage_timings["serialization"].append((t1 - t0) * 1000.0)

        # 9. Stage: end_to_end_live_stream
        t0 = time.perf_counter()
        await session_mgr.process_multimodal_live(
            session_id=session_id,
            image_base64=face_b64,
            audio_base64=audio_b64,
            consent_reference=consent_ref,
        )
        t1 = time.perf_counter()
        stage_timings["end_to_end_live_stream"].append((t1 - t0) * 1000.0)

    await session_mgr.shutdown()

    results: dict[str, Any] = {
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "environment": get_environment_info(),
        "disclaimer": (
            "LATENCY MEASUREMENTS ONLY: Measures actual hardware execution timings using time.perf_counter(). "
            "These benchmarks use synthetic signal fixtures to evaluate compute performance, "
            "and DO NOT assess or imply affective recognition accuracy."
        ),
        "stages": {},
    }

    print("\nBenchmark Results (in milliseconds):")
    print(f"{'Stage':<26} | {'Mean':>8} | {'Median':>8} | {'P95':>8} | {'Min':>8} | {'Max':>8}")
    print("-" * 75)

    for stage_name, timings in stage_timings.items():
        stats = compute_stage_stats(timings)
        results["stages"][stage_name] = stats
        print(
            f"{stage_name:<26} | "
            f"{stats['mean_ms']:>7.2f}ms | "
            f"{stats['median_ms']:>7.2f}ms | "
            f"{stats['p95_ms']:>7.2f}ms | "
            f"{stats['min_ms']:>7.2f}ms | "
            f"{stats['max_ms']:>7.2f}ms"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("-" * 75)
    print(f"[SUCCESS] Benchmark results saved to: {output_path}")
    return results


def main() -> None:
    """Run stage latency benchmarks."""
    asyncio.run(run_stage_benchmarks())


if __name__ == "__main__":
    main()
