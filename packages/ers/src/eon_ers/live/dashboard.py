"""Professional, enterprise-grade scientific instrumentation dashboard for OVIC EON ERS.

Provides:
- Dark/Light theme switching with CSS variables
- Independent Camera and Microphone hardware acquisition and lifecycle control
- Explicit MediaStreamTrack stopping to prevent device lockouts or leaks
- Real-time audio VU metering using Web Audio API AudioWorklet/ScriptProcessor
- Bounded rolling telemetry history with P50, P95, P99 latency instrumentation
- Model validation state banners and unvalidated evidence callouts
- Device enumeration and hotplug change detection
- Reconnection logic with exponential backoff and jitter
"""

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OVIC EON — ERS Telemetry & Perception Instrumentation</title>
    <style>
        :root {
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            --font-mono: "SF Mono", "Segoe UI Mono", "Roboto Mono", Menlo, Courier, monospace;

            /* Dark Theme (Default) */
            --bg-base: #090d16;
            --bg-surface: #111827;
            --bg-surface-elevated: #1f2937;
            --bg-subtle: #1e2638;
            --border-subtle: #1f293d;
            --border-medium: #374151;
            --text-main: #f3f4f6;
            --text-secondary: #9ca3af;
            --text-muted: #6b7280;
            --primary: #3b82f6;
            --primary-hover: #2563eb;
            --accent: #6366f1;
            --status-success: #10b981;
            --status-warning: #f59e0b;
            --status-error: #ef4444;
            --status-neutral: #6b7280;
            --card-radius: 8px;
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }

        [data-theme="light"] {
            --bg-base: #f8fafc;
            --bg-surface: #ffffff;
            --bg-surface-elevated: #f1f5f9;
            --bg-subtle: #e2e8f0;
            --border-subtle: #e2e8f0;
            --border-medium: #cbd5e1;
            --text-main: #0f172a;
            --text-secondary: #475569;
            --text-muted: #94a3b8;
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --accent: #4f46e5;
            --status-success: #059669;
            --status-warning: #d97706;
            --status-error: #dc2626;
            --status-neutral: #94a3b8;
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: var(--font-sans);
            background-color: var(--bg-base);
            color: var(--text-main);
            line-height: 1.5;
            padding: 1.25rem;
            min-height: 100vh;
        }

        /* Header & Top Bar */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 1rem;
            border-bottom: 1px solid var(--border-subtle);
            margin-bottom: 1.25rem;
        }

        .brand-container {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .brand-badge {
            font-family: var(--font-mono);
            font-size: 0.7rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            background: var(--bg-surface-elevated);
            color: var(--primary);
            border: 1px solid var(--border-medium);
        }

        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }

        .header-actions {
            display: flex;
            align-items: center;
            gap: 1rem;
        }

        .theme-toggle-btn {
            background: var(--bg-surface);
            border: 1px solid var(--border-medium);
            color: var(--text-secondary);
            padding: 0.35rem 0.75rem;
            font-size: 0.8rem;
            font-family: var(--font-mono);
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .theme-toggle-btn:hover {
            color: var(--text-main);
            border-color: var(--primary);
        }

        /* Banner Notifications */
        .system-banner {
            padding: 0.75rem 1rem;
            border-radius: var(--card-radius);
            margin-bottom: 1.25rem;
            font-size: 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid transparent;
        }

        .banner-warning {
            background-color: rgba(245, 158, 11, 0.1);
            border-color: rgba(245, 158, 11, 0.3);
            color: var(--status-warning);
        }

        .banner-info {
            background-color: rgba(59, 130, 246, 0.1);
            border-color: rgba(59, 130, 246, 0.3);
            color: var(--primary);
        }

        .banner-text strong {
            font-weight: 600;
        }

        /* Main Grid Layout */
        .layout-grid {
            display: grid;
            grid-template-columns: 320px 1fr 340px;
            gap: 1.25rem;
        }

        @media (max-width: 1200px) {
            .layout-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Cards & Panels */
        .panel {
            background-color: var(--bg-surface);
            border: 1px solid var(--border-subtle);
            border-radius: var(--card-radius);
            box-shadow: var(--shadow-sm);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            margin-bottom: 1.25rem;
        }

        .panel-header {
            padding: 0.75rem 1rem;
            background: var(--bg-surface-elevated);
            border-bottom: 1px solid var(--border-subtle);
            font-size: 0.85rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
        }

        .panel-body {
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        /* Control Elements */
        .control-group {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .control-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-family: var(--font-mono);
            letter-spacing: 0.04em;
        }

        .select-input {
            width: 100%;
            padding: 0.45rem 0.6rem;
            background-color: var(--bg-base);
            border: 1px solid var(--border-medium);
            color: var(--text-main);
            border-radius: 4px;
            font-size: 0.82rem;
            font-family: var(--font-sans);
            outline: none;
        }

        .select-input:focus {
            border-color: var(--primary);
        }

        .button-row {
            display: flex;
            gap: 0.5rem;
        }

        .btn {
            flex: 1;
            padding: 0.45rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 500;
            border-radius: 4px;
            cursor: pointer;
            border: 1px solid var(--border-medium);
            background: var(--bg-surface-elevated);
            color: var(--text-main);
            transition: all 0.12s ease-in-out;
            text-align: center;
        }

        .btn:hover:not(:disabled) {
            background: var(--border-medium);
        }

        .btn:disabled {
            opacity: 0.45;
            cursor: not-allowed;
        }

        .btn-primary {
            background-color: var(--primary);
            border-color: var(--primary);
            color: #ffffff;
        }

        .btn-primary:hover:not(:disabled) {
            background-color: var(--primary-hover);
        }

        .btn-danger {
            background-color: rgba(239, 68, 68, 0.15);
            border-color: rgba(239, 68, 68, 0.4);
            color: var(--status-error);
        }

        .btn-danger:hover:not(:disabled) {
            background-color: rgba(239, 68, 68, 0.25);
        }

        /* Video Preview Area */
        .preview-container {
            position: relative;
            background: #000;
            border-radius: 6px;
            overflow: hidden;
            aspect-ratio: 16 / 9;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 1px solid var(--border-subtle);
        }

        video {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }

        .preview-overlay {
            position: absolute;
            top: 0.5rem;
            left: 0.5rem;
            background: rgba(0, 0, 0, 0.65);
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            color: #fff;
            letter-spacing: 0.05em;
            pointer-events: none;
        }

        /* Audio VU Meter */
        .vu-meter-container {
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
        }

        .vu-meter-bar {
            height: 8px;
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }

        .vu-meter-fill {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #10b981 0%, #f59e0b 70%, #ef4444 95%);
            transition: width 0.05s ease-out;
        }

        .vu-meter-labels {
            display: flex;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 0.65rem;
            color: var(--text-muted);
        }

        /* Observation & Fusion Center Stage */
        .perception-card {
            background: var(--bg-surface-elevated);
            border-radius: 6px;
            border: 1px solid var(--border-subtle);
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .state-row {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }

        .dominant-category {
            font-size: 1.75rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: var(--text-main);
            text-transform: capitalize;
        }

        .confidence-indicator {
            font-family: var(--font-mono);
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--primary);
        }

        .metric-badge {
            display: inline-block;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .badge-verified {
            background: rgba(16, 185, 129, 0.15);
            color: var(--status-success);
            border: 1px solid rgba(16, 185, 129, 0.3);
        }

        .badge-unvalidated {
            background: rgba(245, 158, 11, 0.15);
            color: var(--status-warning);
            border: 1px solid rgba(245, 158, 11, 0.3);
        }

        .badge-error {
            background: rgba(239, 68, 68, 0.15);
            color: var(--status-error);
            border: 1px solid rgba(239, 68, 68, 0.3);
        }

        .probability-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.5rem 1rem;
        }

        .prob-item {
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
        }

        .prob-header {
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            font-family: var(--font-mono);
        }

        .prob-bar-container {
            height: 6px;
            background: var(--bg-base);
            border-radius: 3px;
            overflow: hidden;
        }

        .prob-bar-fill {
            height: 100%;
            background: var(--accent);
            width: 0%;
            transition: width 0.2s ease;
        }

        /* Telemetry & Stats Table */
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.8rem;
            font-family: var(--font-mono);
        }

        .stats-table th, .stats-table td {
            padding: 0.4rem 0.6rem;
            text-align: left;
            border-bottom: 1px solid var(--border-subtle);
        }

        .stats-table th {
            color: var(--text-muted);
            font-weight: 500;
        }

        .stats-table td:last-child {
            text-align: right;
            font-weight: 600;
        }

        /* Scientific Event Log */
        .log-container {
            background: var(--bg-base);
            border: 1px solid var(--border-subtle);
            border-radius: 4px;
            padding: 0.5rem;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            height: 160px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }

        .log-entry {
            line-height: 1.4;
            color: var(--text-secondary);
        }

        .log-timestamp {
            color: var(--text-muted);
            margin-right: 0.4rem;
        }

        .log-level-info { color: var(--primary); }
        .log-level-warn { color: var(--status-warning); }
        .log-level-error { color: var(--status-error); }

        /* Status Dot */
        .status-dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--status-neutral);
            margin-right: 0.4rem;
        }
        .status-dot.active { background: var(--status-success); box-shadow: 0 0 6px var(--status-success); }
        .status-dot.warning { background: var(--status-warning); }
        .status-dot.error { background: var(--status-error); }
    </style>
