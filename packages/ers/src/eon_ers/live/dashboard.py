"""Enterprise-grade responsive 15-view UI dashboard for OVIC EON ERS.

Preserves Epistemic Modesty, Consent Isolation, Unvalidated Model Disclosure,
and real browser WebRTC/AudioContext capture streaming directly to the backend.
"""

from __future__ import annotations

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
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
  button.btn:disabled { opacity: 0.5; cursor: not-allowed; }
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
      <span class="pill" id="badge-consent">Consent: inactive</span>
    </div>
    <div class="badges">
      <span class="muted">Invariant: <code>is_definitive_claim = False</code> (No Robot Actuation)</span>
      <button class="btn" id="btn-theme" aria-label="Toggle Light/Dark Theme">Theme</button>
    </div>
  </header>

  <div class="banner" id="qual-banner">
    <strong>Epistemic &amp; Scientific Notice:</strong> ERS estimates observable signals only and never asserts inner truth. Unvalidated baseline models remain marked <code>MODEL_UNVALIDATED</code> until external benchmark qualification succeeds.
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
        <div class="card-title">Live Consent &amp; Session Controls</div>
        <div class="grid-3">
          <div><label for="live-session-id">Session ID</label><input id="live-session-id" type="text" value="live-console-01" /></div>
          <div><label for="live-consent-ref">Consent Reference Token</label><input id="live-consent-ref" type="text" value="explicit-user-consent-token" /></div>
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
          <button class="btn primary" onclick="registerConsent()">Grant Consent</button>
          <button class="btn danger" onclick="revokeConsent()">Revoke Consent</button>
          <button class="btn primary" id="btn-start-cam" onclick="startCamera()">Start Webcam</button>
          <button class="btn" id="btn-stop-cam" onclick="stopCamera()" disabled>Stop Webcam</button>
          <button class="btn primary" id="btn-start-mic" onclick="startMic()">Start Microphone</button>
          <button class="btn" id="btn-stop-mic" onclick="stopMic()" disabled>Stop Microphone</button>
          <button class="btn" onclick="connectWebSocket()">Reconnect WS</button>
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
            <div class="muted" style="margin-bottom:4px;">Microphone RMS Energy Level <span id="mic-silence-badge"></span></div>
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
          <div style="margin-top:10px;"><label>Live Stream Output Log</label><pre id="live-log">Awaiting explicit consent and media activation...</pre></div>
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
        <pre id="img-result">Select an image file and click Analyze Image.</pre>
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
        <pre id="aud-result">Select a WAV file and click Analyze Audio.</pre>
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
        <pre id="vid-result">Select a RIFF AVI (MJPEG) or animated GIF/WEBP file and click Analyze Video.</pre>
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
        <pre id="txt-result">Enter UTF-8 text and click Analyze Text.</pre>
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
        <pre id="mm-result">Provide any 1, 2, or 3 modalities and run fusion.</pre>
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
        <div class="card-title">CPU Diagnostics &amp; Latency Telemetry <button class="btn" onclick="loadDiagnostics()">Refresh</button></div>
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
            <input id="cfg-api-key" type="password" placeholder="Optional API key when auth is enabled" onchange="state.apiKey=this.value" />
          </div>
          <div>
            <label for="cfg-res">Webcam Resolution Width</label>
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
          <li>Raw webcam frames, microphone PCM buffers, video bytes, and text inputs are scrubbed from volatile memory immediately after inference (`zero_disk_retention = True`).</li>
          <li>No permanent facial recognition embeddings are created; session face IDs are strictly ephemeral spatial indices.</li>
          <li>Actuator/motion safety interlocks block robot movement commands; `is_definitive_claim = False` is immutable across every contract.</li>
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
const state = {
  sessionId: "live-console-01",
  consentReference: "explicit-user-consent-token",
  apiKey: "",
  ws: null,
  camStream: null,
  micStream: null,
  audioCtx: null,
  camTimer: null,
  paused: false,
  consentGranted: false
};

function apiHeaders(extra = {}) {
  const h = { ...extra };
  if (state.apiKey) h["X-API-Key"] = state.apiKey;
  return h;
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
  state.sessionId = document.getElementById("live-session-id").value.trim() || "live-console-01";
  state.consentReference = document.getElementById("live-consent-ref").value.trim();
}

async function fetchModelStatus() {
  const res = await fetch("/api/models", { headers: apiHeaders() });
  const data = await res.json();
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
    const [hRes, rRes, dRes] = await Promise.all([
      fetch("/health", { headers: apiHeaders() }),
      fetch("/ready", { headers: apiHeaders() }),
      fetch("/api/v1/diagnostics", { headers: apiHeaders() })
    ]);
    const h = await hRes.json();
    const r = await rRes.json();
    const d = await dRes.json();
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
    document.getElementById("ov-health").textContent = "ERROR";
  }
}

