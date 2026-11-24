# ERS Enterprise Dashboard Design Specification

## 1. Overview & Architecture

The ERS Live Input Instrumentation Dashboard (`/`) provides real-time scientific monitoring of edge affective perception pipelines. It is implemented as a single, self-contained HTML/CSS/JS interface embedded in `eon_ers.live.dashboard`.

### Key Design Principles:
- **Minimal, Scientific Aesthetic:** Clean instrumentation interface with high contrast, legible monospaced typography, and zero consumer-grade gimmicks.
- **Strict Privacy Lifecycle:** Explicit stopping and disposal of `MediaStreamTrack` objects to prevent hardware lockouts and unauthorized background streaming.
- **Real-Time Client Telemetry:** Rolling window computation of P50, P95, and P99 roundtrip inference latency.
- **Model Integrity Transparency:** Unvalidated baseline weights are prominently announced with caution banners, preventing users from misinterpreting suppressed classifications.

---

## 2. Design System Tokens & Themes

### 2.1 Color Tokens

```css
/* Dark Theme (Default) */
--bg-base: #090d16;
--bg-surface: #111827;
--bg-surface-elevated: #1f2937;
--border-subtle: #1f293d;
--border-medium: #374151;
--text-main: #f3f4f6;
--text-secondary: #9ca3af;
--text-muted: #6b7280;
--primary: #3b82f6;
--status-success: #10b981;
--status-warning: #f59e0b;
--status-error: #ef4444;

/* Light Theme */
--bg-base: #f8fafc;
--bg-surface: #ffffff;
--bg-surface-elevated: #f1f5f9;
--border-subtle: #e2e8f0;
--border-medium: #cbd5e1;
--text-main: #0f172a;
--text-secondary: #475569;
--text-muted: #94a3b8;
```

### 2.2 Typography
- Body & Labels: `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`
- Numeric & Telemetry: `SF Mono, Segoe UI Mono, Roboto Mono, Menlo, monospace`

---

## 3. UI Components & Layout

The dashboard features a 3-column responsive layout:

```
+-------------------+--------------------------------+--------------------+
| Hardware Inputs   | Perception Center Stage        | Performance & Reg  |
| - Camera Source   | - Video Monitor (16:9)         | - Rolling P50/95/99|
| - Mic Source      | - Dominant Affect State        | - Dropped Frames   |
| - Live VU Meter   | - Calibrated Class Probability | - Model State Audit|
| - Session Config  | - Scientific Audit Log         | - Invariants       |
+-------------------+--------------------------------+--------------------+
```

### 3.1 Hardware Acquisition Panel
- Independent controls for camera and microphone: `Start Camera`, `Stop Camera`, `Start Mic`, `Stop Mic`.
- Calling `stopCamera()` executes `track.stop()` on every `MediaStreamTrack` in `state.videoStream`.
- Dynamic device enumeration via `navigator.mediaDevices.enumerateDevices()`, refreshed automatically on `devicechange` events.

### 3.2 Web Audio API VU Level Meter
- Implemented using `AudioContext`, `MediaStreamAudioSourceNode`, and `AnalyserNode` ($fftSize = 256$).
- Computes real-time RMS audio power:
  $$\text{Power} = \frac{1}{N} \sum_{i=1}^N x_i$$
- Drives a horizontal gradient bar ($0\%$ to $100\%$) indicating input levels from $-60\text{ dB}$ to $0\text{ dB}$.

### 3.3 Latency Instrumentation
- Rolling circular buffer of up to 100 roundtrip latency measurements.
- Calculates P50, P95, and P99 percentiles in JavaScript and displays them live in the telemetry table.

### 3.4 WebSocket Resiliency
- Reconnects automatically using exponential backoff with jitter (initial delay 1.0s, multiplier 1.5, max delay 10s, max 10 attempts).
- In-memory event log displays connection, inference, and error events with millisecond timestamps.