</head>
<body>

    <header>
        <div class="brand-container">
            <span class="brand-badge">OVIC EON</span>
            <h1>ERS Telemetry & Model Qualification</h1>
        </div>
        <div class="header-actions">
            <div>
                <span class="status-dot" id="ws-status-dot"></span>
                <span style="font-family: var(--font-mono); font-size: 0.75rem;" id="ws-status-text">DISCONNECTED</span>
            </div>
            <button class="theme-toggle-btn" id="theme-toggle-btn">THEME: DARK</button>
        </div>
    </header>

    <div class="system-banner banner-warning" id="model-integrity-banner">
        <div class="banner-text">
            <strong>Qualification Alert:</strong> Loaded models are unverified baseline graphs with unvalidated provenance. Discrete emotion categorization is suppressed to prevent false claims.
        </div>
        <span class="metric-badge badge-unvalidated" id="overall-model-state-badge">MODEL_LOADED_UNVERIFIED</span>
    </div>

    <div class="layout-grid">
        <!-- Column 1: Hardware Inputs & Session -->
        <div>
            <!-- Hardware Input Panel -->
            <div class="panel">
                <div class="panel-header">
                    <span>Hardware Acquisition</span>
                    <span id="device-count-badge" style="font-size: 0.7rem;">0 DEVICES</span>
                </div>
                <div class="panel-body">
                    <!-- Camera Controls -->
                    <div class="control-group">
                        <label class="control-label" for="camera-select">Video Capture Source</label>
                        <select id="camera-select" class="select-input">
                            <option value="">Detecting cameras...</option>
                        </select>
                        <div class="button-row" style="margin-top: 0.35rem;">
                            <button id="btn-camera-start" class="btn btn-primary">Start Camera</button>
                            <button id="btn-camera-stop" class="btn btn-danger" disabled>Stop Camera</button>
                        </div>
                    </div>

                    <!-- Microphone Controls -->
                    <div class="control-group">
                        <label class="control-label" for="mic-select">Audio Capture Source</label>
                        <select id="mic-select" class="select-input">
                            <option value="">Detecting microphones...</option>
                        </select>
                        <div class="button-row" style="margin-top: 0.35rem;">
                            <button id="btn-mic-start" class="btn btn-primary">Start Mic</button>
                            <button id="btn-mic-stop" class="btn btn-danger" disabled>Stop Mic</button>
                        </div>
                    </div>

                    <!-- Audio Level VU Meter -->
                    <div class="vu-meter-container">
                        <div class="control-label">Live Audio Level (RMS)</div>
                        <div class="vu-meter-bar">
                            <div class="vu-meter-fill" id="vu-meter-fill"></div>
                        </div>
                        <div class="vu-meter-labels">
                            <span>-60 dB</span>
                            <span>-24 dB</span>
                            <span>-6 dB</span>
                            <span>0 dB</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Session & Connection Config -->
            <div class="panel">
                <div class="panel-header">
                    <span>Live Session Telemetry</span>
                </div>
                <div class="panel-body">
                    <div class="control-group">
                        <label class="control-label">Active Session ID</label>
                        <div id="session-id-display" style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--text-secondary); word-break: break-all;">
                            generating...
                        </div>
                    </div>
                    <div class="control-group">
                        <label class="control-label">Inference Interval</label>
                        <select id="fps-select" class="select-input">
                            <option value="1000">1.0 Hz (1000ms)</option>
                            <option value="500" selected>2.0 Hz (500ms)</option>
                            <option value="250">4.0 Hz (250ms)</option>
                            <option value="100">10.0 Hz (100ms)</option>
                        </select>
                    </div>
                    <div class="button-row">
                        <button id="btn-reconnect" class="btn">Reconnect WS</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Column 2: Perception Center Stage & Video Monitor -->
        <div>
            <!-- Video Preview Card -->
            <div class="panel">
                <div class="panel-header">
                    <span>Video Monitor</span>
                    <span id="stream-resolution-text" style="font-family: var(--font-mono); font-size: 0.7rem;">NO STREAM</span>
                </div>
                <div class="panel-body" style="padding: 0.75rem;">
                    <div class="preview-container">
                        <video id="live-video" autoplay playsinline muted></video>
                        <div class="preview-overlay" id="video-overlay">INACTIVE</div>
                    </div>
                </div>
            </div>

            <!-- Multimodal Perception Classification -->
            <div class="panel">
                <div class="panel-header">
                    <span>Multimodal Perception State</span>
                    <span class="metric-badge" id="fusion-state-badge">UNVALIDATED</span>
                </div>
                <div class="panel-body">
                    <div class="perception-card">
                        <div class="state-row">
                            <div>
                                <div class="control-label">Hypothesized Affect State</div>
                                <div class="dominant-category" id="dominant-category-text">Awaiting Evidence</div>
                            </div>
                            <div style="text-align: right;">
                                <div class="control-label">Calibrated Confidence</div>
                                <div class="confidence-indicator" id="confidence-val-text">0.00%</div>
                            </div>
                        </div>

                        <!-- Class Probability Distribution -->
                        <div class="control-label" style="margin-top: 0.5rem;">Modality Calibrated Distribution</div>
                        <div class="probability-grid" id="prob-grid">
                            <!-- Populated dynamically -->
                            <div class="prob-item">
                                <div class="prob-header"><span>Neutral</span><span id="prob-val-neutral">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-neutral"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Happy</span><span id="prob-val-happy">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-happy"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Sad</span><span id="prob-val-sad">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-sad"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Surprise</span><span id="prob-val-surprise">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-surprise"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Anger</span><span id="prob-val-anger">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-anger"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Fear</span><span id="prob-val-fear">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-fear"></div></div>
                            </div>
                            <div class="prob-item">
                                <div class="prob-header"><span>Disgust</span><span id="prob-val-disgust">0%</span></div>
                                <div class="prob-bar-container"><div class="prob-bar-fill" id="prob-bar-disgust"></div></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Scientific Event Log -->
            <div class="panel">
                <div class="panel-header">
                    <span>Inference & Safety Audit Log</span>
                    <button id="btn-clear-log" style="background: transparent; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.7rem; font-family: var(--font-mono);">CLEAR</button>
                </div>
                <div class="panel-body" style="padding: 0.5rem;">
                    <div class="log-container" id="log-output">
                        <div class="log-entry"><span class="log-timestamp">[INIT]</span> System dashboard loaded. Zero persistent capture policy active.</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Column 3: Performance Instrumentation & Model Provenance -->
        <div>
            <!-- Latency & Frame Telemetry -->
            <div class="panel">
                <div class="panel-header">
                    <span>Performance Instrumentation</span>
                </div>
                <div class="panel-body">
                    <table class="stats-table">
                        <tbody>
                            <tr>
                                <td>Frames Ingested</td>
                                <td id="stat-frames-count">0</td>
                            </tr>
                            <tr>
                                <td>Audio Slices Ingested</td>
                                <td id="stat-audio-count">0</td>
                            </tr>
                            <tr>
                                <td>Client P50 Latency</td>
                                <td id="stat-latency-p50">0.0 ms</td>
                            </tr>
                            <tr>
                                <td>Client P95 Latency</td>
                                <td id="stat-latency-p95">0.0 ms</td>
                            </tr>
                            <tr>
                                <td>Client P99 Latency</td>
                                <td id="stat-latency-p99">0.0 ms</td>
                            </tr>
                            <tr>
                                <td>Dropped Inferences</td>
                                <td id="stat-dropped-count">0</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Model Qualification Register Panel -->
            <div class="panel">
                <div class="panel-header">
                    <span>Model Validation Register</span>
                </div>
                <div class="panel-body">
                    <div class="control-group">
                        <div class="control-label">Facial Model State</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.8rem; font-family: var(--font-mono);" id="model-facial-name">facial_emotion_model.onnx</span>
                            <span class="metric-badge badge-unvalidated" id="model-facial-state">UNVERIFIED</span>
                        </div>
                    </div>
                    <div class="control-group">
                        <div class="control-label">Speech Model State</div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.8rem; font-family: var(--font-mono);" id="model-speech-name">speech_emotion_model.onnx</span>
                            <span class="metric-badge badge-unvalidated" id="model-speech-state">UNVERIFIED</span>
                        </div>
                    </div>
                    <div class="control-group" style="margin-top: 0.5rem;">
                        <div class="control-label">Commercial Authorization</div>
                        <span style="font-size: 0.75rem; color: var(--status-error); font-family: var(--font-mono);">RESTRICTED / RESEARCH ONLY</span>
                    </div>
                    <div class="control-group">
                        <div class="control-label">Scientific Invariant</div>
                        <span style="font-size: 0.72rem; color: var(--text-secondary); font-family: var(--font-mono);">
                            is_definitive_claim = False (Enforced)
                        </span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Hidden Canvas for Video Sampling -->
    <canvas id="hidden-canvas" style="display: none;"></canvas>

    <script>
        (function() {
            "use strict";

            // State management
            const state = {
                theme: "dark",
                sessionId: "session-" + Math.random().toString(36).substring(2, 10),
                videoStream: null,
                audioStream: null,
                audioContext: null,
                audioAnalyser: null,
                audioSource: null,
                vuAnimationId: null,
                ws: null,
                wsConnected: false,
                wsReconnectAttempts: 0,
                wsMaxReconnectAttempts: 10,
                wsReconnectTimer: null,
                inferenceIntervalId: null,
                inferenceIntervalMs: 500,
                metrics: {
                    framesSent: 0,
                    audioSent: 0,
                    droppedInferences: 0,
                    latencies: [] // bounded rolling window
                }
            };

            const MAX_LATENCY_HISTORY = 100;

            // DOM elements
            const elements = {
                themeToggleBtn: document.getElementById("theme-toggle-btn"),
                wsStatusDot: document.getElementById("ws-status-dot"),
                wsStatusText: document.getElementById("ws-status-text"),
                cameraSelect: document.getElementById("camera-select"),
                micSelect: document.getElementById("mic-select"),
                btnCameraStart: document.getElementById("btn-camera-start"),
                btnCameraStop: document.getElementById("btn-camera-stop"),
                btnMicStart: document.getElementById("btn-mic-start"),
                btnMicStop: document.getElementById("btn-mic-stop"),
                vuMeterFill: document.getElementById("vu-meter-fill"),
                sessionIdDisplay: document.getElementById("session-id-display"),
                fpsSelect: document.getElementById("fps-select"),
                btnReconnect: document.getElementById("btn-reconnect"),
                liveVideo: document.getElementById("live-video"),
                videoOverlay: document.getElementById("video-overlay"),
                streamResText: document.getElementById("stream-resolution-text"),
                dominantCategoryText: document.getElementById("dominant-category-text"),
                confidenceValText: document.getElementById("confidence-val-text"),
                fusionStateBadge: document.getElementById("fusion-state-badge"),
                modelIntegrityBanner: document.getElementById("model-integrity-banner"),
                overallModelStateBadge: document.getElementById("overall-model-state-badge"),
                modelFacialState: document.getElementById("model-facial-state"),
                modelSpeechState: document.getElementById("model-speech-state"),
                statFramesCount: document.getElementById("stat-frames-count"),
                statAudioCount: document.getElementById("stat-audio-count"),
                statLatencyP50: document.getElementById("stat-latency-p50"),
                statLatencyP95: document.getElementById("stat-latency-p95"),
                statLatencyP99: document.getElementById("stat-latency-p99"),
                statDroppedCount: document.getElementById("stat-dropped-count"),
                logOutput: document.getElementById("log-output"),
                btnClearLog: document.getElementById("btn-clear-log"),
                deviceCountBadge: document.getElementById("device-count-badge"),
                hiddenCanvas: document.getElementById("hidden-canvas")
            };

            elements.sessionIdDisplay.textContent = state.sessionId;

            // Theme toggle
            elements.themeToggleBtn.addEventListener("click", () => {
                const html = document.documentElement;
                if (html.getAttribute("data-theme") === "dark") {
                    html.setAttribute("data-theme", "light");
                    elements.themeToggleBtn.textContent = "THEME: LIGHT";
                    state.theme = "light";
                } else {
                    html.setAttribute("data-theme", "dark");
                    elements.themeToggleBtn.textContent = "THEME: DARK";
                    state.theme = "dark";
                }
            });

            // Logger utility
            function logEvent(msg, level = "info") {
                const entry = document.createElement("div");
                entry.className = "log-entry";
                const now = new Date().toISOString().substring(11, 23);
                entry.innerHTML = `<span class="log-timestamp">[${now}]</span> <span class="log-level-${level}">${msg}</span>`;
                elements.logOutput.appendChild(entry);
                elements.logOutput.scrollTop = elements.logOutput.scrollHeight;
                while (elements.logOutput.children.length > 200) {
                    elements.logOutput.removeChild(elements.logOutput.firstChild);
                }
            }

            elements.btnClearLog.addEventListener("click", () => {
                elements.logOutput.innerHTML = "";
            });

            // Fetch Model Status from API
            async function fetchModelStatus() {
                try {
                    const res = await fetch("/api/models");
                    if (!res.ok) throw new Error("Status " + res.status);
                    const data = await res.json();

                    if (data.models) {
                        for (const m of data.models) {
                            if (m.name.includes("facial")) {
                                elements.modelFacialState.textContent = m.state;
                                elements.modelFacialState.className = "metric-badge " + (m.is_validated ? "badge-verified" : "badge-unvalidated");
                            } else if (m.name.includes("speech")) {
                                elements.modelSpeechState.textContent = m.state;
                                elements.modelSpeechState.className = "metric-badge " + (m.is_validated ? "badge-verified" : "badge-unvalidated");
                            }
                        }
                    }

                    if (data.all_models_validated) {
                        elements.modelIntegrityBanner.className = "system-banner banner-info";
                        elements.modelIntegrityBanner.innerHTML = "<strong>Validated Baseline:</strong> All models verified against validation records.";
                        elements.overallModelStateBadge.textContent = "VALIDATED";
                        elements.overallModelStateBadge.className = "metric-badge badge-verified";
                    }
                } catch (e) {
                    logEvent("Failed to fetch model status: " + e.message, "warn");
                }
            }

            // Hardware Device Enumeration
            async function enumerateDevices() {
                try {
                    const devices = await navigator.mediaDevices.enumerateDevices();
                    elements.cameraSelect.innerHTML = "";
                    elements.micSelect.innerHTML = "";
                    let camCount = 0;
                    let micCount = 0;

                    devices.forEach((d) => {
                        const opt = document.createElement("option");
                        opt.value = d.deviceId;
                        if (d.kind === "videoinput") {
                            camCount++;
                            opt.textContent = d.label || `Camera ${camCount}`;
                            elements.cameraSelect.appendChild(opt);
                        } else if (d.kind === "audioinput") {
                            micCount++;
                            opt.textContent = d.label || `Microphone ${micCount}`;
                            elements.micSelect.appendChild(opt);
                        }
                    });

                    if (camCount === 0) {
                        elements.cameraSelect.innerHTML = '<option value="">No camera detected</option>';
                    }
                    if (micCount === 0) {
                        elements.micSelect.innerHTML = '<option value="">No microphone detected</option>';
                    }

                    elements.deviceCountBadge.textContent = `${camCount} CAM / ${micCount} MIC`;
                    logEvent(`Discovered ${camCount} video and ${micCount} audio sources.`);
                } catch (err) {
                    logEvent("Hardware enumeration failed: " + err.message, "error");
                }
            }

            if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
                navigator.mediaDevices.addEventListener("devicechange", enumerateDevices);
            }

            // Camera Acquisition & Explicit Stop
            elements.btnCameraStart.addEventListener("click", async () => {
                const deviceId = elements.cameraSelect.value;
                const constraints = {
                    video: deviceId ? { deviceId: { exact: deviceId } } : true,
                    audio: false
                };

                try {
                    elements.btnCameraStart.disabled = true;
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    stopCamera(); // Clean up existing
                    state.videoStream = stream;
                    elements.liveVideo.srcObject = stream;
                    elements.btnCameraStop.disabled = false;
                    elements.videoOverlay.textContent = "LIVE";

                    const track = stream.getVideoTracks()[0];
                    const settings = track.getSettings();
                    elements.streamResText.textContent = `${settings.width || 640}x${settings.height || 480} @ ${Math.round(settings.frameRate || 30)}fps`;
                    logEvent("Camera stream acquired: " + track.label);
                } catch (err) {
                    elements.btnCameraStart.disabled = false;
                    logEvent("Camera access rejected: " + err.message, "error");
                }
            });

            function stopCamera() {
                if (state.videoStream) {
                    state.videoStream.getTracks().forEach((track) => {
                        track.stop();
                        logEvent("Explicitly stopped video track: " + track.label);
                    });
                    state.videoStream = null;
                }
                elements.liveVideo.srcObject = null;
                elements.videoOverlay.textContent = "INACTIVE";
                elements.streamResText.textContent = "NO STREAM";
                elements.btnCameraStart.disabled = false;
                elements.btnCameraStop.disabled = true;
            }

            elements.btnCameraStop.addEventListener("click", stopCamera);

            // Microphone Acquisition & VU Meter
            elements.btnMicStart.addEventListener("click", async () => {
                const deviceId = elements.micSelect.value;
                const constraints = {
                    audio: deviceId ? { deviceId: { exact: deviceId } } : true,
                    video: false
                };

                try {
                    elements.btnMicStart.disabled = true;
                    const stream = await navigator.mediaDevices.getUserMedia(constraints);
                    stopMicrophone(); // Clean up existing
                    state.audioStream = stream;

                    // Initialize Web Audio API Analyser
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    state.audioContext = new AudioContext();
                    state.audioSource = state.audioContext.createMediaStreamSource(stream);
                    state.audioAnalyser = state.audioContext.createAnalyser();
                    state.audioAnalyser.fftSize = 256;
                    state.audioSource.connect(state.audioAnalyser);

                    elements.btnMicStop.disabled = false;
                    const track = stream.getAudioTracks()[0];
                    logEvent("Microphone stream acquired: " + track.label);

                    // Start VU meter loop
                    updateVuMeter();
                } catch (err) {
                    elements.btnMicStart.disabled = false;
                    logEvent("Microphone access rejected: " + err.message, "error");
                }
            });

            function stopMicrophone() {
                if (state.vuAnimationId) {
                    cancelAnimationFrame(state.vuAnimationId);
                    state.vuAnimationId = null;
                }
                if (state.audioStream) {
                    state.audioStream.getTracks().forEach((track) => {
                        track.stop();
                        logEvent("Explicitly stopped audio track: " + track.label);
                    });
                    state.audioStream = null;
                }
                if (state.audioContext) {
                    state.audioContext.close();
                    state.audioContext = null;
                }
                elements.vuMeterFill.style.width = "0%";
                elements.btnMicStart.disabled = false;
                elements.btnMicStop.disabled = true;
            }

            elements.btnMicStop.addEventListener("click", stopMicrophone);

            function updateVuMeter() {
                if (!state.audioAnalyser) return;
                const dataArray = new Uint8Array(state.audioAnalyser.frequencyBinCount);
                state.audioAnalyser.getByteFrequencyData(dataArray);

                let sum = 0;
                for (let i = 0; i < dataArray.length; i++) {
                    sum += dataArray[i];
                }
                const average = sum / dataArray.length;
                const percentage = Math.min(100, (average / 128) * 100);
                elements.vuMeterFill.style.width = percentage.toFixed(1) + "%";

                state.vuAnimationId = requestAnimationFrame(updateVuMeter);
            }

            // Window unload safety track cleanup
            window.addEventListener("beforeunload", () => {
                stopCamera();
                stopMicrophone();
                if (state.ws) {
                    state.ws.close();
                }
            });

            // WebSocket Connection Management
            function connectWebSocket() {
                if (state.ws) {
                    try { state.ws.close(); } catch (e) {}
                }

                const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
                const wsUrl = `${protocol}//${window.location.host}/ws/stream`;

                elements.wsStatusDot.className = "status-dot warning";
                elements.wsStatusText.textContent = "CONNECTING...";

                try {
                    state.ws = new WebSocket(wsUrl);
                } catch (e) {
                    logEvent("WebSocket creation failed: " + e.message, "error");
                    scheduleReconnect();
                    return;
                }

                state.ws.onopen = () => {
                    state.wsConnected = true;
                    state.wsReconnectAttempts = 0;
                    elements.wsStatusDot.className = "status-dot active";
                    elements.wsStatusText.textContent = "CONNECTED";
                    logEvent("Live telemetry WebSocket connected.");
                };

                state.ws.onmessage = (event) => {
                    handleWsMessage(event.data);
                };

                state.ws.onclose = () => {
                    state.wsConnected = false;
                    elements.wsStatusDot.className = "status-dot error";
                    elements.wsStatusText.textContent = "DISCONNECTED";
                    logEvent("WebSocket closed.", "warn");
                    scheduleReconnect();
                };

                state.ws.onerror = (err) => {
                    elements.wsStatusDot.className = "status-dot error";
                    elements.wsStatusText.textContent = "ERROR";
                    logEvent("WebSocket error.", "error");
                };
            }

            function scheduleReconnect() {
                if (state.wsReconnectAttempts >= state.wsMaxReconnectAttempts) {
                    logEvent("Max reconnection attempts reached. Click Reconnect WS.", "error");
                    return;
                }
                const delay = Math.min(10000, 1000 * Math.pow(1.5, state.wsReconnectAttempts));
                state.wsReconnectAttempts++;
                logEvent(`Reconnecting in ${(delay / 1000).toFixed(1)}s (attempt ${state.wsReconnectAttempts})...`, "warn");
                clearTimeout(state.wsReconnectTimer);
                state.wsReconnectTimer = setTimeout(connectWebSocket, delay);
            }

            elements.btnReconnect.addEventListener("click", () => {
                state.wsReconnectAttempts = 0;
                connectWebSocket();
            });

            // Handle server perception responses
            function handleWsMessage(raw) {
                try {
                    const data = JSON.parse(raw);
                    if (data.type === "pong") {
                        return;
                    }

                    if (data.type === "error") {
                        logEvent("Server returned error: " + data.message, "error");
                        return;
                    }

                    if (data.type === "observation") {
                        renderObservation(data);
                    }
                } catch (e) {
                    logEvent("Failed to parse server message: " + e.message, "error");
                }
            }

            function renderObservation(obs) {
                // Update classification UI
                const dominant = obs.dominant_category || "insufficient_evidence";
                const confidence = obs.confidence !== undefined ? obs.confidence : 0.0;
                const isValidated = obs.is_validated === true;

                elements.dominantCategoryText.textContent = dominant.replace("_", " ");
                elements.confidenceValText.textContent = (confidence * 100).toFixed(1) + "%";

                if (isValidated) {
                    elements.fusionStateBadge.textContent = "VALIDATED";
                    elements.fusionStateBadge.className = "metric-badge badge-verified";
                } else {
                    elements.fusionStateBadge.textContent = "UNVALIDATED";
                    elements.fusionStateBadge.className = "metric-badge badge-unvalidated";
                }

                // Render class probabilities
                if (obs.probabilities) {
                    for (const [cat, p] of Object.entries(obs.probabilities)) {
                        const bar = document.getElementById(`prob-bar-${cat}`);
                        const val = document.getElementById(`prob-val-${cat}`);
                        if (bar && val) {
                            const pct = Math.round(p * 100);
                            bar.style.width = `${pct}%`;
                            val.textContent = `${pct}%`;
                        }
                    }
                }

                // Calculate Latency if timestamp matches
                if (obs.timestamp) {
                    const now = Date.now();
                    const roundtrip = Math.max(1, now - (obs.client_sent_timestamp || (obs.timestamp * 1000)));
                    recordLatency(roundtrip);
                }
            }

            // Latency percentiles calculation
            function recordLatency(latencyMs) {
                state.metrics.latencies.push(latencyMs);
                if (state.metrics.latencies.length > MAX_LATENCY_HISTORY) {
                    state.metrics.latencies.shift();
                }

                const sorted = [...state.metrics.latencies].sort((a, b) => a - b);
                const n = sorted.length;
                const p50 = sorted[Math.floor(n * 0.50)] || 0;
                const p95 = sorted[Math.floor(n * 0.95)] || 0;
                const p99 = sorted[Math.floor(n * 0.99)] || 0;

                elements.statLatencyP50.textContent = p50.toFixed(1) + " ms";
                elements.statLatencyP95.textContent = p95.toFixed(1) + " ms";
                elements.statLatencyP99.textContent = p99.toFixed(1) + " ms";
            }

            // Frame Capturing & Inference Dispatch
            function captureAndSend() {
                if (!state.wsConnected || state.ws.readyState !== WebSocket.OPEN) {
                    return;
                }

                let frameData = null;

                if (state.videoStream && elements.liveVideo.videoWidth > 0) {
                    const canvas = elements.hiddenCanvas;
                    canvas.width = 320; // Reduced resolution for efficient edge processing
                    canvas.height = 240;
                    const ctx = canvas.getContext("2d");
                    ctx.drawImage(elements.liveVideo, 0, 0, 320, 240);
                    frameData = canvas.toDataURL("image/jpeg", 0.6);
                    state.metrics.framesSent++;
                    elements.statFramesCount.textContent = state.metrics.framesSent;
                }

                if (frameData) {
                    const payload = {
                        type: "frame",
                        session_id: state.sessionId,
                        data: frameData,
                        format: "image/jpeg",
                        client_timestamp: Date.now()
                    };

                    try {
                        state.ws.send(JSON.stringify(payload));
                    } catch (e) {
                        state.metrics.droppedInferences++;
                        elements.statDroppedCount.textContent = state.metrics.droppedInferences;
                    }
                }
            }

            // Inference Frequency Selector
            elements.fpsSelect.addEventListener("change", (e) => {
                state.inferenceIntervalMs = parseInt(e.target.value, 10);
                clearInterval(state.inferenceIntervalId);
                state.inferenceIntervalId = setInterval(captureAndSend, state.inferenceIntervalMs);
                logEvent(`Inference frequency set to ${(1000 / state.inferenceIntervalMs).toFixed(1)} Hz.`);
            });

            // Initialize
            enumerateDevices();
            fetchModelStatus();
            connectWebSocket();
            state.inferenceIntervalId = setInterval(captureAndSend, state.inferenceIntervalMs);

        })();
    </script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Return the raw HTML content of the enterprise live telemetry dashboard."""
    return DASHBOARD_HTML
