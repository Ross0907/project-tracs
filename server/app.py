from flask import Flask, render_template_string, request, send_file
import os
from werkzeug.utils import secure_filename
from pathlib import Path
import uuid
import tempfile
import sys

# Ensure we can import the image_processing module from project root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

analyze_dent = None  # lazy-imported in /process to avoid startup failures
try:
  from flask_cors import CORS
except Exception:
  CORS = None

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB limit
UPLOAD_ROOT = Path(tempfile.gettempdir()) / "tracs_uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)

# Allow CORS for the frontend (Vercel/local). FRONTEND_ORIGINS can be comma-separated.
if CORS is not None:
  origins_env = os.getenv('FRONTEND_ORIGINS', 'http://localhost:8080,https://*.vercel.app')
  origins = [o.strip() for o in origins_env.split(',') if o.strip()]
  CORS(app, resources={r"/*": {"origins": origins}})

PAGE_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>TRACS – Image Processing POC</title>
    <style>
      :root {
        --bg: #0b1220; --panel: #0f172a; --muted: #94a3b8; --border: #243040;
        --accent: #22d3ee; --primary: #38bdf8; --ring: rgba(34,211,238,0.25);
      }
      * { box-sizing: border-box; }
      body { font-family: Inter, ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, "Apple Color Emoji", "Segoe UI Emoji"; margin: 0; background: var(--bg); color: #e6e9ef; }
      .header {
        background: linear-gradient(120deg, rgba(56,189,248,0.12), rgba(34,211,238,0.10) 60%, transparent);
        border-bottom: 1px solid #16324d; padding: 28px 0; margin-bottom: 8px;
      }
      .container { max-width: 1100px; margin: 0 auto; padding: 0 24px 24px; }
      h1 { margin: 0; font-size: 28px; letter-spacing: 0.2px; }
      .sub { color: var(--muted); margin-top: 6px; }
      .notice { background: rgba(255, 193, 7, 0.12); color: #ffd166; border: 1px solid rgba(255, 193, 7, 0.28); padding: 10px 14px; border-radius: 10px; margin: 16px 0; }
      .card { background: rgba(13, 17, 23, 0.78); border: 1px solid rgba(148, 163, 184, 0.16); border-radius: 14px; padding: 16px; box-shadow: 0 6px 20px rgba(0,0,0,0.25); }
      .row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
      .layout { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; align-items: start; }
      .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
      .panel h3 { margin: 0 0 10px; font-size: 16px; }
      label { display: block; margin-bottom: 8px; font-weight: 600; color: var(--muted); }
      input[type=file] { width: 100%; padding: 10px; background: #0b1117; border: 1px solid #1f2a38; color: #dce4ee; border-radius: 10px; outline: none; }
      input[type=file]:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--ring); }
      button { background: linear-gradient(180deg, var(--primary), #1890d5); color: #06131e; border: none; padding: 10px 16px; border-radius: 10px; cursor: pointer; font-weight: 700; letter-spacing: .2px; }
      button:hover { filter: brightness(1.05); }
      button:disabled { opacity: 0.6; cursor: not-allowed; }
      .actions { margin-top: 16px; display:flex; gap: 10px; align-items:center; }
  .result { margin-top: 12px; }
      .result img { max-width: 100%; border-radius: 12px; border: 1px solid #223040; background: #0b1117; }
      .small { color: var(--muted); font-size: 12px; }
      /* Camera additions */
      .cam { display: grid; gap: 10px; }
      .cam-controls { display:flex; gap: 10px; align-items:center; flex-wrap: wrap; }
  .cam-wrap { position: relative; background: #0b1117; border: 1px solid #1f2a38; border-radius: 12px; overflow: hidden; }
  .calib-overlay { position:absolute; inset:0; cursor: crosshair; touch-action:none; }
      video#cam { width: 100%; max-height: 360px; display:block; }
  video#camAuto { width: 100%; max-height: 360px; display:block; }
      img.preview { max-width: 100%; border-radius: 8px; border: 1px solid #223040; background: #0b1117; }
      select#cameraSelect { background: #0b1117; color: #dce4ee; border: 1px solid #1f2a38; border-radius: 8px; padding: 8px; }
      .hint { color: var(--muted); font-size: 12px; margin-top: -4px; }
  .auto-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: center; }
    </style>
  </head>
  <body>
    <div class="header">
      <div class="container">
        <h1>TRACS – Analysis Console</h1>
        <div class="sub">Clean profile comparison with deviation metrics</div>
      </div>
    </div>
    <div class="container">
      <div class="notice"><strong>POC</strong> — This is a rudimentary proof of concept, work in progress.</div>
      <div class="card">
        <form id="form" method="post" enctype="multipart/form-data" action="/process">
          <div class="row">
            <div>
              <label>Image 1 — With defects (dented)</label>
              <input type="file" name="dented" accept="image/*" required />
            </div>
            <div>
              <label>Image 2 — Without defects (perfect)</label>
              <input type="file" name="perfect" accept="image/*" required />
            </div>
          </div>

          <div class="panel cam" style="margin-top:16px;">
            <h3>Camera setup</h3>
            <div class="hint">Start your camera. The first frame can be used as the baseline (perfect), then frames are captured automatically every 5s for comparison.</div>
            <div class="cam-controls">
              <select id="cameraSelect" aria-label="Choose camera"></select>
              <button type="button" id="startCam">Start camera</button>
              <button type="button" id="stopCam" disabled>Stop</button>
            </div>
            <div class="cam-wrap">
              <video id="cam" autoplay playsinline></video>
              <canvas id="canvas" style="display:none"></canvas>
            </div>
            <div class="actions">
              <button type="button" id="captureDented" disabled>Capture dented</button>
              <button type="button" id="capturePerfect" disabled>Capture perfect</button>
              <span class="small">Tip: retake as needed; last capture is used.</span>
            </div>
            <div class="row">
              <div>
                <label>Preview — dented</label>
                <img id="previewDented" class="preview" alt="Dented preview" />
              </div>
              <div>
                <label>Preview — perfect</label>
                <img id="previewPerfect" class="preview" alt="Perfect preview" />
              </div>
            </div>
          </div>
          <div class="panel" style="margin-top:16px;">
            <h3>Auto-check (baseline + live camera)</h3>
            <div class="hint">First frame becomes the baseline (perfect) if none is chosen. Then a frame is captured every 5 seconds and compared to that baseline. Live feed on right; last captured frame on left. Use the calibration to convert pixels to millimeters.</div>
            <div class="actions" style="margin-top:8px; gap:8px;">
              <span class="small">Interval: 5s</span>
              <label for="mmPerPx" class="small">Scale (mm/px)</label>
              <input id="mmPerPx" type="number" value="1" step="0.01" min="0" style="width:90px; padding:6px 8px; background:#0b1117; border:1px solid #1f2a38; color:#dce4ee; border-radius:8px;" />
              <label for="fovMm" class="small">FOV height (mm)</label>
              <input id="fovMm" type="number" value="480" step="1" min="1" style="width:100px; padding:6px 8px; background:#0b1117; border:1px solid #1f2a38; color:#dce4ee; border-radius:8px;" />
              <button type="button" id="setScaleFov">Set scale from FOV</button>
              <button type="button" id="calibrateLine">Calibrate (2 points)</button>
              <button type="button" id="resetScale" title="Unlock and revert to auto scale">Reset scale</button>
              <button type="button" id="autoStart">Start Auto Check</button>
              <button type="button" id="autoStop" disabled>Stop</button>
              <span id="autoStatus" class="small">Idle</span>
            </div>
            <div class="auto-grid" style="margin-top:10px;">
              <div>
                <label class="small">Last captured frame</label>
                <img id="previewAuto" class="preview" alt="Last auto-captured frame" />
              </div>
              <div>
                <label class="small">Live video feed</label>
                <div class="cam-wrap">
                  <video id="camAuto" autoplay playsinline muted></video>
                  <canvas id="calibCanvas" class="calib-overlay" style="display:none"></canvas>
                </div>
              </div>
            </div>
          </div>

            <div style="margin-top:12px; display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
              <label class="small">Alignment:</label>
              <select id="alignMode" name="align_mode" style="background:#0b1117; color:#dce4ee; border:1px solid #1f2a38; border-radius:8px; padding:6px;">
                <option value="ransac">RANSAC+Similarity</option>
                <option value="icp">ICP (refine)</option>
                <option value="piecewise">Piecewise (fallback)</option>
              </select>
              <label class="small">Inlier px:</label>
              <input id="inlierPx" name="inlier_px" type="number" value="25" step="1" style="width:90px; padding:6px 8px; background:#0b1117; border:1px solid #1f2a38; color:#dce4ee; border-radius:8px;" />
              <label class="small" title="Allow similarity scaling (uniform).">Allow scale:</label>
              <input id="allowScale" name="allow_scale" type="checkbox" checked />
              <label class="small" title="Return a debug image overlaying matches and inliers.">Debug visual:</label>
              <input id="debugVisual" name="debug_visual" type="checkbox" />
              <div class="actions">
                <button type="submit">Run Analysis</button>
                <span class="small">Max 32MB per image</span>
              </div>
            </div>
        </form>
        <div class="layout" style="margin-top:12px;">
          <div class="panel">
            <div id="result" class="result"></div>
          </div>
          <div class="panel">
            <h3>Deviation details</h3>
            <div id="details" class="small">Upload images and run analysis…</div>
          </div>
        </div>

        <div class="panel" style="margin-top:16px;">
          <h3>WebUSB (optional)</h3>
          <div class="hint">Connect supported USB devices for future automation. Most webcams are not accessible via WebUSB; use the Camera capture above for images.</div>
          <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap; margin-top:8px;">
            <label for="vid" class="small">vendorId (hex)</label>
            <input id="vid" placeholder="0x2341" style="width:110px; padding:6px 8px; background:#0b1117; border:1px solid #1f2a38; color:#dce4ee; border-radius:8px;" />
            <label for="pid" class="small">productId (hex, optional)</label>
            <input id="pid" placeholder="0x0001" style="width:110px; padding:6px 8px; background:#0b1117; border:1px solid #1f2a38; color:#dce4ee; border-radius:8px;" />
            <button type="button" id="connectUsb">Connect USB</button>
            <button type="button" id="disconnectUsb" disabled>Disconnect</button>
          </div>
          <pre id="usbInfo" class="small" style="margin-top:10px; white-space:pre-wrap; background:#0b1117; border:1px solid #1f2a38; padding:10px; border-radius:8px; min-height:44px;"></pre>
        </div>
      </div>
    </div>

    <script>
      // DOM refs
      const form = document.getElementById('form');
      const result = document.getElementById('result');
      const details = document.getElementById('details');
      const startCamBtn = document.getElementById('startCam');
      const stopCamBtn = document.getElementById('stopCam');
      const captureDentedBtn = document.getElementById('captureDented');
      const capturePerfectBtn = document.getElementById('capturePerfect');
      const video = document.getElementById('cam');
  const canvas = document.getElementById('canvas');
  const camAuto = document.getElementById('camAuto');
  const calibCanvas = document.getElementById('calibCanvas');
    const cameraSelect = document.getElementById('cameraSelect');
      const inputDented = document.querySelector('input[name="dented"]');
      const inputPerfect = document.querySelector('input[name="perfect"]');
  const previewDented = document.getElementById('previewDented');
  const previewPerfect = document.getElementById('previewPerfect');
  const autoStartBtn = document.getElementById('autoStart');
  const autoStopBtn = document.getElementById('autoStop');
  // fixed interval = 5s
  const autoStatus = document.getElementById('autoStatus');
  const previewAuto = document.getElementById('previewAuto');
  const mmPerPxInput = document.getElementById('mmPerPx');
  const fovMmInput = document.getElementById('fovMm');
  const setScaleFovBtn = document.getElementById('setScaleFov');
  const calibrateLineBtn = document.getElementById('calibrateLine');
  const resetScaleBtn = document.getElementById('resetScale');

  let currentStream = null;
  let autoTimer = null;
  let autoBusy = false;

      async function listCameras() {
        if (!navigator.mediaDevices?.enumerateDevices) return;
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const cams = devices.filter(d => d.kind === 'videoinput');
          cameraSelect.innerHTML = '';
          cams.forEach((cam, idx) => {
            const opt = document.createElement('option');
            opt.value = cam.deviceId;
            opt.textContent = cam.label || `Camera ${idx + 1}`;
            cameraSelect.appendChild(opt);
          });
        } catch (e) { console.warn('enumerateDevices error', e); }
      }

  let userLockedScale = false; // set to true when user manually calibrates
  const LS_KEY_SCALE = 'tracs_mm_per_px';
  const LS_KEY_LOCK = 'tracs_scale_locked';

      function updateScaleFromStream() {
        try {
          if (!currentStream) return;
          const track = currentStream.getVideoTracks()[0];
          const settings = track?.getSettings?.() || {};
          const h = settings.height || video.videoHeight || 0;
          if (userLockedScale) return; // don't override manual calibration
          if (h > 0 && mmPerPxInput) {
            // Default heuristic: assume 1 px = 1 mm at 480p; scale ∝ 1/height
            const mmPerPx = 480 / h;
            if (Number.isFinite(mmPerPx) && mmPerPx > 0) {
              mmPerPxInput.value = mmPerPx.toFixed(3);
            }
          }
        } catch {}
      }

      async function startCamera() {
        try {
          stopCamera();
          const deviceId = cameraSelect.value || undefined;
          const constraints = {
            video: deviceId ? { deviceId: { exact: deviceId } } : {
              facingMode: { ideal: 'environment' },
              width: { ideal: 1920 },
              height: { ideal: 1080 }
            },
            audio: false
          };
          const stream = await navigator.mediaDevices.getUserMedia(constraints);
          currentStream = stream;
          video.srcObject = stream;
          if (camAuto) {
            camAuto.srcObject = stream;
            // size overlay canvas to video client size
            camAuto.onloadedmetadata = () => {
              setTimeout(() => {
                if (!calibCanvas) return;
                calibCanvas.width = camAuto.videoWidth;
                calibCanvas.height = camAuto.videoHeight;
                calibCanvas.style.width = camAuto.clientWidth + 'px';
                calibCanvas.style.height = camAuto.clientHeight + 'px';
              }, 100);
            };
          }
          // Wait a microtask to ensure metadata is ready, then compute default scale
          setTimeout(updateScaleFromStream, 200);
          startCamBtn.disabled = true;
          stopCamBtn.disabled = false;
          captureDentedBtn.disabled = false;
          capturePerfectBtn.disabled = false;
        } catch (e) {
          alert('Unable to access camera: ' + (e?.message || e));
          console.error(e);
        }
      }

      function stopCamera() {
        if (currentStream) {
          currentStream.getTracks().forEach(t => t.stop());
          currentStream = null;
        }
        startCamBtn.disabled = false;
        stopCamBtn.disabled = true;
        captureDentedBtn.disabled = true;
        capturePerfectBtn.disabled = true;
  video.srcObject = null;
  if (camAuto) camAuto.srcObject = null;
      }

      async function captureToInput(target) {
        if (!currentStream) { alert('Start the camera first.'); return; }
        const track = currentStream.getVideoTracks()[0];
        const settings = track.getSettings();
        const w = settings.width || 1280;
        const h = settings.height || 720;
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, w, h);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.95));
        if (!blob) return;
        const fname = `${target}-capture-${Date.now()}.jpg`;
        const file = new File([blob], fname, { type: 'image/jpeg' });
        const dt = new DataTransfer();
        dt.items.add(file);
        if (target === 'dented') {
          inputDented.files = dt.files;
          previewDented.src = URL.createObjectURL(blob);
        } else {
          inputPerfect.files = dt.files;
          previewPerfect.src = URL.createObjectURL(blob);
        }
      }

      async function captureFrameBlob() {
        if (!currentStream) return null;
        const track = currentStream.getVideoTracks()[0];
        const settings = track.getSettings();
        const w = settings.width || 1280;
        const h = settings.height || 720;
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, w, h);
        const blob = await new Promise(res => canvas.toBlob(res, 'image/jpeg', 0.9));
        if (blob) previewAuto.src = URL.createObjectURL(blob);
        return blob;
      }

      function renderDetails(metrics) {
        if (!metrics) { details.textContent = 'No metrics available (insufficient features).'; return; }
        const scale = parseFloat(mmPerPxInput?.value || '1') || 1;
        const toMM = (v) => (v * scale).toFixed(2);
        const m = metrics;
        details.innerHTML = `
          <ul style="margin:0; padding-left: 18px;">
            <li><strong>Max deviation:</strong> ${toMM(m.max_deviation_px)} mm</li>
            <li><strong>Mean deviation:</strong> ${toMM(m.mean_deviation_px)} mm</li>
            <li><strong>RMS deviation:</strong> ${toMM(m.rms_deviation_px)} mm</li>
            <li><strong>95th percentile:</strong> ${toMM(m.p95_deviation_px)} mm</li>
            <li><strong>Profile length:</strong> ${toMM(m.total_profile_length_px)} mm</li>
            <li><strong>Worst point (index):</strong> ${m.worst_point?.index ?? '-'} </li>
          </ul>`;
      }

      async function runAutoCheckOnce() {
        if (autoBusy) return;
        if (!inputPerfect.files || inputPerfect.files.length === 0) {
          autoStatus.textContent = 'Select a perfect image first.';
          return;
        }
        autoBusy = true;
        autoStatus.textContent = 'Capturing…';
        try {
          if (!currentStream) { await startCamera(); }
          const blob = await captureFrameBlob();
          if (!blob) { autoStatus.textContent = 'Capture failed'; autoBusy = false; return; }
          const dentedFile = new File([blob], `dented-auto-${Date.now()}.jpg`, { type: 'image/jpeg' });
          const fd = new FormData();
          const perfectFile = inputPerfect.files[0];
          fd.append('perfect', perfectFile, perfectFile.name || 'perfect.jpg');
          fd.append('dented', dentedFile, dentedFile.name);
          const res = await fetch('/process', { method: 'POST', body: fd });
          let data; try { data = await res.json(); } catch { data = null; }
          if (!res.ok) {
            const msg = data && data.error ? data.error : `Auto-check failed (HTTP ${res.status}).`;
            autoStatus.textContent = msg; autoBusy = false; return;
          }
          result.innerHTML = `<p class="small">Auto-check: ${data.time.toFixed(2)}s</p><img src="${data.image_url}" alt="Profile Comparison" />`;
          renderDetails(data.metrics);
          autoStatus.textContent = 'Last run OK';
        } catch (e) {
          console.error(e);
          autoStatus.textContent = 'Auto-check error';
        } finally {
          autoBusy = false;
        }
      }

      async function startAutoCheck() {
  const sec = 5;
        if (!currentStream) { await startCamera(); }
        // If no perfect is selected, capture baseline from camera as perfect
        if (!inputPerfect.files || inputPerfect.files.length === 0) {
          const baseline = await captureFrameBlob();
          if (!baseline) { alert('Could not capture baseline frame.'); return; }
          const baseFile = new File([baseline], `perfect-baseline-${Date.now()}.jpg`, { type: 'image/jpeg' });
          const dt = new DataTransfer();
          dt.items.add(baseFile);
          inputPerfect.files = dt.files;
          previewPerfect.src = URL.createObjectURL(baseline);
          autoStatus.textContent = 'Baseline captured';
        }
        if (autoTimer) clearInterval(autoTimer);
        await runAutoCheckOnce();
        autoTimer = setInterval(runAutoCheckOnce, sec * 1000);
        autoStartBtn.disabled = true; autoStopBtn.disabled = false;
        autoStatus.textContent = `Running every ${sec}s`;
      }

      function stopAutoCheck() {
        if (autoTimer) { clearInterval(autoTimer); autoTimer = null; }
        autoStartBtn.disabled = false; autoStopBtn.disabled = true;
        autoStatus.textContent = 'Stopped';
      }

      // Calibration: set mm/px from known field-of-view height (mm)
      function setScaleFromFov() {
        const fovMm = parseFloat(fovMmInput?.value || '0');
        if (!currentStream) { alert('Start the camera first to read video height.'); return; }
        const track = currentStream.getVideoTracks()[0];
        const settings = track?.getSettings?.() || {};
        const h = settings.height || video.videoHeight || 0;
        if (!(fovMm > 0) || !(h > 0)) { alert('Invalid FOV (mm) or video height.'); return; }
        const mmPerPx = fovMm / h;
        if (Number.isFinite(mmPerPx) && mmPerPx > 0) {
          mmPerPxInput.value = mmPerPx.toFixed(3);
          userLockedScale = true;
          try { localStorage.setItem(LS_KEY_SCALE, mmPerPxInput.value); localStorage.setItem(LS_KEY_LOCK, '1'); } catch {}
          autoStatus.textContent = `Scale set: ${mmPerPxInput.value} mm/px (h=${h}px)`;
        }
      }

      setScaleFovBtn?.addEventListener('click', setScaleFromFov);

      // Manual input lock/persist
      mmPerPxInput?.addEventListener('change', () => {
        const v = parseFloat(mmPerPxInput.value);
        if (v > 0) { userLockedScale = true; try { localStorage.setItem(LS_KEY_SCALE, v.toFixed(3)); localStorage.setItem(LS_KEY_LOCK, '1'); } catch {} }
      });
      resetScaleBtn?.addEventListener('click', () => { userLockedScale = false; try { localStorage.removeItem(LS_KEY_LOCK); } catch {}; updateScaleFromStream(); autoStatus.textContent = 'Scale reset to auto heuristic.'; });

      // Two-point calibration on overlay
      let calibActive = false;
      let p1 = null; let p2 = null;
      function drawOverlay() {
        if (!calibCanvas || !calibActive) return;
        const ctx = calibCanvas.getContext('2d');
        ctx.clearRect(0,0,calibCanvas.width, calibCanvas.height);
        ctx.strokeStyle = 'rgba(34,211,238,0.9)';
        ctx.fillStyle = 'rgba(34,211,238,0.9)';
        ctx.lineWidth = 2;
        if (p1) { ctx.beginPath(); ctx.arc(p1.x, p1.y, 5, 0, Math.PI*2); ctx.fill(); }
        if (p2) { ctx.beginPath(); ctx.arc(p2.x, p2.y, 5, 0, Math.PI*2); ctx.fill(); }
        if (p1 && p2) { ctx.beginPath(); ctx.moveTo(p1.x, p1.y); ctx.lineTo(p2.x, p2.y); ctx.stroke(); }
      }
      function toCanvasCoords(ev) {
        const rect = calibCanvas.getBoundingClientRect();
        const sx = calibCanvas.width / rect.width;
        const sy = calibCanvas.height / rect.height;
        const x = (ev.clientX - rect.left) * sx;
        const y = (ev.clientY - rect.top) * sy;
        return { x, y };
      }
      function handleOverlayClick(ev) {
        if (!calibActive) return;
        const pt = toCanvasCoords(ev);
        if (!p1) p1 = pt; else if (!p2) p2 = pt; else { p1 = pt; p2 = null; }
        drawOverlay();
        if (p1 && p2) {
          const dx = p1.x - p2.x; const dy = p1.y - p2.y;
          const distPx = Math.hypot(dx, dy);
          const mm = parseFloat(prompt('Enter real distance between points (mm):', '100') || '0');
          if (mm > 0 && distPx > 0) {
            const mmPerPx = mm / distPx;
            mmPerPxInput.value = mmPerPx.toFixed(3);
            userLockedScale = true;
            try { localStorage.setItem(LS_KEY_SCALE, mmPerPxInput.value); localStorage.setItem(LS_KEY_LOCK, '1'); } catch {}
            autoStatus.textContent = `Scale set: ${mmPerPxInput.value} mm/px`;
          }
          // end calibration session
          calibActive = false; calibCanvas.style.display = 'none'; p1 = null; p2 = null; drawOverlay();
        }
      }
      calibCanvas?.addEventListener('click', handleOverlayClick);
      calibrateLineBtn?.addEventListener('click', () => {
        if (!camAuto?.videoWidth) { alert('Start the camera first.'); return; }
        calibCanvas.width = camAuto.videoWidth;
        calibCanvas.height = camAuto.videoHeight;
        calibCanvas.style.display = 'block';
        calibActive = true; p1 = null; p2 = null; drawOverlay();
        autoStatus.textContent = 'Click two points on the overlay to calibrate.';
      });

      // Restore scale and alignment settings from previous session
      try {
        const saved = localStorage.getItem(LS_KEY_SCALE);
        const locked = localStorage.getItem(LS_KEY_LOCK) === '1';
        if (saved) { mmPerPxInput.value = saved; userLockedScale = locked; }
        const savedAlign = localStorage.getItem('tracs_align_mode');
        const savedInlier = localStorage.getItem('tracs_inlier_px');
        const savedAllowScale = localStorage.getItem('tracs_allow_scale') === '1';
        const savedDebug = localStorage.getItem('tracs_debug_visual') === '1';
        if (savedAlign && document.getElementById('alignMode')) document.getElementById('alignMode').value = savedAlign;
        if (savedInlier && document.getElementById('inlierPx')) document.getElementById('inlierPx').value = savedInlier;
        if (document.getElementById('allowScale')) document.getElementById('allowScale').checked = savedAllowScale;
        if (document.getElementById('debugVisual')) document.getElementById('debugVisual').checked = savedDebug;
      } catch {}

      // Persist alignment UI changes
      try {
        const persistAlignSettings = () => {
          try {
            const align = document.getElementById('alignMode')?.value || 'ransac';
            const inlier = document.getElementById('inlierPx')?.value || '25';
            const allow = document.getElementById('allowScale')?.checked ? '1' : '0';
            const debug = document.getElementById('debugVisual')?.checked ? '1' : '0';
            localStorage.setItem('tracs_align_mode', align);
            localStorage.setItem('tracs_inlier_px', inlier);
            localStorage.setItem('tracs_allow_scale', allow);
            localStorage.setItem('tracs_debug_visual', debug);
          } catch {}
        };
        ['alignMode','inlierPx','allowScale','debugVisual'].forEach(id => { const el = document.getElementById(id); if (el) el.addEventListener('change', persistAlignSettings); });
      } catch {}

      // Initialize device list when permissions are granted
      if (navigator.mediaDevices?.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true, audio: false })
          .then(s => { s.getTracks().forEach(t => t.stop()); return listCameras(); })
          .catch(() => listCameras());
      }

      startCamBtn?.addEventListener('click', startCamera);
      stopCamBtn?.addEventListener('click', stopCamera);
      cameraSelect?.addEventListener('change', () => { if (currentStream) startCamera(); });
      captureDentedBtn?.addEventListener('click', () => captureToInput('dented'));
      capturePerfectBtn?.addEventListener('click', () => captureToInput('perfect'));
  autoStartBtn?.addEventListener('click', startAutoCheck);
  autoStopBtn?.addEventListener('click', stopAutoCheck);
      window.addEventListener('beforeunload', stopCamera);
  window.addEventListener('beforeunload', stopAutoCheck);

      // Form submit -> process images
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        result.innerHTML = 'Processing...';
        // Ensure alignment options are included
        const alignMode = document.getElementById('alignMode')?.value || 'ransac';
        const inlierPx = document.getElementById('inlierPx')?.value || '25';
        const allowScale = document.getElementById('allowScale')?.checked ? '1' : '0';
        const fd = new FormData(form);
  fd.set('align_mode', alignMode);
  fd.set('inlier_px', inlierPx);
  fd.set('allow_scale', allowScale);
  fd.set('debug_visual', document.getElementById('debugVisual')?.checked ? '1' : '0');
        const res = await fetch('/process', { method: 'POST', body: fd });
        let data; try { data = await res.json(); } catch { data = null; }
        if (!res.ok) {
          const msg = data && data.error ? data.error : `Processing failed (HTTP ${res.status}).`;
          result.textContent = msg;
          return;
        }
        result.innerHTML = `<p class="small">Took ${data.time.toFixed(2)}s</p><img src="${data.image_url}" alt="Profile Comparison" />`;
        renderDetails(data.metrics);
      });

      // --- WebUSB helpers ---
      const connectUsbBtn = document.getElementById('connectUsb');
      const disconnectUsbBtn = document.getElementById('disconnectUsb');
      const usbInfo = document.getElementById('usbInfo');
      const vidInput = document.getElementById('vid');
      const pidInput = document.getElementById('pid');
      let usbDevice = null;

      const hexToInt = (s) => {
        if (!s) return undefined;
        const v = s.toString().trim().toLowerCase();
        const clean = v.startsWith('0x') ? v.slice(2) : v;
        const n = parseInt(clean, 16);
        return Number.isFinite(n) ? n : undefined;
      };

      async function connectUsb() {
        if (!('usb' in navigator)) { usbInfo.textContent = 'WebUSB not supported in this browser.'; return; }
        const vendorId = hexToInt(vidInput.value);
        const productId = hexToInt(pidInput.value);
        if (!vendorId) { usbInfo.textContent = 'Enter a valid vendorId (hex), e.g., 0x2341.'; return; }
        try {
          const filters = productId ? [{ vendorId, productId }] : [{ vendorId }];
          const device = await navigator.usb.requestDevice({ filters });
          await device.open();
          if (device.configuration === null) { await device.selectConfiguration(1); }
          const iface = device.configuration?.interfaces?.[0];
          if (iface) { await device.claimInterface(iface.interfaceNumber); }
          usbDevice = device;
          connectUsbBtn.disabled = true;
          disconnectUsbBtn.disabled = false;
          usbInfo.textContent = `Connected to:\n` +
            `Product: ${device.productName || '-'}\n` +
            `Manufacturer: ${device.manufacturerName || '-'}\n` +
            `Serial: ${device.serialNumber || '-'}\n` +
            `VID: 0x${device.vendorId.toString(16)} PID: 0x${device.productId.toString(16)}`;
        } catch (e) {
          usbInfo.textContent = 'USB connect failed: ' + (e?.message || e);
          console.error(e);
        }
      }

      async function disconnectUsb() {
        if (!usbDevice) return;
        try { if (usbDevice.opened) { try { await usbDevice.close(); } catch {} } }
        finally {
          usbDevice = null; connectUsbBtn.disabled = false; disconnectUsbBtn.disabled = true; usbInfo.textContent = 'Disconnected.';
        }
      }

      connectUsbBtn?.addEventListener('click', connectUsb);
      disconnectUsbBtn?.addEventListener('click', disconnectUsb);
    </script>
  </body>
 </html>
