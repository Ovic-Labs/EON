# ERS CPU Performance Benchmarks

**Disclaimer:** These measurements quantify local CPU execution latency and memory RSS using synthetic signal fixtures. They do **not** evaluate affective classification accuracy.

## Host Environment (`task-8402`)
- **Processor:** `Intel64 Family 6 Model 181 Stepping 0, GenuineIntel` (`12` physical / `14` logical cores)
- **OS / Python:** `Windows-10-10.0.26300-SP0` / Python `3.11.9`
- **Providers:** `CPUExecutionProvider` (`onnxruntime 1.32.0`, `num_threads=4`)
- **Peak RSS / Initialization:** `162.15 MB` Peak RSS | `945.01 ms` cold engine init

## Measured Latencies (`benchmark_cpu.py`, 30 warm iterations)

| Pipeline | Cold (ms) | Mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) |
|---|---|---|---|---|---|
| **Facial** | `15.21` | `4.90` | `4.71` | `5.85` | `6.24` |
| **Speech** | `20.36` | `10.87` | `10.32` | `15.76` | `19.34` |
| **Multimodal Fusion** | `28.98` | `21.69` | `21.53` | `25.45` | `27.33` |

## Live Stage Breakdown (`benchmark_live_stages.py`, 40 iterations)

| Stage | Median (ms) | p95 (ms) |
|---|---|---|
| `frame_decode` | `1.13` | `1.82` |
| `face_detect_landmarks` | `1.63` | `2.20` |
| `facial_inference` | `0.40` | `0.59` |
| `audio_decode` | `0.87` | `1.22` |
| `speech_prosody_inference` | `6.60` | `10.43` |
| `multimodal_fusion` | `0.11` | `0.27` |
| `end_to_end_live_stream` | `23.02` | `35.94` |

Reproduce locally:
```bash
python packages/ers/benchmarks/benchmark_cpu.py
python packages/ers/benchmarks/benchmark_live_stages.py
```
