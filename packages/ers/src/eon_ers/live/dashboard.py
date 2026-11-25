"""Enterprise-grade responsive 15-view UI dashboard for OVIC EON ERS.

Fixes Phase 3.2 critical consent, live capture, audio resampling, WebSocket,
and error-handling defects:
- Zero default or hard-coded consent credentials.
- No automatic consent registration on webcam, microphone, or analysis calls.
- Explicit Grant Consent action, backend-synchronized consent status, and terminal revocation lock.
- Real browser WebRTC video & AudioContext mic capture with CPU-safe 16kHz downsampling,
  bounded buffer/backpressure guards, track disconnect handlers, and node cleanup.
- Full HTTP error reporting across every endpoint with optional X-API-Key auth support.
"""

from __future__ import annotations

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="icon" href="data:," />
<title>OVIC EON — ERS Enterprise Console</title>
<style>
  :root[data-theme="dark"] {
    --bg: #0b0f17; --surface: #111827; --surface-2: #182235; --border: #263248;
    --text: #e5edf7; --muted: #8ea0b8; --accent: #3b82f6; --accent-fg: #ffffff;
    --ok: #10b981; --warn: #f59e0b; --err: #ef4444; --chip: #1e293b;
  }
  :root[data-theme="light"] {
    --bg: #f4f6fa; --surface: #ffffff; --surface-2: #f8fafc; --border: #dbe2ec;
    --text: #0f172a; --muted: #475569; --accent: #1d4ed8; --accent-fg: #ffffff;
    --ok: #047857; --warn: #b45309; --err: #b91c1c; --chip: #e2e8f0;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
    background: var(--bg); color: var(--text); font-size: 13px; line-height: 1.5;
    display: flex; min-height: 100vh;
  }
  @media (prefers-reduced-motion: reduce) { * { transition: none !important; animation: none !important; } }
  .sidebar {
    width: 230px; flex-shrink: 0; background: var(--surface); border-right: 1px solid var(--border);
    display: flex; flex-direction: column; padding: 14px 10px; gap: 4px;
  }
  .brand { padding: 8px 10px 14px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
  .brand-title { font-weight: 700; font-size: 14px; letter-spacing: 0.03em; }
  .brand-sub { font-size: 11px; color: var(--muted); }
  .nav-btn {
    text-align: left; background: transparent; border: none; color: var(--muted);
    padding: 7px 10px; border-radius: 6px; cursor: pointer; font-size: 12.5px; font-weight: 500;
  }
  .nav-btn:hover { background: var(--surface-2); color: var(--text); }
  .nav-btn.active { background: var(--accent); color: var(--accent-fg); }
  .nav-btn:focus-visible, button:focus-visible, input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--accent); outline-offset: 2px;
  }
  .main { flex: 1; display: flex; flex-direction: column; min-width: 0; }
  .topbar {
    background: var(--surface); border-bottom: 1px solid var(--border); padding: 10px 18px;
    display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px;
  }
  .badges { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .pill {
    padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 600;
    background: var(--chip); color: var(--text); border: 1px solid var(--border);
  }
  .pill.ok { border-color: var(--ok); color: var(--ok); }
  .pill.warn { border-color: var(--warn); color: var(--warn); }
  .pill.err { border-color: var(--err); color: var(--err); }
  .banner {
    background: rgba(245, 158, 11, 0.12); border-bottom: 1px solid var(--warn);
    color: var(--text); padding: 8px 18px; font-size: 12px;
  }
  .err-banner {
    display: none; background: rgba(239, 68, 68, 0.15); border-bottom: 1px solid var(--err);
    color: var(--text); padding: 8px 18px; font-size: 12px; font-weight: 600;
    justify-content: space-between; align-items: center; gap: 10px;
  }
  .err-banner.visible { display: flex; }
  .content { padding: 18px; max-width: 1400px; width: 100%; }
  .view { display: none; }
  .view.active { display: block; }
  .grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }
  .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px; }
  .card {
    background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
    padding: 14px; margin-bottom: 14px;
  }
  .card-title { font-weight: 600; font-size: 13px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .kpi { font-size: 22px; font-weight: 700; margin-top: 2px; }
  .muted { color: var(--muted); font-size: 12px; }
  .row { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 10px; }
  label { display: block; font-size: 11.5px; color: var(--muted); margin-bottom: 4px; }
  input[type="text"], input[type="password"], input[type="number"], select, textarea {
    width: 100%; background: var(--surface-2); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 9px; font-size: 12.5px;
  }
  button.btn {
    background: var(--surface-2); color: var(--text); border: 1px solid var(--border);
    border-radius: 6px; padding: 7px 12px; font-size: 12.5px; font-weight: 600; cursor: pointer;
  }
  button.btn.primary { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }
  button.btn.danger { background: var(--err); color: #fff; border-color: var(--err); }
  button.btn:disabled { opacity: 0.45; cursor: not-allowed; }
  video { width: 100%; max-height: 280px; background: #000; border-radius: 6px; border: 1px solid var(--border); }
  .meter { height: 10px; background: var(--surface-2); border-radius: 999px; overflow: hidden; border: 1px solid var(--border); }
  .meter > div { height: 100%; background: var(--ok); width: 0%; transition: width 120ms linear; }
  pre {
    background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px;
    padding: 10px; overflow-x: auto; font-size: 11.5px; max-height: 300px;
  }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th, td { text-align: left; padding: 7px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
  th { color: var(--muted); font-weight: 600; }
  @media (max-width: 820px) {
    body { flex-direction: column; }
    .sidebar { width: 100%; flex-direction: row; overflow-x: auto; border-right: none; border-bottom: 1px solid var(--border); }
    .brand { display: none; }
  }
</style>
</head>
<body>
<nav class="sidebar" aria-label="ERS Navigation" role="tablist">
  <div class="brand">
    <div class="brand-title">OVIC EON</div>
    <div class="brand-sub">ERS Telemetry &amp; Console</div>
  </div>
  <button class="nav-btn active" role="tab" data-view="overview">1. Overview</button>
  <button class="nav-btn" role="tab" data-view="live">2. Live ERS</button>
  <button class="nav-btn" role="tab" data-view="image">3. Image Analysis</button>
  <button class="nav-btn" role="tab" data-view="audio">4. Audio Analysis</button>
  <button class="nav-btn" role="tab" data-view="video">5. Video Analysis</button>
  <button class="nav-btn" role="tab" data-view="text">6. Text Analysis</button>
  <button class="nav-btn" role="tab" data-view="multimodal">7. Multimodal Analysis</button>
  <button class="nav-btn" role="tab" data-view="registry">8. Model Registry</button>
  <button class="nav-btn" role="tab" data-view="evaluation">9. Model Evaluation</button>
  <button class="nav-btn" role="tab" data-view="datasets">10. Dataset Management</button>
  <button class="nav-btn" role="tab" data-view="sessions">11. Session Management</button>
  <button class="nav-btn" role="tab" data-view="apidocs">12. API Documentation</button>
  <button class="nav-btn" role="tab" data-view="health">13. System Health</button>
  <button class="nav-btn" role="tab" data-view="settings">14. Settings</button>
  <button class="nav-btn" role="tab" data-view="privacy">15. Privacy &amp; Consent</button>
</nav>

<div class="main">
  <header class="topbar">
    <div class="badges">
      <span class="pill" id="badge-health">Engine: checking...</span>
      <span class="pill" id="badge-qual">Qualification: checking...</span>
      <span class="pill" id="badge-ws">WS: disconnected</span>
      <span class="pill warn" id="badge-consent">Consent: not granted</span>
    </div>
    <div class="badges">
      <span class="muted">Invariant: <code>is_definitive_claim = False</code> (No Robot Actuation)</span>
      <button class="btn" id="btn-theme" aria-label="Toggle Light/Dark Theme">Theme</button>
    </div>
  </header>

  <div class="banner" id="qual-banner">
    <strong>Epistemic &amp; Scientific Notice:</strong> ERS estimates observable signals only and never asserts inner truth. Unvalidated baseline models remain marked <code>MODEL_UNVALIDATED</code> until external benchmark qualification succeeds.
  </div>

  <div class="err-banner" id="global-err-banner" role="alert">
    <span id="global-err-text"></span>
    <button class="btn" onclick="clearError()" aria-label="Dismiss Error">Dismiss</button>
  </div>

  <main class="content">
    <!-- 1. Overview -->
    <section id="view-overview" class="view active">
      <div class="grid-3">
        <div class="card"><div class="muted">Backend Status</div><div class="kpi" id="ov-health">-</div><div class="muted" id="ov-state"></div></div>
        <div class="card"><div class="muted">Qualified / Total Models</div><div class="kpi" id="ov-models">-</div><div class="muted" id="ov-qual-note"></div></div>
        <div class="card"><div class="muted">Active Sessions &amp; Throughput</div><div class="kpi" id="ov-sessions">-</div><div class="muted" id="ov-throughput"></div></div>
        <div class="card"><div class="muted">Process CPU / RSS Memory</div><div class="kpi" id="ov-resources">-</div><div class="muted" id="ov-errors"></div></div>
      </div>
      <div class="card">
        <div class="card-title">Readiness &amp; Loaded Model Qualification <button class="btn" onclick="refreshOverview()">Refresh</button></div>
        <div id="ov-model-list" class="muted">Loading models...</div>
      </div>
    </section>

    <!-- 2. Live ERS -->
    <section id="view-live" class="view">
      <div class="card">
        <div class="card-title">Explicit Consent &amp; Live Session Controls</div>
        <div class="grid-3">
          <div>
            <label for="live-session-id">Active Session ID (Revoked IDs are permanent)</label>
            <input id="live-session-id" type="text" value="" placeholder="Session ID" onchange="onSessionIdChanged()" />
          </div>
          <div>
            <label for="live-consent-ref">Explicit User Consent Token (Required — No Default)</label>
            <input id="live-consent-ref" type="password" value="" placeholder="Enter your explicit consent token" />
          </div>
          <div>
            <label for="live-mode">Streaming Mode</label>
            <select id="live-mode">
              <option value="both">Webcam + Microphone</option>
              <option value="camera">Webcam Only</option>
              <option value="mic">Microphone Only</option>
            </select>
          </div>
        </div>
        <div class="row" style="margin-top:10px;">
          <button class="btn primary" id="btn-grant-consent" onclick="registerConsent()">Grant Consent</button>
          <button class="btn danger" id="btn-revoke-consent" onclick="revokeConsent()" disabled>Revoke Consent</button>
          <button class="btn" id="btn-new-session" onclick="startNewSession()">New Session</button>
          <button class="btn primary" id="btn-start-cam" onclick="startCamera()" disabled>Start Webcam</button>
          <button class="btn" id="btn-stop-cam" onclick="stopCamera()" disabled>Stop Webcam</button>
          <button class="btn primary" id="btn-start-mic" onclick="startMic()" disabled>Start Microphone</button>
          <button class="btn" id="btn-stop-mic" onclick="stopMic()" disabled>Stop Microphone</button>
          <button class="btn" id="btn-ws-reconnect" onclick="connectWebSocket()">Connect WS</button>
          <button class="btn" onclick="togglePauseLive()" id="btn-pause-live">Pause Stream</button>
        </div>
        <div class="grid-3">
          <div><label for="sel-cam">Camera Device</label><select id="sel-cam"></select></div>
          <div><label for="sel-mic">Microphone Device</label><select id="sel-mic"></select></div>
          <div>
            <label for="live-fps">Capture FPS (<span id="lbl-fps">2</span>)</label>
            <input id="live-fps" type="number" min="0.5" max="10" step="0.5" value="2" onchange="document.getElementById('lbl-fps').textContent=this.value" />
          </div>
        </div>
      </div>

      <div class="grid-2">
        <div class="card">
          <div class="card-title">Live Webcam Preview <span class="muted" id="live-cam-stats">Inactive</span></div>
          <video id="webcam-video" autoplay muted playsinline></video>
          <canvas id="capture-canvas" width="320" height="240" style="display:none;"></canvas>
          <div style="margin-top:10px;">
            <div class="muted" style="margin-bottom:4px;">Microphone RMS Energy Level <span id="mic-silence-badge">(Inactive)</span></div>
            <div class="meter"><div id="mic-level-bar"></div></div>
          </div>
        </div>
        <div class="card">
          <div class="card-title">Live Observations &amp; Multimodal Estimate</div>
          <table>
            <tr><th>Stream</th><th>Estimate</th><th>Confidence</th><th>Uncertainty</th><th>Latency</th></tr>
            <tr><td>Facial</td><td id="res-face-dom">-</td><td id="res-face-conf">-</td><td id="res-face-unc">-</td><td id="res-face-lat">-</td></tr>
            <tr><td>Vocal</td><td id="res-speech-dom">-</td><td id="res-speech-conf">-</td><td id="res-speech-unc">-</td><td id="res-speech-lat">-</td></tr>
            <tr><td>Multimodal</td><td id="res-fusion-dom">-</td><td id="res-fusion-conf">-</td><td id="res-fusion-unc">-</td><td id="res-fusion-lat">-</td></tr>
          </table>
          <div style="margin-top:10px;"><label>Live Stream Output Log</label><pre id="live-log">Grant explicit consent before activating webcam or microphone capture.</pre></div>
        </div>
      </div>
    </section>

    <!-- 3. Image Analysis -->
    <section id="view-image" class="view">
      <div class="card">
        <div class="card-title">Image Expression Analysis (<code>POST /api/v1/analyze/image</code>)</div>
        <div class="row">
          <input type="file" id="img-file" accept="image/jpeg,image/png,image/webp,image/bmp" />
          <button class="btn primary" onclick="analyzeImageUpload()">Analyze Image</button>
        </div>
        <pre id="img-result">Grant explicit consent first, then select an image file and click Analyze Image.</pre>
      </div>
    </section>

    <!-- 4. Audio Analysis -->
    <section id="view-audio" class="view">
      <div class="card">
        <div class="card-title">Vocal Affect Upload (<code>POST /api/v1/analyze/audio</code>)</div>
        <div class="row">
          <input type="file" id="aud-file" accept="audio/wav,.wav,.pcm" />
          <button class="btn primary" onclick="analyzeAudioUpload()">Analyze Audio</button>
        </div>
        <pre id="aud-result">Grant explicit consent first, then select a WAV file and click Analyze Audio.</pre>
      </div>
    </section>

    <!-- 5. Video Analysis -->
    <section id="view-video" class="view">
      <div class="card">
        <div class="card-title">Bounded Video Analysis (<code>POST /api/v1/analyze/video</code>)</div>
        <div class="row">
          <input type="file" id="vid-file" accept="video/avi,image/gif,image/webp,.avi,.gif,.webp" />
          <button class="btn primary" onclick="analyzeVideoUpload()">Analyze Video</button>
        </div>
        <pre id="vid-result">Grant explicit consent first, then select a RIFF AVI (MJPEG) or animated GIF/WEBP file.</pre>
      </div>
    </section>

    <!-- 6. Text Analysis -->
    <section id="view-text" class="view">
      <div class="card">
        <div class="card-title">Textual Sentiment &amp; Affect Analysis (<code>POST /api/v1/analyze/text</code>)</div>
        <label for="txt-input">Input UTF-8 Text (kept separate from visual/vocal expression)</label>
        <textarea id="txt-input" rows="4" placeholder="Enter text sample to analyze..."></textarea>
        <div class="row" style="margin-top:10px;">
          <button class="btn primary" onclick="analyzeTextInput()">Analyze Text</button>
        </div>
        <pre id="txt-result">Grant explicit consent first, then enter UTF-8 text and click Analyze Text.</pre>
      </div>
    </section>

    <!-- 7. Multimodal Analysis -->
    <section id="view-multimodal" class="view">
      <div class="card">
        <div class="card-title">Three-Modality Fusion (<code>POST /api/v1/analyze/multimodal</code>)</div>
        <div class="grid-3">
          <div><label for="mm-img">Optional Facial Image</label><input type="file" id="mm-img" accept="image/*" /></div>
          <div><label for="mm-aud">Optional WAV Audio</label><input type="file" id="mm-aud" accept="audio/wav,.wav" /></div>
          <div><label for="mm-txt">Optional Text</label><input type="text" id="mm-txt" placeholder="Optional text utterance..." /></div>
        </div>
        <div class="row" style="margin-top:10px;"><button class="btn primary" onclick="analyzeMultimodalUpload()">Run Multimodal Fusion</button></div>
        <pre id="mm-result">Grant explicit consent first, provide any 1, 2, or 3 modalities, and run fusion.</pre>
      </div>
    </section>

    <!-- 8. Model Registry -->
    <section id="view-registry" class="view">
      <div class="card">
        <div class="card-title">Model Registry &amp; Activation Guard <button class="btn" onclick="loadRegistry()">Refresh</button></div>
        <div id="reg-table">Loading model registry...</div>
      </div>
    </section>

    <!-- 9. Model Evaluation -->
    <section id="view-evaluation" class="view">
      <div class="card">
        <div class="card-title">Holdout Evaluation &amp; Calibration Reports <button class="btn" onclick="loadEvaluations()">Refresh</button></div>
        <pre id="eval-output">Loading evaluation records...</pre>
      </div>
    </section>

    <!-- 10. Dataset Management -->
    <section id="view-datasets" class="view">
      <div class="card">
        <div class="card-title">Registered Datasets &amp; Provenance <button class="btn" onclick="loadDatasets()">Refresh</button></div>
        <div id="ds-table">Loading dataset register...</div>
      </div>
    </section>

    <!-- 11. Session Management -->
    <section id="view-sessions" class="view">
      <div class="card">
        <div class="card-title">Active Live Sessions <button class="btn" onclick="loadSessions()">Refresh</button></div>
        <div class="row">
          <input type="text" id="new-sess-id" placeholder="New session ID (optional)" style="max-width:260px;" />
          <button class="btn primary" onclick="createNewSession()">Create Session</button>
        </div>
        <div id="sess-table">Loading sessions...</div>
      </div>
    </section>

    <!-- 12. API Documentation -->
    <section id="view-apidocs" class="view">
      <div class="card">
        <div class="card-title">API Endpoints &amp; Interactive OpenAPI Links</div>
        <p class="muted" style="margin-bottom:10px;">Inspect interactive schemas or system endpoints directly:</p>
        <div class="row">
          <a class="btn primary" href="/docs" target="_blank" rel="noopener">Swagger UI (/docs)</a>
          <a class="btn" href="/redoc" target="_blank" rel="noopener">ReDoc (/redoc)</a>
          <a class="btn" href="/openapi.json" target="_blank" rel="noopener">OpenAPI JSON</a>
          <a class="btn" href="/health" target="_blank" rel="noopener">/health</a>
          <a class="btn" href="/ready" target="_blank" rel="noopener">/ready</a>
          <a class="btn" href="/version" target="_blank" rel="noopener">/version</a>
          <a class="btn" href="/capabilities" target="_blank" rel="noopener">/capabilities</a>
          <a class="btn" href="/metrics?format=prometheus" target="_blank" rel="noopener">/metrics</a>
        </div>
      </div>
    </section>

    <!-- 13. System Health & Diagnostics -->
    <section id="view-health" class="view">
      <div class="card">
        <div class="card-title">CPU Diagnostics, Verified Devices &amp; Telemetry <button class="btn" onclick="loadDiagnostics()">Refresh</button></div>
        <pre id="diag-output">Loading host diagnostics...</pre>
      </div>
    </section>

    <!-- 14. Settings -->
    <section id="view-settings" class="view">
      <div class="card">
        <div class="card-title">Console &amp; Security Settings</div>
        <div class="grid-2">
          <div>
            <label for="cfg-api-key">Optional Service API Key (X-API-Key, kept in volatile page memory)</label>
            <input id="cfg-api-key" type="password" placeholder="Required when EON_ERS_API_AUTH=true" onchange="state.apiKey=this.value.trim(); refreshOverview(); refreshConsentStatus();" />
          </div>
          <div>
            <label for="cfg-res">Webcam Resolution</label>
            <select id="cfg-res">
              <option value="320x240">320 x 240 (Low CPU)</option>
              <option value="640x480" selected>640 x 480 (Balanced)</option>
            </select>
          </div>
        </div>
      </div>
    </section>

    <!-- 15. Privacy & Consent -->
    <section id="view-privacy" class="view">
      <div class="card">
        <div class="card-title">Privacy, Zero-Retention &amp; Robot Safety Verification</div>
        <ul style="margin-left:18px;">
          <li>Consent tokens are hashed with SHA-256 on the backend and required on every capture call.</li>
          <li>No consent credential is pre-populated or automatically submitted.</li>
          <li>Revoked sessions are terminal and cannot be reused; a new session ID and explicit consent action are mandatory.</li>
          <li>Raw webcam frames, microphone PCM buffers, video bytes, and text inputs are scrubbed immediately after inference (`zero_disk_retention = True`).</li>
          <li>Actuator safety interlocks block robot motion commands; `is_definitive_claim = False` is strictly enforced.</li>
        </ul>
        <pre id="privacy-status" style="margin-top:10px;">Click Refresh Status to inspect active session consent metadata.</pre>
        <div class="row" style="margin-top:8px;">
          <button class="btn" onclick="refreshConsentStatus()">Refresh Status</button>
          <button class="btn danger" onclick="revokeConsent()">Immediate Revocation</button>
        </div>
      </div>
    </section>
  </main>
</div>

<script>
function generateSessionId() {
  if (window.crypto && typeof window.crypto.randomUUID === "function") {
    return "live-" + window.crypto.randomUUID().slice(0, 12);
  }
  return "live-" + Math.random().toString(16).slice(2, 10) + "-" + Date.now().toString(36);
}

const state = {
  sessionId: generateSessionId(),
  consentReference: "",
  apiKey: "",
  ws: null,
  wsAuthenticated: false,
  wsManuallyClosed: false,
  wsHeartbeatTimer: null,
  camStream: null,
  micStream: null,
  audioCtx: null,
  audioSrcNode: null,
  audioProcNode: null,
  camTimer: null,
  paused: false,
  consentGranted: false,
  sessionRevoked: false
};

function showError(msg) {
  const banner = document.getElementById("global-err-banner");
  document.getElementById("global-err-text").textContent = msg;
  banner.classList.add("visible");
}

function clearError() {
  const banner = document.getElementById("global-err-banner");
  banner.classList.remove("visible");
  document.getElementById("global-err-text").textContent = "";
}

function apiHeaders(extra = {}) {
  const h = { ...extra };
  if (state.apiKey) h["X-API-Key"] = state.apiKey;
  return h;
}

async function apiRequest(url, options = {}) {
  const opts = {
    ...options,
    headers: apiHeaders(options.headers || {})
  };
  const res = await fetch(url, opts);
  const rawText = await res.text();
  let parsed = null;
  if (rawText) {
    try { parsed = JSON.parse(rawText); } catch (_) { parsed = { raw: rawText }; }
  }
  if (!res.ok) {
    let detail = res.statusText || "Request failed";
    if (parsed && parsed.detail) {
      detail = typeof parsed.detail === "string"
        ? parsed.detail
        : (parsed.detail.message || JSON.stringify(parsed.detail));
    } else if (parsed && parsed.error) {
      detail = typeof parsed.error === "string"
        ? parsed.error
        : (parsed.error.message || JSON.stringify(parsed.error));
    } else if (rawText) {
      detail = rawText;
    }
    throw new Error(`HTTP ${res.status}: ${detail}`);
  }
  return parsed ?? {};
}

function updateConsentControls() {
  const canCapture = state.consentGranted && !state.sessionRevoked;
  const bc = document.getElementById("badge-consent");
  if (state.sessionRevoked) {
    bc.textContent = "Consent: REVOKED (Terminal Session)";
    bc.className = "pill err";
  } else if (state.consentGranted) {
    bc.textContent = "Consent: ACTIVE";
    bc.className = "pill ok";
  } else {
    bc.textContent = "Consent: not granted";
    bc.className = "pill warn";
  }
  document.getElementById("btn-grant-consent").disabled = state.sessionRevoked;
  document.getElementById("btn-revoke-consent").disabled = !canCapture;
  document.getElementById("btn-start-cam").disabled = !canCapture || !!state.camStream;
  document.getElementById("btn-start-mic").disabled = !canCapture || !!state.micStream;
  document.getElementById("btn-stop-cam").disabled = !state.camStream;
  document.getElementById("btn-stop-mic").disabled = !state.micStream;
}

function formatMediaError(kind, err) {
  const name = (err && err.name) ? err.name : "";
  const msg = (err && err.message) ? err.message : String(err || "Unknown error");
  if (name === "NotAllowedError" || name === "PermissionDeniedError") {
    return `${kind} permission denied (${name}). Allow ${kind.toLowerCase()} access in your browser site permissions (address bar icon) for ${location.origin}, then retry.`;
  }
  if (name === "NotFoundError" || name === "DevicesNotFoundError") {
    return `No ${kind.toLowerCase()} device detected (${name}). Verify hardware connection and OS privacy settings, then click Retry.`;
  }
  if (name === "NotReadableError" || name === "TrackStartError") {
    return `${kind} hardware is busy or unreadable (${name}). Close any other application using the device and retry.`;
  }
  return `${kind} start failed: ${msg}`;
}

document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("view-" + btn.dataset.view).classList.add("active");
    const v = btn.dataset.view;
    if (v === "overview") refreshOverview();
    if (v === "registry") loadRegistry();
    if (v === "evaluation") loadEvaluations();
    if (v === "datasets") loadDatasets();
    if (v === "sessions") loadSessions();
    if (v === "health") loadDiagnostics();
    if (v === "privacy") refreshConsentStatus();
  });
});

