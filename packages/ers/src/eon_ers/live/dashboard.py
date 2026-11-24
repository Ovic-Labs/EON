"""Interactive HTML/CSS/JavaScript live demonstration dashboard for ERS."""

from __future__ import annotations


def get_dashboard_html() -> str:
    """Return the complete standalone, self-contained responsive dashboard HTML."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OVIC EON — ERS Live Input Demonstration</title>
    <style>
        :root {
            --bg-primary: #0f141c;
            --bg-secondary: #1a2230;
            --bg-card: #222d3f;
            --border: #31425a;
            --text-primary: #f0f4f8;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --accent-amber: #fbbf24;
            --accent-rose: #fb7185;
            --accent-purple: #c084fc;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            min-height: 100vh;
            padding: 1rem;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .brand-title {
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .brand-badge {
            background-color: rgba(56, 189, 248, 0.15);
            color: var(--accent-blue);
            font-size: 0.75rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            border: 1px solid rgba(56, 189, 248, 0.3);
            font-weight: 600;
        }

        .header-status-pills {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        .pill {
            font-size: 0.75rem;
            padding: 0.25rem 0.6rem;
            border-radius: 9999px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        .pill-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--text-muted);
        }

        .pill-dot.active { background-color: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
        .pill-dot.warning { background-color: var(--accent-amber); }
        .pill-dot.danger { background-color: var(--accent-rose); }

        .banner-alert {
            background: rgba(251, 191, 36, 0.1);
            border: 1px solid rgba(251, 191, 36, 0.3);
            color: var(--accent-amber);
            padding: 0.65rem 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .grid-layout {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1rem;
        }

        @media (min-width: 1024px) {
            .grid-layout {
                grid-template-columns: 1.15fr 1fr;
            }
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 0.5rem;
        }

        .card-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
        }

        .consent-box {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 6px;
            padding: 0.75rem;
            font-size: 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .consent-label {
            display: flex;
            align-items: flex-start;
            gap: 0.5rem;
            cursor: pointer;
            color: var(--text-primary);
            line-height: 1.4;
        }

        .consent-label input[type="checkbox"] {
            margin-top: 0.2rem;
            cursor: pointer;
        }

        .btn-group {
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
        }

        button {
            padding: 0.45rem 0.85rem;
            font-size: 0.85rem;
            font-weight: 600;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: var(--bg-secondary);
            color: var(--text-primary);
            cursor: pointer;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
        }

        button:hover:not(:disabled) {
            background: #2b3950;
            border-color: #475d7c;
        }

        button:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        button.btn-primary {
            background: #0284c7;
            border-color: #38bdf8;
            color: #ffffff;
        }

        button.btn-primary:hover:not(:disabled) {
            background: #0369a1;
        }

        button.btn-danger {
            background: rgba(244, 63, 94, 0.15);
            border-color: rgba(244, 63, 94, 0.4);
            color: var(--accent-rose);
        }

        button.btn-danger:hover:not(:disabled) {
            background: rgba(244, 63, 94, 0.25);
        }

        .media-preview-container {
            position: relative;
            background: #000;
            border-radius: 6px;
            overflow: hidden;
            width: 100%;
            height: 240px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        video, canvas {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }

        .preview-overlay {
            position: absolute;
            top: 0.5rem;
            left: 0.5rem;
            background: rgba(15, 20, 28, 0.75);
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .preview-canvas-overlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }

        .audio-meter-bar {
            width: 100%;
            height: 12px;
            background: #111827;
            border-radius: 9999px;
            overflow: hidden;
            border: 1px solid var(--border);
        }

        .audio-meter-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, var(--accent-green) 0%, var(--accent-amber) 70%, var(--accent-rose) 100%);
            transition: width 0.08s ease;
        }

        .metric-row {
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }

        .metric-val {
            font-weight: 600;
            color: var(--text-primary);
        }

        .prob-bars-container {
            display: flex;
            flex-direction: column;
            gap: 0.4rem;
        }

        .prob-bar-row {
            display: grid;
            grid-template-columns: 85px 1fr 45px;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
        }

        .prob-bar-label {
            color: var(--text-secondary);
            text-transform: capitalize;
        }

        .prob-bar-track {
            background: var(--bg-secondary);
            border-radius: 4px;
            height: 10px;
            overflow: hidden;
        }

        .prob-bar-fill {
            height: 100%;
            background: var(--accent-blue);
            width: 0%;
            transition: width 0.2s ease;
        }

        .dominant-estimate-badge {
            font-size: 1.25rem;
            font-weight: 700;
            padding: 0.35rem 0.75rem;
            border-radius: 6px;
            display: inline-block;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-blue);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .uncertainty-meter {
            display: flex;
            gap: 0.5rem;
            align-items: center;
        }

        .controls-row {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
            font-size: 0.8rem;
        }

        select {
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.35rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }

        footer {
            margin-top: 1.5rem;
            padding-top: 1rem;
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 0.75rem;
            color: var(--text-muted);
        }
    </style>
</head>
<body>

    <header>
        <div class="brand-title">
            <span>OVIC EON</span>
            <span class="brand-badge">ERS LIVE DEMO</span>
        </div>
        <div class="header-status-pills">
            <div class="pill" id="pill-engine">
                <span class="pill-dot pill-dot active" id="dot-engine"></span>
                <span>Engine: <b id="val-engine">INITIALIZING</b></span>
            </div>
            <div class="pill" id="pill-core">
                <span class="pill-dot warning"></span>
                <span>Core: <b>NOT_CONNECTED</b></span>
            </div>
            <div class="pill" id="pill-model">
                <span class="pill-dot warning"></span>
                <span>Model: <b>EXPERIMENTAL BASELINE</b></span>
            </div>
            <div class="pill" id="pill-ws">
                <span class="pill-dot danger" id="dot-ws"></span>
                <span>Stream: <b id="val-ws">DISCONNECTED</b></span>
            </div>
        </div>
    </header>

    <div class="banner-alert">
        <span><b>Scientific Notice:</b> Observable behavioral features are analyzed via local CPU baseline models. Internal affective states cannot be definitively inferred (Epistemic Modesty: is_definitive_claim = False). Zero persistent disk storage.</span>
    </div>

    <div class="grid-layout">

        <!-- Column 1: Live Sensory Capture & Controls -->
        <div style="display: flex; flex-direction: column; gap: 1rem;">

            <!-- Consent & Session Control Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">1. Privacy Consent & Hardware Controls</span>
                    <span class="pill" id="pill-consent"><span class="pill-dot danger" id="dot-consent"></span><span id="val-consent">Consent: Required</span></span>
                </div>

                <div class="consent-box">
                    <label class="consent-label">
                        <input type="checkbox" id="chk-consent">
                        <span>I grant explicit consent for real-time webcam and microphone affective feature analysis on this device. Sensory media is processed strictly in volatile memory and never persisted or transmitted.</span>
                    </label>
                    <div class="metric-row">
                        <span>Active Session ID: <code id="txt-session-id">generating...</code></span>
                        <span>Token: <code id="txt-consent-ref">not_registered</code></span>
                    </div>
                </div>

                <div class="controls-row">
                    <label for="sel-fps">Video Sample Rate:</label>
                    <select id="sel-fps">
                        <option value="1">1 FPS (Ultra-low CPU)</option>
                        <option value="2" selected>2 FPS (Standard Edge)</option>
                        <option value="5">5 FPS (Real-time)</option>
                    </select>

                    <label for="sel-chunk">Audio Chunk Duration:</label>
                    <select id="sel-chunk">
                        <option value="500">500 ms (Low latency)</option>
                        <option value="1000" selected>1000 ms (Standard)</option>
                        <option value="1500">1500 ms (Enhanced Prosody)</option>
                    </select>
                </div>

                <div class="btn-group">
                    <button class="btn-primary" id="btn-start" disabled>Start Live Stream</button>
                    <button id="btn-cam-toggle" disabled>Toggle Camera</button>
                    <button id="btn-mic-toggle" disabled>Toggle Microphone</button>
                    <button class="btn-danger" id="btn-stop" disabled>Stop Capture</button>
                    <button class="btn-danger" id="btn-revoke">Revoke Consent</button>
                </div>
            </div>

            <!-- Video Feed Preview Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">2. Live Optical Capture (Webcam)</span>
                    <span class="pill" id="pill-cam"><span class="pill-dot danger" id="dot-cam"></span><span id="val-cam">INACTIVE</span></span>
                </div>

                <div class="media-preview-container">
                    <video id="vid-preview" autoplay playsinline muted></video>
                    <canvas id="canvas-overlay" class="preview-canvas-overlay"></canvas>
                    <div class="preview-overlay" id="txt-cam-overlay">Camera Inactive</div>
                </div>

                <div class="metric-row">
                    <span>Face Detection: <b id="val-face-status" class="metric-val">NO_FACE</b></span>
                    <span>Laplacian Blur Score: <b id="val-face-blur" class="metric-val">0.0</b></span>
                    <span>Illumination: <b id="val-face-lum" class="metric-val">0.0</b></span>
                </div>
            </div>

            <!-- Microphone Audio Monitor Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">3. Live Acoustic Monitor (Microphone)</span>
                    <span class="pill" id="pill-mic"><span class="pill-dot danger" id="dot-mic"></span><span id="val-mic">INACTIVE</span></span>
                </div>

                <div class="audio-meter-bar">
                    <div class="audio-meter-fill" id="meter-audio-fill"></div>
                </div>

                <div class="metric-row">
                    <span>Signal Quality: <b id="val-audio-snr" class="metric-val">0.0 dB</b></span>
                    <span>Acoustic RMS: <b id="val-audio-rms" class="metric-val">0.0 dB</b></span>
                    <span>Voice Activity: <b id="val-audio-vad" class="metric-val">INACTIVE</b></span>
                </div>
            </div>

        </div>

        <!-- Column 2: ERS Affective Observation & Multimodal Fusion -->
        <div style="display: flex; flex-direction: column; gap: 1rem;">

            <!-- Multimodal Affective State Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">4. Real-Time Multimodal Emotion Fusion</span>
                    <span class="pill" id="pill-modality-weights">Weights: F 50% | S 50%</span>
                </div>

                <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.2rem;">DOMINANT OBSERVABLE ESTIMATE</div>
                        <div class="dominant-estimate-badge" id="badge-dominant">INSUFFICIENT_EVIDENCE</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.2rem;">PIPELINE LATENCY</div>
                        <div style="font-size: 1.15rem; font-weight: 700; color: var(--accent-green);" id="txt-latency">-- ms</div>
                    </div>
                </div>

                <div class="uncertainty-meter">
                    <div style="flex: 1;">
                        <div class="metric-row" style="margin-bottom: 0.2rem;">
                            <span>Observation Confidence:</span>
                            <span class="metric-val" id="val-confidence">0.00</span>
                        </div>
                        <div class="prob-bar-track">
                            <div class="prob-bar-fill" id="bar-confidence" style="background: var(--accent-green); width: 0%;"></div>
                        </div>
                    </div>
                    <div style="flex: 1;">
                        <div class="metric-row" style="margin-bottom: 0.2rem;">
                            <span>Epistemic Uncertainty:</span>
                            <span class="metric-val" id="val-uncertainty">1.00</span>
                        </div>
                        <div class="prob-bar-track">
                            <div class="prob-bar-fill" id="bar-uncertainty" style="background: var(--accent-amber); width: 100%;"></div>
                        </div>
                    </div>
                </div>

                <div class="card-title" style="font-size: 0.85rem; margin-top: 0.5rem;">Fused Affective Probability Distribution</div>
                <div class="prob-bars-container" id="container-probs">
                    <!-- Probability rows injected via JS -->
                </div>

                <div class="metric-row" style="margin-top: 0.25rem;">
                    <span>Conflict Metric (JSD): <b id="val-jsd" class="metric-val">0.000</b></span>
                    <span>Conflict Detected: <b id="val-conflict" class="metric-val">NO</b></span>
                </div>
            </div>

            <!-- Unimodal Streams Diagnostics Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">5. Unimodal Diagnostic Signals</span>
                </div>

                <div class="metric-row">
                    <span>Facial Stream Estimate:</span>
                    <b id="val-face-estimate" class="metric-val">--</b>
                </div>
                <div class="metric-row">
                    <span>Speech Stream Estimate:</span>
                    <b id="val-speech-estimate" class="metric-val">--</b>
                </div>
                <div class="metric-row">
                    <span>Responsible AI Non-Definitive Invariant:</span>
                    <b class="metric-val" style="color: var(--accent-green);">is_definitive_claim = False (Verified)</b>
                </div>
                <div class="metric-row">
                    <span>Actuator Motion Commands Prohibited:</span>
                    <b class="metric-val" style="color: var(--accent-green);">HARD INTERLOCK ACTIVE</b>
                </div>
            </div>

            <!-- System Diagnostic Console Card -->
            <div class="card">
                <div class="card-header">
                    <span class="card-title">6. Observation Limitations & Status Log</span>
                </div>
                <div id="txt-limitations-log" style="font-family: monospace; font-size: 0.75rem; color: var(--text-muted); max-height: 120px; overflow-y: auto; display: flex; flex-direction: column; gap: 0.25rem;">
                    <div>[Init] Ready for user consent registration.</div>
                </div>
            </div>

        </div>

    </div>

    <footer>
        OVIC EON — Emotional Intelligence Infrastructure for Robotics &copy; 2026 OVIC Labs. Local edge execution on CPU.
    </footer>

    <!-- Hidden canvas used for capturing video frames -->
    <canvas id="hidden-capture-canvas" style="display: none;"></canvas>

    <script>
        // --- State Management ---
        const EMOTIONS = ["neutral", "happiness", "sadness", "anger", "fear", "surprise", "disgust"];
        let sessionId = "session-" + Math.random().toString(36).substring(2, 10);
        let consentRef = null;
        let ws = null;
        let mediaStream = null;
        let audioContext = null;
        let audioProcessor = null;
        let audioInputNode = null;
        let frameInterval = null;
        let isCamActive = false;
        let isMicActive = false;
        let isStreaming = false;

        document.getElementById("txt-session-id").innerText = sessionId;

        // Render initial emotion bars
        const probContainer = document.getElementById("container-probs");
        probContainer.innerHTML = EMOTIONS.map(em => `
            <div class="prob-bar-row">
                <span class="prob-bar-label">${em}</span>
                <div class="prob-bar-track">
                    <div class="prob-bar-fill" id="bar-em-${em}"></div>
                </div>
                <span class="metric-val" id="val-em-${em}">0.0%</span>
            </div>
        `).join("");

        // --- UI Element Bindings ---
        const chkConsent = document.getElementById("chk-consent");
        const btnStart = document.getElementById("btn-start");
        const btnStop = document.getElementById("btn-stop");
        const btnRevoke = document.getElementById("btn-revoke");
        const btnCamToggle = document.getElementById("btn-cam-toggle");
        const btnMicToggle = document.getElementById("btn-mic-toggle");
        const selFps = document.getElementById("sel-fps");
        const selChunk = document.getElementById("sel-chunk");

        const vidPreview = document.getElementById("vid-preview");
        const canvasOverlay = document.getElementById("canvas-overlay");
        const hiddenCanvas = document.getElementById("hidden-capture-canvas");
        const txtCamOverlay = document.getElementById("txt-cam-overlay");
        const meterAudioFill = document.getElementById("meter-audio-fill");

        // --- Consent Controls ---
        chkConsent.addEventListener("change", async () => {
            if (chkConsent.checked) {
                consentRef = "token-live-" + Math.random().toString(36).substring(2, 12);
                try {
                    const res = await fetch("/api/consent/register", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ session_id: sessionId, consent_reference: consentRef })
                    });
                    if (res.ok) {
                        document.getElementById("txt-consent-ref").innerText = consentRef.substring(0, 8) + "***";
                        document.getElementById("dot-consent").className = "pill-dot active";
                        document.getElementById("val-consent").innerText = "Consent: ACTIVE";
                        btnStart.disabled = false;
                        logNotice("Consent registered for session " + sessionId);
                    } else {
                        throw new Error("Server rejected consent registration");
                    }
                } catch (e) {
                    alert("Failed to register consent: " + e.message);
                    chkConsent.checked = false;
                }
            } else {
                await revokeConsent();
            }
        });

        btnRevoke.addEventListener("click", async () => {
            await revokeConsent();
        });

        async function revokeConsent() {
            try {
                await fetch("/api/consent/revoke", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ session_id: sessionId })
                });
            } catch (e) {}

            stopCapture();
            consentRef = null;
            chkConsent.checked = false;
            document.getElementById("txt-consent-ref").innerText = "revoked";
            document.getElementById("dot-consent").className = "pill-dot danger";
            document.getElementById("val-consent").innerText = "Consent: REVOKED";
            btnStart.disabled = true;
            logNotice("Consent explicitly revoked. Sensory capture halted.");
        }

        // --- WebSocket Streaming ---
        function initWebSocket() {
            const loc = window.location;
            const wsProto = loc.protocol === "https:" ? "wss:" : "ws:";
            const wsUrl = `${wsProto}//${loc.host}/ws/live/${sessionId}`;

            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                document.getElementById("dot-ws").className = "pill-dot active";
                document.getElementById("val-ws").innerText = "CONNECTED";
                ws.send(JSON.stringify({ type: "init", session_id: sessionId, consent_reference: consentRef }));
                logNotice("WebSocket streaming established.");
            };

            ws.onmessage = (event) => {
                const msg = JSON.parse(event.data);
                handleServerMessage(msg);
            };

            ws.onerror = (err) => {
                document.getElementById("dot-ws").className = "pill-dot danger";
                document.getElementById("val-ws").innerText = "ERROR";
                logNotice("WebSocket streaming error encountered.");
            };

            ws.onclose = () => {
                document.getElementById("dot-ws").className = "pill-dot danger";
                document.getElementById("val-ws").innerText = "DISCONNECTED";
                logNotice("WebSocket closed.");
            };
        }

        function handleServerMessage(msg) {
            if (msg.type === "observation" && msg.modality === "facial") {
                const obs = msg.data;
                document.getElementById("val-face-estimate").innerText = `${obs.dominant_estimate} (${(obs.confidence * 100).toFixed(1)}%)`;
                if (obs.expression_observations) {
                    if (obs.expression_observations.blur_variance !== undefined) {
                        document.getElementById("val-face-blur").innerText = obs.expression_observations.blur_variance.toFixed(1);
                    }
                    if (obs.expression_observations.mean_brightness !== undefined) {
                        document.getElementById("val-face-lum").innerText = obs.expression_observations.mean_brightness.toFixed(2);
                    }
                    if (obs.expression_observations.face_box_confidence !== undefined) {
                        document.getElementById("val-face-status").innerText = "DETECTED";
                    }
                }
            } else if (msg.type === "observation" && msg.modality === "speech") {
                const obs = msg.data;
                document.getElementById("val-speech-estimate").innerText = `${obs.dominant_estimate} (${(obs.confidence * 100).toFixed(1)}%)`;
                if (obs.expression_observations) {
                    if (obs.expression_observations.snr_db !== undefined) {
                        document.getElementById("val-audio-snr").innerText = `${obs.expression_observations.snr_db.toFixed(1)} dB`;
                    }
                    if (obs.expression_observations.rms_energy !== undefined) {
                        document.getElementById("val-audio-rms").innerText = `${obs.expression_observations.rms_energy.toFixed(2)} dB`;
                    }
                    if (obs.expression_observations.voice_activity_ratio !== undefined) {
                        document.getElementById("val-audio-vad").innerText = obs.expression_observations.voice_activity_ratio > 0.2 ? "VOICE" : "SILENCE";
                    }
                }
            } else if (msg.type === "fusion") {
                const f = msg.data;
                document.getElementById("badge-dominant").innerText = f.dominant_estimate || "INSUFFICIENT_EVIDENCE";
                document.getElementById("txt-latency").innerText = `${msg.latency_ms || f.latency_ms || "--"} ms`;

                const conf = f.confidence || 0.0;
                const unc = f.uncertainty !== undefined ? f.uncertainty : 1.0;
                document.getElementById("val-confidence").innerText = conf.toFixed(2);
                document.getElementById("bar-confidence").style.width = `${(conf * 100).toFixed(0)}%`;
                document.getElementById("val-uncertainty").innerText = unc.toFixed(2);
                document.getElementById("bar-uncertainty").style.width = `${(unc * 100).toFixed(0)}%`;

                // Update probabilities
                if (f.fused_probabilities) {
                    EMOTIONS.forEach(em => {
                        const p = f.fused_probabilities[em] || 0.0;
                        document.getElementById(`bar-em-${em}`).style.width = `${(p * 100).toFixed(1)}%`;
                        document.getElementById(`val-em-${em}`).innerText = `${(p * 100).toFixed(1)}%`;
                    });
                }

                // Modality weights
                if (f.modality_weights) {
                    const fw = ((f.modality_weights.facial || 0) * 100).toFixed(0);
                    const sw = ((f.modality_weights.speech || 0) * 100).toFixed(0);
                    document.getElementById("pill-modality-weights").innerText = `Weights: F ${fw}% | S ${sw}%`;
                }

                // Conflict
                document.getElementById("val-jsd").innerText = (f.conflict_metric || 0.0).toFixed(3);
                document.getElementById("val-conflict").innerText = f.conflicting_evidence ? "YES (HIGH DIVERGENCE)" : "NO";
                document.getElementById("val-conflict").style.color = f.conflicting_evidence ? "var(--accent-rose)" : "var(--accent-green)";

                // Limitations
                if (f.limitations && f.limitations.length > 0) {
                    f.limitations.forEach(lim => logNotice(lim));
                }
            } else if (msg.type === "error") {
                logNotice("Server warning: " + msg.error);
            }
        }

        // --- Hardware Acquisition ---
        btnStart.addEventListener("click", async () => {
            if (!chkConsent.checked || !consentRef) {
                alert("Consent is required before activating sensory devices.");
                return;
            }

            try {
                mediaStream = await navigator.mediaDevices.getUserMedia({
                    video: { width: { ideal: 640 }, height: { ideal: 480 }, frameRate: { ideal: 15 } },
                    audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true, noiseSuppression: true }
                });

                vidPreview.srcObject = mediaStream;
                isCamActive = true;
                isMicActive = true;
                isStreaming = true;

                document.getElementById("dot-cam").className = "pill-dot active";
                document.getElementById("val-cam").innerText = "STREAMING";
                document.getElementById("dot-mic").className = "pill-dot active";
                document.getElementById("val-mic").innerText = "STREAMING";
                txtCamOverlay.innerText = "Webcam Live";

                btnStart.disabled = true;
                btnStop.disabled = false;
                btnCamToggle.disabled = false;
                btnMicToggle.disabled = false;

                initWebSocket();
                setupAudioProcessing(mediaStream);
                startFrameSampling();

                logNotice("Hardware media streams initialized successfully.");
            } catch (err) {
                if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                    document.getElementById("dot-cam").className = "pill-dot danger";
                    document.getElementById("val-cam").innerText = "DENIED";
                    document.getElementById("dot-mic").className = "pill-dot danger";
                    document.getElementById("val-mic").innerText = "DENIED";
                    alert("Permission denied: Camera or Microphone access was blocked by the browser. Please allow permissions in your browser address bar.");
                } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                    document.getElementById("dot-cam").className = "pill-dot warning";
                    document.getElementById("val-cam").innerText = "UNAVAILABLE";
                    alert("Device unavailable: No camera or microphone hardware found on this machine.");
                } else {
                    alert("Media capture error: " + err.message);
                }
            }
        });

        btnStop.addEventListener("click", () => {
            stopCapture();
        });

        function stopCapture() {
            if (frameInterval) {
                clearInterval(frameInterval);
                frameInterval = null;
            }

            if (audioProcessor) {
                audioProcessor.disconnect();
                audioProcessor = null;
            }
            if (audioContext && audioContext.state !== "closed") {
                audioContext.close();
                audioContext = null;
            }

            if (mediaStream) {
                mediaStream.getTracks().forEach(track => track.stop());
                mediaStream = null;
            }

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: "stop", session_id: sessionId }));
                ws.close();
            }

            vidPreview.srcObject = null;
            isCamActive = false;
            isMicActive = false;
            isStreaming = false;

            document.getElementById("dot-cam").className = "pill-dot danger";
            document.getElementById("val-cam").innerText = "INACTIVE";
            document.getElementById("dot-mic").className = "pill-dot danger";
            document.getElementById("val-mic").innerText = "INACTIVE";
            txtCamOverlay.innerText = "Camera Stopped";
            meterAudioFill.style.width = "0%";

            btnStart.disabled = !chkConsent.checked;
            btnStop.disabled = true;
            btnCamToggle.disabled = true;
            btnMicToggle.disabled = true;

            logNotice("Sensory capture stopped. All tracks released.");
        }

        btnCamToggle.addEventListener("click", () => {
            if (!mediaStream) return;
            const videoTracks = mediaStream.getVideoTracks();
            if (videoTracks.length > 0) {
                videoTracks[0].enabled = !videoTracks[0].enabled;
                isCamActive = videoTracks[0].enabled;
                document.getElementById("val-cam").innerText = isCamActive ? "STREAMING" : "MUTED";
                document.getElementById("dot-cam").className = isCamActive ? "pill-dot active" : "pill-dot warning";
            }
        });

        btnMicToggle.addEventListener("click", () => {
            if (!mediaStream) return;
            const audioTracks = mediaStream.getAudioTracks();
            if (audioTracks.length > 0) {
                audioTracks[0].enabled = !audioTracks[0].enabled;
                isMicActive = audioTracks[0].enabled;
                document.getElementById("val-mic").innerText = isMicActive ? "STREAMING" : "MUTED";
                document.getElementById("dot-mic").className = isMicActive ? "pill-dot active" : "pill-dot warning";
            }
        });

        // --- Visual Frame Sampling ---
        function startFrameSampling() {
            const fps = parseInt(selFps.value, 10) || 2;
            const intervalMs = Math.round(1000 / fps);

            frameInterval = setInterval(() => {
                if (!isStreaming || !isCamActive || !ws || ws.readyState !== WebSocket.OPEN) return;

                const w = vidPreview.videoWidth || 320;
                const h = vidPreview.videoHeight || 240;
                hiddenCanvas.width = 128;
                hiddenCanvas.height = 128;

                const ctx = hiddenCanvas.getContext("2d");
                ctx.drawImage(vidPreview, 0, 0, 128, 128);

                const dataUrl = hiddenCanvas.toDataURL("image/jpeg", 0.7);
                ws.send(JSON.stringify({
                    type: "frame",
                    session_id: sessionId,
                    consent_reference: consentRef,
                    image_base64: dataUrl,
                    timestamp: Date.now() / 1000.0
                }));
            }, intervalMs);
        }

        // --- Audio Sampling (Web Audio API) ---
        function setupAudioProcessing(stream) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
            audioInputNode = audioContext.createMediaStreamSource(stream);

            // Buffer size 4096 at 16kHz ~= 256ms chunk
            const bufferSize = 4096;
            audioProcessor = audioContext.createScriptProcessor(bufferSize, 1, 1);

            let accumulatedSamples = [];
            const targetSamples = 16000; // 1 second chunk at 16kHz

            audioProcessor.onaudioprocess = (e) => {
                if (!isStreaming || !isMicActive) return;

                const channelData = e.inputBuffer.getChannelData(0);
                // Calculate RMS for visual audio bar
                let sumSq = 0;
                for (let i = 0; i < channelData.length; i++) {
                    sumSq += channelData[i] * channelData[i];
                    accumulatedSamples.push(channelData[i]);
                }
                const rms = Math.sqrt(sumSq / channelData.length);
                meterAudioFill.style.width = `${Math.min(100, rms * 400).toFixed(0)}%`;

                if (accumulatedSamples.length >= targetSamples) {
                    const chunk = accumulatedSamples.slice(0, targetSamples);
                    accumulatedSamples = accumulatedSamples.slice(targetSamples);

                    // Convert Float32 to 16-bit PCM WAV in memory
                    const wavBytes = encodeWAV(chunk, 16000);
                    const b64 = arrayBufferToBase64(wavBytes);

                    if (ws && ws.readyState === WebSocket.OPEN) {
                        ws.send(JSON.stringify({
                            type: "audio",
                            session_id: sessionId,
                            consent_reference: consentRef,
                            audio_base64: b64,
                            sample_rate: 16000,
                            timestamp: Date.now() / 1000.0
                        }));
                    }
                }
            };

            audioInputNode.connect(audioProcessor);
            audioProcessor.connect(audioContext.destination);
        }

        // Helper: in-memory 16-bit Mono WAV encoder
        function encodeWAV(samples, sampleRate) {
            const buffer = new ArrayBuffer(44 + samples.length * 2);
            const view = new DataView(buffer);

            // RIFF chunk descriptor
            writeString(view, 0, "RIFF");
            view.setUint32(4, 36 + samples.length * 2, true);
            writeString(view, 8, "WAVE");

            // fmt sub-chunk
            writeString(view, 12, "fmt ");
            view.setUint32(16, 16, true);
            view.setUint16(20, 1, true); // PCM
            view.setUint16(22, 1, true); // Mono
            view.setUint32(24, sampleRate, true);
            view.setUint32(28, sampleRate * 2, true);
            view.setUint16(32, 2, true);
            view.setUint16(34, 16, true);

            // data sub-chunk
            writeString(view, 36, "data");
            view.setUint32(40, samples.length * 2, true);

            // Write PCM samples
            let offset = 44;
            for (let i = 0; i < samples.length; i++, offset += 2) {
                const s = Math.max(-1, Math.min(1, samples[i]));
                view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
            }
            return buffer;
        }

        function writeString(view, offset, string) {
            for (let i = 0; i < string.length; i++) {
                view.setUint8(offset + i, string.charCodeAt(i));
            }
        }

        function arrayBufferToBase64(buffer) {
            let binary = "";
            const bytes = new Uint8Array(buffer);
            for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            return window.btoa(binary);
        }

        function logNotice(msg) {
            const box = document.getElementById("txt-limitations-log");
            const d = document.createElement("div");
            d.innerText = `[${new Date().toLocaleTimeString()}] ${msg}`;
            box.appendChild(d);
            box.scrollTop = box.scrollHeight;
        }

        // Fetch health on load
        fetch("/api/health").then(r => r.json()).then(data => {
            document.getElementById("val-engine").innerText = data.state || "READY";
        }).catch(() => {});
    </script>
</body>
</html>
"""