async function registerConsent() {
  syncInputs();
  const res = await fetch("/api/consent/register", {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference })
  });
  const data = await res.json();
  state.consentGranted = !!data.has_active_consent;
  const bc = document.getElementById("badge-consent");
  bc.textContent = state.consentGranted ? "Consent: ACTIVE" : "Consent: INACTIVE";
  bc.className = "pill " + (state.consentGranted ? "ok" : "err");
  if (!state.ws || state.ws.readyState !== WebSocket.OPEN) connectWebSocket();
}

async function revokeConsent() {
  syncInputs();
  await fetch("/api/consent/revoke", {
    method: "POST",
    headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId })
  });
  state.consentGranted = false;
  document.getElementById("badge-consent").textContent = "Consent: REVOKED";
  document.getElementById("badge-consent").className = "pill err";
  stopCamera();
  stopMic();
  if (state.ws && state.ws.readyState === WebSocket.OPEN) {
    state.ws.send(JSON.stringify({ type: "revoke", session_id: state.sessionId }));
  }
}

async function refreshConsentStatus() {
  syncInputs();
  const res = await fetch(`/api/consent/status/${encodeURIComponent(state.sessionId)}`, { headers: apiHeaders() });
  document.getElementById("privacy-status").textContent = JSON.stringify(await res.json(), null, 2);
}