document.getElementById("btn-theme").addEventListener("click", () => {
  const root = document.documentElement;
  const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
  root.setAttribute("data-theme", next);
  try { localStorage.setItem("ers_theme", next); } catch (_) {}
});
try {
  const savedTheme = localStorage.getItem("ers_theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    document.documentElement.setAttribute("data-theme", savedTheme);
  }
} catch (_) {}

function syncInputs() {
  const sidEl = document.getElementById("live-session-id");
  const refEl = document.getElementById("live-consent-ref");
  if (!sidEl.value.trim()) sidEl.value = state.sessionId || generateSessionId();
  state.sessionId = sidEl.value.trim();
  state.consentReference = refEl.value.trim();
}

function onSessionIdChanged() {
  state.consentGranted = false;
  state.sessionRevoked = false;
  updateConsentControls();
  refreshConsentStatus();
}

function startNewSession() {
  clearError();
  stopCamera();
  stopMic();
  if (state.ws) {
    state.wsManuallyClosed = true;
    try { state.ws.close(); } catch (_) {}
    state.ws = null;
  }
  state.sessionId = generateSessionId();
  state.consentReference = "";
  state.consentGranted = false;
  state.sessionRevoked = false;
  document.getElementById("live-session-id").value = state.sessionId;
  document.getElementById("live-consent-ref").value = "";
  document.getElementById("live-log").textContent = "New session created. Enter an explicit consent token and click Grant Consent.";
  updateConsentControls();
  refreshConsentStatus();
}

