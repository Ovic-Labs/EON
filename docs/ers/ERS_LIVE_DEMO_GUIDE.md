# OVIC EON — ERS Live Sensory Demonstration Guide
## Phase 3.1.2: Real-Time Webcam and Microphone Integration

This guide provides instructions for launching, configuring, and testing the **OVIC EON Emotion Recognition System (ERS)** live sensory demonstration.

The live demonstration runs a self-contained local FastAPI streaming server with an interactive web dashboard. It processes real-time video frames from your webcam and audio streams from your microphone using local CPU-first models.

---

## 1. Quickstart Launch

### Option A: Via Python Executable Script

Run from the root of the repository:

```powershell
python packages/ers/examples/live_demo.py --open-browser
```

### Option B: Via Installed CLI Entrypoint

If `packages/ers` is installed in editable mode (`pip install -e packages/ers[live]`):

```powershell
eon-ers-live --open-browser --port 8000
```

### Server Command-Line Arguments

| Flag | Default | Description |
|---|---|---|
| `--host` | `127.0.0.1` | Network interface address to bind the server. |
| `--port` | `8000` | Port number for the HTTP and WebSocket server. |
| `--open-browser` | `False` | Automatically launches the dashboard in default web browser. |
| `--log-level` | `info` | Uvicorn logging verbosity (`debug`, `info`, `warning`, `error`). |
| `--facial-model` | `packages/ers/models/facial_emotion_model.onnx` | Path to the ONNX facial emotion model. |
| `--speech-model` | `packages/ers/models/speech_emotion_model.onnx` | Path to the ONNX speech emotion model. |

---

## 2. Browser Interface Walkthrough

Open `http://127.0.0.1:8000/` in Chrome, Firefox, Edge, or Safari.

### 2.1 System Header and Invariant Indicators

- **Engine Status**: Displays current engine state (`READY`, `INITIALIZED`).
- **Core Integration**: Explicitly reports `NOT_CONNECTED` (confirming standalone Phase 3.1 boundary isolation from robot control buses).
- **Epistemic Modesty Badge**: Highlights `is_definitive_claim = False`, confirming outputs represent observable behavioral cues rather than certified psychiatric states.
- **Privacy Guarantee**: Affirms zero persistent media storage on disk or server logs.

### 2.2 Privacy Consent Authorization

Live processing is **gated by strict user consent**:
1. Enter or use the generated Consent Reference Token (e.g. `consent-token-live-demo-1`).
2. Click **Authorize & Start Stream**.
3. To exercise immediate revocation at any moment, click **Revoke Consent**. All processing terminates instantaneously, and the server immediately rejects subsequent incoming frames.

### 2.3 Sensor Controls and Permissions

1. Click **Start Webcam & Mic**.
2. When prompted by your browser, grant permissions for:
   - Camera access (used for capturing 128x128 face crops at 2 FPS).
   - Microphone access (used for capturing 16kHz mono PCM chunks at 1000ms intervals).
3. If permissions are denied, the dashboard renders an explicit alert banner with troubleshooting instructions.

### 2.4 Real-Time Analytics and Visualization

The dashboard provides live meters and distribution graphs:
- **Signal Quality**: Live scores for facial contrast/resolution and audio signal-to-noise ratio.
- **Epistemic Uncertainty**: Normalized Shannon entropy and margin uncertainty of current evidence.
- **Dominant Emotion**: Real-time classified expression category (e.g., `neutral`, `happiness`, `surprise`).
- **Emotion Distribution**: Probability bar charts dynamically updating across 7 categories.
- **Acoustic Features**: Live pitch F0 fundamental frequency, RMS energy, and tempo estimations.
- **Multimodal Agreement & Conflict**: Jensen-Shannon divergence indicating agreement between visual and acoustic signals.
- **Latency Timer**: Actual round-trip execution latency in milliseconds.

---

## 3. Architecture & Security Invariants

1. **Zero Raw Media Retention**: Video frames and audio chunks are decoded in volatile RAM, evaluated, and immediately scrubbed (`inp.scrub_media_payload()`). No media files are ever written to disk or recorded in logs.
2. **Epistemic Modesty**: All emotion outputs enforce `is_definitive_claim = False`. EON analyzes external expression cues, not internal psychological ground truth.
3. **Subsystem Isolation**: Live streaming endpoints strictly reject all robot actuator or motion command payloads.

---

## 4. Troubleshooting

### Camera or Microphone Not Starting
- Ensure permissions are allowed in browser settings for `http://127.0.0.1:8000`.
- Verify no other application (e.g., Zoom, Teams) has exclusive locks on the camera.

### Port In Use (8000)
- Specify a different port using `--port 8080`:
  ```powershell
  python packages/ers/examples/live_demo.py --port 8080 --open-browser
  ```

### WebSocket Disconnection
- If the session is disconnected, refresh the page or click **Authorize & Start Stream** to re-establish the WebSocket connection.