function connectWebSocket() {
  syncInputs();
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}/ws/live/${encodeURIComponent(state.sessionId)}`;
  if (state.ws) try { state.ws.close(); } catch (_) {}
  const ws = new WebSocket(url);
  state.ws = ws;
  ws.onopen = () => {
    document.getElementById("badge-ws").textContent = "WS: connected";
    document.getElementById("badge-ws").className = "pill ok";
    ws.send(JSON.stringify({
      type: "init",
      session_id: state.sessionId,
      consent_reference: state.consentReference
    }));
  };
  ws.onclose = () => {
    document.getElementById("badge-ws").textContent = "WS: disconnected";
    document.getElementById("badge-ws").className = "pill warn";
  };
  ws.onmessage = (evt) => handleWsMessage(JSON.parse(evt.data));
}

function handleWsMessage(msg) {
  if (msg.type === "observation" && msg.data) {
    renderObservation(msg.modality, msg.data);
  } else if (msg.type === "fusion" && msg.data) {
    renderObservation("fusion", msg.data);
  } else if (msg.type === "error") {
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
  const devs = await navigator.mediaDevices.enumerateDevices();
  const camSel = document.getElementById("sel-cam");
  const micSel = document.getElementById("sel-mic");
  camSel.innerHTML = ""; micSel.innerHTML = "";
  devs.forEach(d => {
    const opt = document.createElement("option");
    opt.value = d.deviceId; opt.textContent = d.label || `${d.kind} (${d.deviceId.slice(0,8)})`;
    if (d.kind === "videoinput") camSel.appendChild(opt);
    if (d.kind === "audioinput") micSel.appendChild(opt);
  });
}

async function startCamera() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    document.getElementById("live-log").textContent = "Webcam API unavailable in current browser context.";
    return;
  }
  const [w, h] = document.getElementById("cfg-res").value.split("x").map(Number);
  const devId = document.getElementById("sel-cam").value;
  state.camStream = await navigator.mediaDevices.getUserMedia({
    video: { width: w, height: h, deviceId: devId ? { exact: devId } : undefined }
  });
  document.getElementById("webcam-video").srcObject = state.camStream;
  document.getElementById("btn-start-cam").disabled = true;
  document.getElementById("btn-stop-cam").disabled = false;
  await enumerateMediaDevices();
  const fps = Math.max(0.5, Number(document.getElementById("live-fps").value) || 2);
  document.getElementById("live-cam-stats").textContent = `Streaming @ ${fps} FPS (${w}x${h})`;
  if (state.camTimer) clearInterval(state.camTimer);
  state.camTimer = setInterval(captureAndSend, Math.round(1000 / fps));
}

function stopCamera() {
  if (state.camTimer) { clearInterval(state.camTimer); state.camTimer = null; }
  if (state.camStream) { state.camStream.getTracks().forEach(t => t.stop()); state.camStream = null; }
  document.getElementById("webcam-video").srcObject = null;
  document.getElementById("btn-start-cam").disabled = false;
  document.getElementById("btn-stop-cam").disabled = true;
  document.getElementById("live-cam-stats").textContent = "Inactive";
}

function captureAndSend() {
  if (state.paused || !state.ws || state.ws.readyState !== WebSocket.OPEN || !state.camStream) return;
  const video = document.getElementById("webcam-video");
  if (!video.videoWidth || !video.videoHeight) return;
  const canvas = document.getElementById("capture-canvas");
  canvas.width = video.videoWidth; canvas.height = video.videoHeight;
  canvas.getContext("2d").drawImage(video, 0, 0);
  const frameData = canvas.toDataURL("image/jpeg", 0.85);
  state.ws.send(JSON.stringify({
    type: "frame",
    session_id: state.sessionId,
    consent_reference: state.consentReference,
    image_base64: frameData
  }));
}

async function startMic() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    document.getElementById("live-log").textContent = "Microphone API unavailable in current browser context.";
    return;
  }
  const devId = document.getElementById("sel-mic").value;
  state.micStream = await navigator.mediaDevices.getUserMedia({
    audio: { deviceId: devId ? { exact: devId } : undefined }
  });
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  state.audioCtx = new AudioCtx({ sampleRate: 16000 });
  const src = state.audioCtx.createMediaStreamSource(state.micStream);
  const proc = state.audioCtx.createScriptProcessor(4096, 1, 1);
  let pcmChunks = [];
  proc.onaudioprocess = (e) => {
    if (state.paused) return;
    const ch = e.inputBuffer.getChannelData(0);
    let sumSq = 0;
    const pcm = new Int16Array(ch.length);
    for (let i = 0; i < ch.length; i++) {
      const s = Math.max(-1, Math.min(1, ch[i]));
      sumSq += s * s;
      pcm[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    const rms = Math.sqrt(sumSq / ch.length);
    document.getElementById("mic-level-bar").style.width = Math.min(100, Math.round(rms * 300)) + "%";
    document.getElementById("mic-silence-badge").textContent = rms < 0.006 ? "(Silence)" : "(Active)";
    pcmChunks.push(pcm);
    if (pcmChunks.length >= 4 && state.ws && state.ws.readyState === WebSocket.OPEN) {
      const merged = new Int16Array(pcmChunks.reduce((a, c) => a + c.length, 0));
      let off = 0;
      pcmChunks.forEach(c => { merged.set(c, off); off += c.length; });
      pcmChunks = [];
      const bytes = new Uint8Array(merged.buffer);
      let bin = "";
      for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
      state.ws.send(JSON.stringify({
        type: "audio",
        session_id: state.sessionId,
        consent_reference: state.consentReference,
        sample_rate: state.audioCtx.sampleRate || 16000,
        audio_base64: btoa(bin)
      }));
    }
  };
  src.connect(proc);
  proc.connect(state.audioCtx.destination);
  document.getElementById("btn-start-mic").disabled = true;
  document.getElementById("btn-stop-mic").disabled = false;
}

function stopMic() {
  if (state.audioCtx) { try { state.audioCtx.close(); } catch (_) {} state.audioCtx = null; }
  if (state.micStream) { state.micStream.getTracks().forEach(t => t.stop()); state.micStream = null; }
  document.getElementById("mic-level-bar").style.width = "0%";
  document.getElementById("btn-start-mic").disabled = false;
  document.getElementById("btn-stop-mic").disabled = true;
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
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  const f = document.getElementById("img-file").files[0];
  if (!f) return;
  const b64 = await fileToBase64(f);
  const res = await fetch("/api/v1/analyze/image", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, modality: "facial", image_base64: b64 })
  });
  document.getElementById("img-result").textContent = JSON.stringify(await res.json(), null, 2);
}

async function analyzeAudioUpload() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  const f = document.getElementById("aud-file").files[0];
  if (!f) return;
  const b64 = await fileToBase64(f);
  const res = await fetch("/api/v1/analyze/audio", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, modality: "speech", audio_base64: b64, sample_rate: 16000 })
  });
  document.getElementById("aud-result").textContent = JSON.stringify(await res.json(), null, 2);
}

async function analyzeVideoUpload() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  const f = document.getElementById("vid-file").files[0];
  if (!f) return;
  const b64 = await fileToBase64(f);
  const res = await fetch("/api/v1/analyze/video", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, video_base64: b64 })
  });
  document.getElementById("vid-result").textContent = JSON.stringify(await res.json(), null, 2);
}

async function analyzeTextInput() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  const text = document.getElementById("txt-input").value;
  const res = await fetch("/api/v1/analyze/text", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: state.sessionId, consent_reference: state.consentReference, text })
  });
  document.getElementById("txt-result").textContent = JSON.stringify(await res.json(), null, 2);
}

async function analyzeMultimodalUpload() {
  syncInputs();
  if (!state.consentGranted) await registerConsent();
  const payload = { session_id: state.sessionId, consent_reference: state.consentReference, sample_rate: 16000 };
  const fi = document.getElementById("mm-img").files[0];
  const fa = document.getElementById("mm-aud").files[0];
  const txt = document.getElementById("mm-txt").value.trim();
  if (fi) payload.image_base64 = await fileToBase64(fi);
  if (fa) payload.audio_base64 = await fileToBase64(fa);
  if (txt) payload.text = txt;
  const res = await fetch("/api/v1/analyze/multimodal", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload)
  });
  document.getElementById("mm-result").textContent = JSON.stringify(await res.json(), null, 2);
}

async function loadRegistry() {
  const res = await fetch("/api/v1/models", { headers: apiHeaders() });
  const data = await res.json();
  const rows = (data.models || []).map(m => `
    <tr>
      <td><strong>${m.name}</strong><br><code>${m.model_id}</code></td>
      <td>${m.modality}</td><td>${m.version}</td><td>${m.framework}</td>
      <td><code>${(m.sha256_checksum || "").slice(0,16)}...</code></td>
      <td>${m.qualification_state}</td>
      <td><button class="btn" onclick="activateModel('${m.model_id}')">${m.activated ? "Activated" : "Activate"}</button></td>
    </tr>
  `).join("");
  document.getElementById("reg-table").innerHTML = `<table><tr><th>Model</th><th>Modality</th><th>Ver</th><th>Framework</th><th>SHA-256</th><th>State</th><th>Action</th></tr>${rows}</table>`;
}

async function activateModel(id) {
  const res = await fetch(`/api/v1/models/${encodeURIComponent(id)}/activate`, { method: "POST", headers: apiHeaders() });
  const data = await res.json();
  alert(res.ok ? `Activated ${id}` : `Activation Blocked (${res.status}): ${JSON.stringify(data.detail || data)}`);
  loadRegistry();
}

async function loadEvaluations() {
  const res = await fetch("/api/v1/evaluation/reports", { headers: apiHeaders() });
  document.getElementById("eval-output").textContent = JSON.stringify(await res.json(), null, 2);
}

async function loadDatasets() {
  const res = await fetch("/api/v1/datasets", { headers: apiHeaders() });
  const data = await res.json();
  const rows = (data.datasets || []).map(d => `
    <tr><td><strong>${d.name}</strong></td><td>${d.license}</td><td>${d.commercial_allowed}</td><td>${d.partition_strategy}</td><td><code>${d.repository_status}</code></td></tr>
  `).join("");
  document.getElementById("ds-table").innerHTML = `<table><tr><th>Dataset</th><th>License</th><th>Commercial</th><th>Split Policy</th><th>Status</th></tr>${rows}</table>`;
}

async function loadSessions() {
  const res = await fetch("/api/v1/live/sessions", { headers: apiHeaders() });
  const data = await res.json();
  const rows = (data.sessions || []).map(s => `
    <tr><td><code>${s.session_id}</code></td><td>${s.owner_id}</td><td>${s.state}</td><td>${s.frame_count}/${s.audio_count}/${s.text_count}</td>
    <td><button class="btn danger" onclick="closeSession('${s.session_id}')">Close</button></td></tr>
  `).join("");
  document.getElementById("sess-table").innerHTML = `<table><tr><th>Session ID</th><th>Owner</th><th>State</th><th>F/A/T</th><th>Action</th></tr>${rows}</table>`;
}

async function createNewSession() {
  const sid = document.getElementById("new-sess-id").value.trim() || undefined;
  await fetch("/api/v1/live/sessions", {
    method: "POST", headers: apiHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ session_id: sid })
  });
  loadSessions();
}

async function closeSession(sid) {
  await fetch(`/api/v1/live/sessions/${encodeURIComponent(sid)}`, { method: "DELETE", headers: apiHeaders() });
  loadSessions();
}

async function loadDiagnostics() {
  const res = await fetch("/api/v1/diagnostics", { headers: apiHeaders() });
  document.getElementById("diag-output").textContent = JSON.stringify(await res.json(), null, 2);
}

window.addEventListener("load", () => { refreshOverview(); enumerateMediaDevices(); });
</script>
</body>
</html>
"""


def get_dashboard_html() -> str:
    """Return the complete enterprise 15-view ERS HTML console."""
    return DASHBOARD_HTML