async function fetchModelStatus() {
  const data = await apiRequest("/api/models");
  const isQual = data.overall_qualification === "VALIDATED";
  const badge = document.getElementById("badge-qual");
  badge.textContent = isQual ? "Qualification: VALIDATED" : "Qualification: " + data.overall_qualification;
  badge.className = "pill " + (isQual ? "ok" : "warn");
  const listEl = document.getElementById("ov-model-list");
  const models = data.models || [];
  document.getElementById("ov-models").textContent = `${models.filter(m => m.is_validated).length} / ${models.length}`;
  document.getElementById("ov-qual-note").textContent = data.overall_qualification;
  listEl.innerHTML = models.map(m =>
    `<div style="padding:4px 0;"><strong>${m.modality || m.model_id}</strong> (${m.model_id} v${m.version}) — <code>${m.state}</code> | validated: ${m.is_validated}</div>`
  ).join("") || "No models loaded.";
}

async function refreshOverview() {
  try {
    const [h, r, d] = await Promise.all([
      apiRequest("/health"),
      apiRequest("/ready"),
      apiRequest("/api/v1/diagnostics")
    ]);
    document.getElementById("ov-health").textContent = h.status;
    document.getElementById("ov-state").textContent = `State: ${h.state} | Validated Inference Ready: ${r.qualified_inference_ready}`;
    const bh = document.getElementById("badge-health");
    bh.textContent = "Engine: " + h.status;
    bh.className = "pill " + (h.is_running ? "ok" : "err");
    const m = d.metrics || {};
    const sys = d.system || {};
    document.getElementById("ov-sessions").textContent = `${m.ws_active_connections || 0} WS / ${m.total_processed || 0} ops`;
    document.getElementById("ov-throughput").textContent = `${m.throughput_per_second || 0} ops/s | dropped ${m.dropped_frames || 0}`;
    document.getElementById("ov-resources").textContent = `${sys.process_cpu_percent || 0}% CPU / ${sys.process_rss_mb || 0} MB`;
    document.getElementById("ov-errors").textContent = `Errors: ${m.error_count || 0} | p95: ${m.latency_p95_ms || 0} ms`;
    await fetchModelStatus();
  } catch (err) {
    document.getElementById("ov-health").textContent = "AUTH/ERROR";
    showError("Overview refresh failed: " + err.message);
  }
}

