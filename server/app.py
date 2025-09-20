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
          <div class="actions">
            <button type="submit">Run Analysis</button>
            <span class="small">Max 32MB per image</span>
          </div>
        </form>
        <div class="layout">
          <div class="panel">
            <div id="result" class="result"></div>
          </div>
          <div class="panel">
            <h3>Deviation details</h3>
            <div id="details" class="small">Upload images and run analysis…</div>
          </div>
        </div>
      </div>
    </div>
    <script>
      const form = document.getElementById('form');
      const result = document.getElementById('result');
      const details = document.getElementById('details');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        result.innerHTML = 'Processing...';
        const fd = new FormData(form);
        const res = await fetch('/process', { method: 'POST', body: fd });
        let data;
        try { data = await res.json(); } catch { data = null; }
        if (!res.ok) {
          const msg = data && data.error ? data.error : `Processing failed (HTTP ${res.status}).`;
          result.textContent = msg;
          return;
        }
        result.innerHTML = `<p class=\"small\">Took ${data.time.toFixed(2)}s</p><img src=\"${data.image_url}\" alt=\"Profile Comparison\" />`;
        if (data.metrics) {
          const m = data.metrics;
          details.innerHTML = `
            <ul style=\"margin:0; padding-left: 18px;\">
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
    </script>
  </body>
 </html>
"""

@app.get('/')
def index():
    return render_template_string(PAGE_HTML)

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
    app.run(host='127.0.0.1', port=5050, debug=True)
