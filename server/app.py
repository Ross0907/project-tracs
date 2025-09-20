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

from image_processing import analyze_dent
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
      video#cam { width: 100%; max-height: 360px; display:block; }
      img.preview { max-width: 100%; border-radius: 8px; border: 1px solid #223040; background: #0b1117; }
      select#cameraSelect { background: #0b1117; color: #dce4ee; border: 1px solid #1f2a38; border-radius: 8px; padding: 8px; }
      .hint { color: var(--muted); font-size: 12px; margin-top: -4px; }
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
            <h3>Camera capture (optional)</h3>
            <div class="hint">Use your camera to capture both images. Captured photos auto-fill the file inputs above.</div>
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

          <div class="actions">
            <button type="submit">Run Analysis</button>
            <span class="small">Max 32MB per image</span>
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
      const cameraSelect = document.getElementById('cameraSelect');
      const inputDented = document.querySelector('input[name="dented"]');
      const inputPerfect = document.querySelector('input[name="perfect"]');
      const previewDented = document.getElementById('previewDented');
      const previewPerfect = document.getElementById('previewPerfect');

      let currentStream = null;

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
      window.addEventListener('beforeunload', stopCamera);

      // Form submit -> process images
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        result.innerHTML = 'Processing...';
        const fd = new FormData(form);
        const res = await fetch('/process', { method: 'POST', body: fd });
        let data; try { data = await res.json(); } catch { data = null; }
        if (!res.ok) {
          const msg = data && data.error ? data.error : `Processing failed (HTTP ${res.status}).`;
          result.textContent = msg;
          return;
        }
        result.innerHTML = `<p class="small">Took ${data.time.toFixed(2)}s</p><img src="${data.image_url}" alt="Profile Comparison" />`;
        if (data.metrics) {
          const m = data.metrics;
          details.innerHTML = `
            <ul style="margin:0; padding-left: 18px;">
              <li><strong>Max deviation:</strong> ${m.max_deviation_px} px</li>
              <li><strong>Mean deviation:</strong> ${m.mean_deviation_px} px</li>
              <li><strong>RMS deviation:</strong> ${m.rms_deviation_px} px</li>
              <li><strong>95th percentile:</strong> ${m.p95_deviation_px} px</li>
              <li><strong>Profile length:</strong> ${m.total_profile_length_px} px</li>
              <li><strong>Worst point (index):</strong> ${m.worst_point?.index ?? '-'} </li>
            </ul>`;
        } else {
          details.textContent = 'No metrics available (insufficient features).';
        }
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
  try:
    result = analyze_dent(
      str(perfect_path),
      str(dented_path),
      show_plot=False,
      output_path=str(output_path),
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