"""

@app.get('/')
def index():
    return render_template_string(PAGE_HTML)

@app.get('/healthz')
def healthz():
  return {'status': 'ok'}, 200

@app.post('/process')
def process():
  dented = request.files.get('dented')
  perfect = request.files.get('perfect')
  if not dented or not perfect:
    return {'error': 'Both images are required'}, 400

  uid = uuid.uuid4().hex
  workdir = UPLOAD_ROOT / uid
  workdir.mkdir(parents=True, exist_ok=True)

  dented_path = workdir / secure_filename(dented.filename or f"dented_{uid}.jpg")
  perfect_path = workdir / secure_filename(perfect.filename or f"perfect_{uid}.jpg")
  dented.save(dented_path)
  perfect.save(perfect_path)

  output_path = workdir / 'profile_comparison.jpg'
  global analyze_dent
  if analyze_dent is None:
    # Lazy import to prevent startup crashes if dependencies aren't ready
    try:
      from image_processing import analyze_dent as _analyze
      analyze_dent = _analyze
    except Exception as e:
      return {'error': f'Failed to import image_processing: {e}'}, 500
  try:
    # Read alignment options from form (optional)
    align_mode = request.form.get('align_mode', 'ransac')
    inlier_px = float(request.form.get('inlier_px', '25'))
    allow_scale = request.form.get('allow_scale', '0') in ('1', 'true', 'True')
    debug_visual = request.form.get('debug_visual', '0') in ('1', 'true', 'True')

    result = analyze_dent(
      str(perfect_path),
      str(dented_path),
      show_plot=False,
      output_path=str(output_path),
      align_mode=align_mode,
      inlier_px=float(inlier_px),
      allow_scale=bool(allow_scale),
      debug_visual=bool(debug_visual),
    )
  except TypeError as e:
    return {'error': f'Processing failed (type error): {e}'}, 400
  except Exception as e:
    return {'error': f'Processing failed: {e}'}, 500

  if not result or not isinstance(result, tuple) or len(result) < 2:
    return {'error': 'Processing failed: invalid result (image load error or pipeline issue). Ensure valid images.'}, 400

  # Backward/forward compatible tuple unpacking (path, time, metrics?)
  out_file = result[0]
  elapsed = result[1]
  metrics = result[2] if len(result) > 2 else None
  return {'image_url': f"/result/{uid}", 'time': elapsed, 'metrics': metrics}

@app.get('/result/<uid>')
def result(uid: str):
    img_path = UPLOAD_ROOT / uid / 'profile_comparison.jpg'
    if not img_path.exists():
        return { 'error': 'Not found' }, 404
    return send_file(img_path, mimetype='image/jpeg')

if __name__ == '__main__':
  port = int(os.getenv('PORT', '5050'))
  host = os.getenv('HOST', '0.0.0.0')
  app.run(host=host, port=port, debug=True)