async function refreshConsentStatus() {
  syncInputs();
  try {
    const st = await apiRequest(`/api/consent/status/${encodeURIComponent(state.sessionId)}`);
    state.consentGranted = Boolean(st.has_active_consent) && !Boolean(st.is_revoked);
    state.sessionRevoked = Boolean(st.is_revoked);
    updateConsentControls();
    const privEl = document.getElementById("privacy-status");
    if (privEl) privEl.textContent = JSON.stringify(st, null, 2);
  } catch (err) {
    state.consentGranted = false;
    updateConsentControls();
    const privEl = document.getElementById("privacy-status");
    if (privEl) privEl.textContent = "Consent status unavailable: " + err.message;
  }
}

async function registerConsent() {
  clearError();
  syncInputs();
  if (!state.consentReference) {
    const msg = "Consent registration blocked: enter an explicit consent token before clicking Grant Consent.";
    showError(msg);
    document.getElementById("live-log").textContent = msg;
    return;
  }
  try {
    const data = await apiRequest("/api/consent/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference })
    });
    state.consentGranted = Boolean(data.has_active_consent);
    state.sessionRevoked = Boolean(data.is_revoked);
    updateConsentControls();
    await refreshConsentStatus();
    if (state.consentGranted && (!state.ws || state.ws.readyState !== WebSocket.OPEN)) {
      connectWebSocket();
    }
    document.getElementById("live-log").textContent = `Explicit consent active for session '${state.sessionId}'.`;
  } catch (err) {
    state.consentGranted = false;
    if (err.message.toLowerCase().includes("revoked")) {
      state.sessionRevoked = true;
    }
    updateConsentControls();
    showError("Grant Consent failed: " + err.message);
    document.getElementById("live-log").textContent = "Grant Consent failed: " + err.message;
  }
}

async function revokeConsent() {
  clearError();
  syncInputs();
  stopCamera();
  stopMic();
  try {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({ type: "revoke", session_id: state.sessionId }));
    }
    await apiRequest("/api/consent/revoke", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId })
    });
    state.consentGranted = false;
    state.sessionRevoked = true;
    updateConsentControls();
    await refreshConsentStatus();
    document.getElementById("live-log").textContent =
      `Session '${state.sessionId}' revoked and terminated. Click 'New Session' to start a new consented session.`;
  } catch (err) {
    showError("Revoke Consent failed: " + err.message);
  }
}

function sendMediaState(camActive, micActive) {
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    const msg = { type: "media_state", session_id: state.sessionId };
    if (camActive !== null && camActive !== undefined) msg.camera_active = camActive;
    if (micActive !== null && micActive !== undefined) msg.microphone_active = micActive;
    try { state.ws.send(JSON.stringify(msg)); } catch (_) {}
  }
}

function connectWebSocket() {
  clearError();
  syncInputs();
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/live/${encodeURIComponent(state.sessionId)}`;
  if (state.wsHeartbeatTimer) {
    clearInterval(state.wsHeartbeatTimer);
    state.wsHeartbeatTimer = null;
  }
  if (state.ws) {
    state.wsManuallyClosed = true;
    state.ws.onopen = null;
    state.ws.onmessage = null;
    state.ws.onclose = null;
    state.ws.onerror = null;
    try { state.ws.close(); } catch (_) {}
    state.ws = null;
  }
  state.wsManuallyClosed = false;
  state.wsAuthenticated = false;
  document.getElementById("badge-ws").textContent = "WS: connecting...";
  document.getElementById("badge-ws").className = "pill warn";
  const ws = new WebSocket(url);
  state.ws = ws;
  ws.onopen = () => {
    document.getElementById("badge-ws").textContent = "WS: connected";
    document.getElementById("badge-ws").className = "pill ok";
    if (state.apiKey) {
      ws.send(JSON.stringify({ type: "auth", api_key: state.apiKey }));
    }
    ws.send(JSON.stringify({ type: "init", session_id: state.sessionId }));
    if (state.camStream || state.micStream) {
      sendMediaState(!!state.camStream, !!state.micStream);
    }
    if (state.wsHeartbeatTimer) clearInterval(state.wsHeartbeatTimer);
    state.wsHeartbeatTimer = setInterval(() => {
      if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        try { state.ws.send(JSON.stringify({ type: "heartbeat", session_id: state.sessionId })); } catch (_) {}
      }
    }, 25000);
  };
  ws.onerror = () => {
    document.getElementById("badge-ws").textContent = "WS: error";
    document.getElementById("badge-ws").className = "pill err";
    showError("WebSocket connection error on session " + state.sessionId);
  };
  ws.onclose = (evt) => {
    if (state.wsHeartbeatTimer) {
      clearInterval(state.wsHeartbeatTimer);
      state.wsHeartbeatTimer = null;
    }
    document.getElementById("badge-ws").textContent = evt.code === 4401 ? "WS: unauthorized" : "WS: disconnected";
    document.getElementById("badge-ws").className = "pill " + (evt.code === 4401 ? "err" : "warn");
    if (!state.wsManuallyClosed && evt.code === 4401) {
      showError("WebSocket authentication failed (4401): provide a valid X-API-Key in Settings.");
    }
  };
  ws.onmessage = (evt) => {
    try { handleWsMessage(JSON.parse(evt.data)); } catch (_) {}
  };
}

function handleWsMessage(msg) {
  if (msg.type === "observation" && msg.data) {
    if (msg.data.status === "consent_rejected") {
      state.consentGranted = false;
      stopCamera();
      stopMic();
      refreshConsentStatus();
      showError(msg.data.error || "Consent rejected by backend.");
    }
    renderObservation(msg.modality, msg.data);
  } else if (msg.type === "fusion" && msg.data) {
    renderObservation("fusion", msg.data);
  } else if (msg.type === "status" && msg.status === "consent_revoked") {
    state.consentGranted = false;
    state.sessionRevoked = true;
    stopCamera();
    stopMic();
    updateConsentControls();
  } else if (msg.type === "error") {
    showError("WS Error: " + (msg.error || JSON.stringify(msg)));
    document.getElementById("live-log").textContent = "ERROR: " + (msg.error || JSON.stringify(msg));
  }
}

function renderObservation(mod, d) {
  if (mod === "facial") {
    document.getElementById("res-face-dom").textContent = d.dominant_estimate || d.status;
    document.getElementById("res-face-conf").textContent = String(d.confidence ?? 0);
    document.getElementById("res-face-unc").textContent = String(d.uncertainty ?? 1);
    document.getElementById("res-face-lat").textContent = `${d.latency_ms ?? 0} ms`;
  } else if (mod === "speech") {
    document.getElementById("res-speech-dom").textContent = d.dominant_estimate || d.status;
    document.getElementById("res-speech-conf").textContent = String(d.confidence ?? 0);
    document.getElementById("res-speech-unc").textContent = String(d.uncertainty ?? 1);
    document.getElementById("res-speech-lat").textContent = `${d.latency_ms ?? 0} ms`;
  } else if (mod === "fusion") {
    document.getElementById("res-fusion-dom").textContent = d.dominant_estimate || "-";
    document.getElementById("res-fusion-conf").textContent = String(d.confidence ?? 0);
    document.getElementById("res-fusion-unc").textContent = String(d.uncertainty ?? 1);
    document.getElementById("res-fusion-lat").textContent = `${d.latency_ms ?? 0} ms`;
  }
  document.getElementById("live-log").textContent = JSON.stringify(d, null, 2);
}

async function enumerateMediaDevices() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) return;
  try {
    const devs = await navigator.mediaDevices.enumerateDevices();
    const camSel = document.getElementById("sel-cam");
    const micSel = document.getElementById("sel-mic");
    const prevCam = camSel.value;
    const prevMic = micSel.value;
    camSel.innerHTML = "";
    micSel.innerHTML = "";
    devs.forEach(d => {
      const opt = document.createElement("option");
      opt.value = d.deviceId;
      opt.textContent = d.label || `${d.kind} (${d.deviceId.slice(0, 8) || "default"})`;
      if (d.kind === "videoinput") camSel.appendChild(opt);
      if (d.kind === "audioinput") micSel.appendChild(opt);
    });
    if (prevCam) camSel.value = prevCam;
    if (prevMic) micSel.value = prevMic;
  } catch (_) {}
}

if (navigator.mediaDevices && typeof navigator.mediaDevices.addEventListener === "function") {
  navigator.mediaDevices.addEventListener("devicechange", enumerateMediaDevices);
}

function ensureActiveConsentForCapture() {
  syncInputs();
  if (state.sessionRevoked) {
    throw new Error("Session consent was revoked. Click 'New Session' and grant fresh explicit consent.");
  }
  if (!state.consentGranted || !state.consentReference) {
    throw new Error("Active explicit consent is required before capture or analysis. Click 'Grant Consent' first.");
  }
}

async function startCamera() {
  clearError();
  try {
    ensureActiveConsentForCapture();
  } catch (err) {
    showError(err.message);
    document.getElementById("live-log").textContent = err.message;
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError("Webcam API unavailable in current browser context.");
    return;
  }
  if (state.camStream) return;
  try {
    document.getElementById("live-cam-stats").textContent = "Requesting permission...";
    const [w, h] = document.getElementById("cfg-res").value.split("x").map(Number);
    const devId = document.getElementById("sel-cam").value;
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { width: w, height: h, deviceId: devId ? { exact: devId } : undefined }
    });
    if (!state.consentGranted || state.sessionRevoked) {
      stream.getTracks().forEach(t => t.stop());
      throw new Error("Consent is no longer active; camera capture aborted.");
    }
    const videoEl = document.getElementById("webcam-video");
    videoEl.srcObject = stream;
    await videoEl.play();
    state.camStream = stream;
    stream.getVideoTracks().forEach(track => {
      track.onended = () => {
        stopCamera();
        document.getElementById("live-cam-stats").textContent = "Disconnected";
        showError("Webcam device disconnected.");
      };
    });
    await enumerateMediaDevices();
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) connectWebSocket();
    sendMediaState(true, null);
    const fps = Math.max(0.5, Number(document.getElementById("live-fps").value) || 2);
    document.getElementById("live-cam-stats").textContent = `Active @ ${fps} FPS (${w}x${h})`;
    if (state.camTimer) clearInterval(state.camTimer);
    state.camTimer = setInterval(captureAndSend, Math.round(1000 / fps));
    updateConsentControls();
  } catch (err) {
    stopCamera();
    const formatted = formatMediaError("Webcam", err);
    document.getElementById("live-cam-stats").textContent =
      (err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError"))
        ? "Permission Denied" : "Error";
    showError(formatted);
    document.getElementById("live-log").textContent = formatted;
  }
}

function stopCamera() {
  if (state.camTimer) { clearInterval(state.camTimer); state.camTimer = null; }
  if (state.camStream) {
    state.camStream.getTracks().forEach(t => { t.onended = null; t.stop(); });
    state.camStream = null;
  }
  document.getElementById("webcam-video").srcObject = null;
  document.getElementById("live-cam-stats").textContent = "Inactive";
  sendMediaState(false, null);
  updateConsentControls();
}

function captureAndSend() {
  if (state.paused || !state.consentGranted || state.sessionRevoked) return;
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN || !state.camStream) return;
  if (state.ws.bufferedAmount > 2 * 1024 * 1024) return;
  const video = document.getElementById("webcam-video");
  if (!video.videoWidth || !video.videoHeight) return;
  const canvas = document.getElementById("capture-canvas");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const frameData = canvas.toDataURL("image/jpeg", 0.85);
  state.ws.send(JSON.stringify({
    type: "frame",
    session_id: state.sessionId,
    consent_reference: state.consentReference,
    image_base64: frameData
  }));
}

function downsampleTo16k(input, sourceRate) {
  const targetRate = 16000;
  if (!sourceRate || sourceRate === targetRate) return input;
  const ratio = sourceRate / targetRate;
  const outLen = Math.max(1, Math.floor(input.length / ratio));
  const output = new Float32Array(outLen);
  for (let i = 0; i < outLen; i++) {
    const srcIdx = i * ratio;
    const idx0 = Math.floor(srcIdx);
    const idx1 = Math.min(input.length - 1, idx0 + 1);
    const frac = srcIdx - idx0;
    output[i] = input[idx0] * (1 - frac) + input[idx1] * frac;
  }
  return output;
}

async function startMic() {
  clearError();
  try {
    ensureActiveConsentForCapture();
  } catch (err) {
    showError(err.message);
    document.getElementById("live-log").textContent = err.message;
    return;
  }
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showError("Microphone API unavailable in current browser context.");
    return;
  }
  if (state.micStream) return;
  try {
    document.getElementById("mic-silence-badge").textContent = "(Requesting permission...)";
    const devId = document.getElementById("sel-mic").value;
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: { deviceId: devId ? { exact: devId } : undefined }
    });
    if (!state.consentGranted || state.sessionRevoked) {
      stream.getTracks().forEach(t => t.stop());
      throw new Error("Consent is no longer active; microphone capture aborted.");
    }
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const audioCtx = new AudioCtx();
    const src = audioCtx.createMediaStreamSource(stream);
    const proc = audioCtx.createScriptProcessor(4096, 1, 1);
    state.micStream = stream;
    state.audioCtx = audioCtx;
    state.audioSrcNode = src;
    state.audioProcNode = proc;
    stream.getAudioTracks().forEach(track => {
      track.onended = () => {
        stopMic();
        document.getElementById("mic-silence-badge").textContent = "(Disconnected)";
        showError("Microphone device disconnected.");
      };
    });
    await enumerateMediaDevices();
    if (!state.ws || state.ws.readyState !== WebSocket.OPEN) connectWebSocket();
    sendMediaState(null, true);
    let pcmChunks = [];
    let totalBufferedSamples = 0;
    const maxBufferedSamples = 32000;
    proc.onaudioprocess = (e) => {
      if (state.paused || !state.consentGranted || state.sessionRevoked) return;
      const raw = e.inputBuffer.getChannelData(0);
      const down = downsampleTo16k(raw, audioCtx.sampleRate || 16000);
      let sumSq = 0;
      const pcm = new Int16Array(down.length);
      for (let i = 0; i < down.length; i++) {
        const s = Math.max(-1, Math.min(1, down[i]));
        sumSq += s * s;
        pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      const rms = Math.sqrt(sumSq / down.length);
      document.getElementById("mic-level-bar").style.width = Math.min(100, Math.round(rms * 300)) + "%";
      document.getElementById("mic-silence-badge").textContent = rms < 0.006 ? "(Silence)" : "(Active)";
      pcmChunks.push(pcm);
      totalBufferedSamples += pcm.length;
      if (totalBufferedSamples > maxBufferedSamples) {
        const dropped = pcmChunks.shift();
        if (dropped) totalBufferedSamples -= dropped.length;
      }
      if (totalBufferedSamples >= 4000 && state.ws && state.ws.readyState === WebSocket.OPEN) {
        if (state.ws.bufferedAmount > 2 * 1024 * 1024) {
          pcmChunks = [];
          totalBufferedSamples = 0;
          return;
        }
        const merged = new Int16Array(totalBufferedSamples);
        let off = 0;
        pcmChunks.forEach(c => { merged.set(c, off); off += c.length; });
        pcmChunks = [];
        totalBufferedSamples = 0;
        const bytes = new Uint8Array(merged.buffer);
        let bin = "";
        for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
        state.ws.send(JSON.stringify({
          type: "audio",
          session_id: state.sessionId,
          consent_reference: state.consentReference,
          sample_rate: 16000,
          audio_base64: btoa(bin)
        }));
      }
    };
    src.connect(proc);
    proc.connect(audioCtx.destination);
    updateConsentControls();
  } catch (err) {
    stopMic();
    const formatted = formatMediaError("Microphone", err);
    document.getElementById("mic-silence-badge").textContent =
      (err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError"))
        ? "(Permission Denied)" : "(Error)";
    showError(formatted);
    document.getElementById("live-log").textContent = formatted;
  }
}

function stopMic() {
  if (state.audioProcNode) { try { state.audioProcNode.disconnect(); } catch (_) {} state.audioProcNode.onaudioprocess = null; state.audioProcNode = null; }
  if (state.audioSrcNode) { try { state.audioSrcNode.disconnect(); } catch (_) {} state.audioSrcNode = null; }
  if (state.audioCtx) { try { state.audioCtx.close(); } catch (_) {} state.audioCtx = null; }
  if (state.micStream) {
    state.micStream.getTracks().forEach(t => { t.onended = null; t.stop(); });
    state.micStream = null;
  }
  document.getElementById("mic-level-bar").style.width = "0%";
  document.getElementById("mic-silence-badge").textContent = "(Inactive)";
  sendMediaState(null, false);
  updateConsentControls();
}

function togglePauseLive() {
  state.paused = !state.paused;
  document.getElementById("btn-pause-live").textContent = state.paused ? "Resume Stream" : "Pause Stream";
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: state.paused ? "pause" : "resume", session_id: state.sessionId }));
  }
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(String(r.result).split(",")[1] || "");
    r.onerror = reject;
    r.readAsDataURL(file);
  });
}

async function analyzeImageUpload() {
  clearError();
  try {
    ensureActiveConsentForCapture();
    const f = document.getElementById("img-file").files[0];
    if (!f) throw new Error("Select an image file first.");
    const b64 = await fileToBase64(f);
    const data = await apiRequest("/api/v1/analyze/image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, modality: "facial", image_base64: b64 })
    });
    document.getElementById("img-result").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError(err.message);
    document.getElementById("img-result").textContent = "Error: " + err.message;
  }
}

async function analyzeAudioUpload() {
  clearError();
  try {
    ensureActiveConsentForCapture();
    const f = document.getElementById("aud-file").files[0];
    if (!f) throw new Error("Select a WAV/PCM file first.");
    const b64 = await fileToBase64(f);
    const data = await apiRequest("/api/v1/analyze/audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, modality: "speech", audio_base64: b64, sample_rate: 16000 })
    });
    document.getElementById("aud-result").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError(err.message);
    document.getElementById("aud-result").textContent = "Error: " + err.message;
  }
}

async function analyzeVideoUpload() {
  clearError();
  try {
    ensureActiveConsentForCapture();
    const f = document.getElementById("vid-file").files[0];
    if (!f) throw new Error("Select a video file first.");
    const b64 = await fileToBase64(f);
    const data = await apiRequest("/api/v1/analyze/video", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, video_base64: b64 })
    });
    document.getElementById("vid-result").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError(err.message);
    document.getElementById("vid-result").textContent = "Error: " + err.message;
  }
}

async function analyzeTextInput() {
  clearError();
  try {
    ensureActiveConsentForCapture();
    const text = document.getElementById("txt-input").value;
    const data = await apiRequest("/api/v1/analyze/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, text })
    });
    document.getElementById("txt-result").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError(err.message);
    document.getElementById("txt-result").textContent = "Error: " + err.message;
  }
}

async function analyzeMultimodalUpload() {
  clearError();
  try {
    ensureActiveConsentForCapture();
    const payload = { session_id: state.sessionId, consent_reference: state.consentReference, sample_rate: 16000 };
    const fi = document.getElementById("mm-img").files[0];
    const fa = document.getElementById("mm-aud").files[0];
    const txt = document.getElementById("mm-txt").value.trim();
    if (fi) payload.image_base64 = await fileToBase64(fi);
    if (fa) payload.audio_base64 = await fileToBase64(fa);
    if (txt) payload.text = txt;
    const data = await apiRequest("/api/v1/analyze/multimodal", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    document.getElementById("mm-result").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    showError(err.message);
    document.getElementById("mm-result").textContent = "Error: " + err.message;
  }
}

async function loadRegistry() {
  try {
    const data = await apiRequest("/api/v1/models");
    const rows = (data.models || []).map(m => `
      <tr>
        <td><strong>${m.name}</strong><br><code>${m.model_id}</code></td>
        <td>${m.modality}</td><td>${m.version}</td><td>${m.framework}</td>
        <td><code>${(m.sha256_checksum || "").slice(0, 16)}...</code></td>
        <td>${m.qualification_state}</td>
        <td><button class="btn" onclick="activateModel('${m.model_id}')">${m.activated ? "Activated" : "Activate"}</button></td>
      </tr>
    `).join("");
    document.getElementById("reg-table").innerHTML = `<table><tr><th>Model</th><th>Modality</th><th>Ver</th><th>Framework</th><th>SHA-256</th><th>State</th><th>Action</th></tr>${rows}</table>`;
  } catch (err) {
    showError("Model registry load failed: " + err.message);
  }
}

async function activateModel(id) {
  try {
    await apiRequest(`/api/v1/models/${encodeURIComponent(id)}/activate`, { method: "POST" });
    await loadRegistry();
  } catch (err) {
    showError(`Activation blocked for ${id}: ${err.message}`);
  }
}

async function loadEvaluations() {
  try {
    const data = await apiRequest("/api/v1/evaluation/reports");
    document.getElementById("eval-output").textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    document.getElementById("eval-output").textContent = "Error: " + err.message;
  }
}

async function loadDatasets() {
  try {
    const data = await apiRequest("/api/v1/datasets");
    const rows = (data.datasets || []).map(d => `
      <tr><td><strong>${d.name}</strong></td><td>${d.license}</td><td>${d.commercial_allowed}</td><td>${d.partition_strategy}</td><td><code>${d.repository_status}</code></td></tr>
    `).join("");
    document.getElementById("ds-table").innerHTML = `<table><tr><th>Dataset</th><th>License</th><th>Commercial</th><th>Split Policy</th><th>Status</th></tr>${rows}</table>`;
  } catch (err) {
    showError("Datasets load failed: " + err.message);
  }
}

async function loadSessions() {
  try {
    const data = await apiRequest("/api/v1/live/sessions");
    const rows = (data.sessions || []).map(s => `
      <tr><td><code>${s.session_id}</code></td><td>${s.owner_id}</td><td>${s.state}</td><td>${s.frame_count}/${s.audio_count}/${s.text_count}</td>
      <td><button class="btn danger" onclick="closeSession('${s.session_id}')">Close</button></td></tr>
    `).join("");
    document.getElementById("sess-table").innerHTML = `<table><tr><th>Session ID</th><th>Owner</th><th>State</th><th>F/A/T</th><th>Action</th></tr>${rows}</table>`;
  } catch (err) {
    showError("Sessions load failed: " + err.message);
  }
}

async function createNewSession() {
  try {
    const sid = document.getElementById("new-sess-id").value.trim() || undefined;
    await apiRequest("/api/v1/live/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sid })
    });
    await loadSessions();
  } catch (err) {
    showError("Create session failed: " + err.message);
  }
}

async function closeSession(sid) {
  try {
    await apiRequest(`/api/v1/live/sessions/${encodeURIComponent(sid)}`, { method: "DELETE" });
    await loadSessions();
  } catch (err) {
    showError("Close session failed: " + err.message);
  }
}

async function loadDiagnostics() {
  try {
    const [diag, devs] = await Promise.all([
      apiRequest("/api/v1/diagnostics"),
      apiRequest("/api/v1/devices")
    ]);
    document.getElementById("diag-output").textContent = JSON.stringify({ diagnostics: diag, verified_devices: devs }, null, 2);
  } catch (err) {
    document.getElementById("diag-output").textContent = "Error: " + err.message;
  }
}

window.addEventListener("load", () => {
  document.getElementById("live-session-id").value = state.sessionId;
  document.getElementById("live-consent-ref").value = "";
  updateConsentControls();
  refreshOverview();
  refreshConsentStatus();
  enumerateMediaDevices();
});
</script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Return the complete enterprise 15-view ERS HTML console."""
    return DASHBOARD_HTML
