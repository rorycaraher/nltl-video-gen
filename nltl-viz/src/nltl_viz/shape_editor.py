from __future__ import annotations

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from nltl_viz import shapes as shapes_mod
from nltl_viz.shapes import CustomShape

_PAGE_TEMPLATE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>NLTL Viz — Shape Editor</title>
<style>
  body { font-family: -apple-system, sans-serif; background: #1a1a1a; color: #eee;
         display: flex; flex-direction: column; align-items: center; padding: 20px; }
  canvas { background: #0a0a0c; border: 1px solid #444; cursor: crosshair; }
  .controls { margin-top: 16px; display: flex; gap: 8px; align-items: center; }
  input[type=text] { padding: 6px; font-size: 14px; }
  button { padding: 6px 14px; font-size: 14px; cursor: pointer; }
  #message { margin-top: 10px; min-height: 20px; color: #f66; }
  .hint { color: #999; font-size: 13px; margin-top: 8px; text-align: center; }
</style>
</head>
<body>
<h2>NLTL Viz — Shape Editor</h2>
<div class="hint">Click empty space to add a vertex, in order.<br>
Drag a vertex to move it. Click a vertex (without dragging) to delete it.</div>
<canvas id="canvas" width="520" height="520"></canvas>
<div class="controls">
  <input type="text" id="nameInput" placeholder="shape name">
  <button id="saveBtn">Save</button>
  <button id="cancelBtn">Cancel</button>
  <button id="clearBtn">Clear</button>
</div>
<div id="message"></div>
<script>
const state = __INITIAL_STATE__;
const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');
const nameInput = document.getElementById('nameInput');
const message = document.getElementById('message');
nameInput.value = state.name || '';

let vertices = (state.vertices || []).map(v => [v[0], v[1]]);
const MARGIN = 20;
const SIZE = canvas.width - 2 * MARGIN;
const VERTEX_RADIUS = 7;
const DRAG_THRESHOLD = 4;
const GRID_STEPS = 20;

function toPixel([fx, fy]) {
  return [MARGIN + fx * SIZE, MARGIN + fy * SIZE];
}
function toFraction(px, py) {
  return [(px - MARGIN) / SIZE, (py - MARGIN) / SIZE];
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  ctx.strokeStyle = '#2a2a2e';
  ctx.lineWidth = 1;
  for (let i = 0; i <= GRID_STEPS; i++) {
    const p = MARGIN + (i / GRID_STEPS) * SIZE;
    ctx.beginPath(); ctx.moveTo(p, MARGIN); ctx.lineTo(p, MARGIN + SIZE); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(MARGIN, p); ctx.lineTo(MARGIN + SIZE, p); ctx.stroke();
  }
  ctx.strokeStyle = '#555';
  ctx.strokeRect(MARGIN, MARGIN, SIZE, SIZE);

  if (vertices.length > 0) {
    ctx.strokeStyle = '#D8D8D2';
    ctx.lineWidth = 2;
    ctx.beginPath();
    const [x0, y0] = toPixel(vertices[0]);
    ctx.moveTo(x0, y0);
    for (let i = 1; i < vertices.length; i++) {
      const [x, y] = toPixel(vertices[i]);
      ctx.lineTo(x, y);
    }
    if (vertices.length > 2) ctx.closePath();
    ctx.stroke();

    vertices.forEach((v, i) => {
      const [x, y] = toPixel(v);
      ctx.fillStyle = i === 0 ? '#6E5470' : '#2E8C8A';
      ctx.beginPath();
      ctx.arc(x, y, VERTEX_RADIUS, 0, Math.PI * 2);
      ctx.fill();
    });
  }
}

function hitTestVertex(px, py) {
  for (let i = 0; i < vertices.length; i++) {
    const [x, y] = toPixel(vertices[i]);
    if (Math.hypot(x - px, y - py) <= VERTEX_RADIUS + 3) return i;
  }
  return -1;
}

let dragIndex = -1;
let dragMoved = false;
let dragStart = [0, 0];

canvas.addEventListener('mousedown', (e) => {
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  const hit = hitTestVertex(px, py);
  if (hit >= 0) {
    dragIndex = hit;
    dragMoved = false;
    dragStart = [px, py];
  }
});

canvas.addEventListener('mousemove', (e) => {
  if (dragIndex < 0) return;
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  if (Math.hypot(px - dragStart[0], py - dragStart[1]) > DRAG_THRESHOLD) {
    dragMoved = true;
  }
  if (dragMoved) {
    vertices[dragIndex] = toFraction(px, py);
    draw();
  }
});

canvas.addEventListener('mouseup', (e) => {
  const rect = canvas.getBoundingClientRect();
  const px = e.clientX - rect.left, py = e.clientY - rect.top;
  if (dragIndex >= 0) {
    if (!dragMoved) {
      vertices.splice(dragIndex, 1);
    }
    dragIndex = -1;
    dragMoved = false;
    draw();
    return;
  }
  vertices.push(toFraction(px, py));
  draw();
});

document.getElementById('clearBtn').addEventListener('click', () => {
  vertices = [];
  draw();
});

document.getElementById('cancelBtn').addEventListener('click', async () => {
  await fetch('/cancel', { method: 'POST' });
  document.body.innerHTML =
    '<h2 style="color:#eee;font-family:sans-serif;text-align:center;margin-top:40px;">Cancelled. You can close this tab.</h2>';
});

document.getElementById('saveBtn').addEventListener('click', async () => {
  message.textContent = '';
  const name = nameInput.value.trim();
  const resp = await fetch('/save', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, vertices }),
  });
  const payload = await resp.json();
  if (!resp.ok) {
    message.textContent = payload.error;
    return;
  }
  document.body.innerHTML =
    '<h2 style="color:#eee;font-family:sans-serif;text-align:center;margin-top:40px;">Saved. You can close this tab.</h2>';
});

draw();
</script>
</body>
</html>
"""


def run(existing: Optional[CustomShape], path: Path) -> Optional[CustomShape]:
    """Start a local-only HTTP server, open the browser to the vertex editor,
    and block until the user saves or cancels. Returns the saved shape (also
    already written to `path`), or None if cancelled."""
    result: dict[str, Optional[CustomShape]] = {"shape": None}
    done = threading.Event()

    initial_state = json.dumps(
        {
            "name": existing.name if existing else "",
            "vertices": [list(v) for v in existing.vertices] if existing else [],
        }
    )
    page = _PAGE_TEMPLATE.replace("__INITIAL_STATE__", initial_state)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass  # keep the CLI quiet; validation errors surface via the JSON response instead

        def _respond_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path != "/":
                self.send_response(404)
                self.end_headers()
                return
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}

            if self.path == "/cancel":
                self._respond_json(200, {"ok": True})
                done.set()
                threading.Thread(target=httpd.shutdown, daemon=True).start()
                return

            if self.path == "/save":
                name = str(body.get("name", "")).strip()
                vertices = tuple((float(x), float(y)) for x, y in body.get("vertices", []))
                try:
                    shapes_mod.validate_name(name)
                    shapes_mod.validate_simple_polygon(vertices)
                except ValueError as exc:
                    self._respond_json(400, {"error": str(exc)})
                    return
                shape = CustomShape(name=name, vertices=vertices)
                shapes_mod.upsert(path, shape)
                result["shape"] = shape
                self._respond_json(200, {"ok": True})
                done.set()
                threading.Thread(target=httpd.shutdown, daemon=True).start()
                return

            self.send_response(404)
            self.end_headers()

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = httpd.server_address[1]
    url = f"http://127.0.0.1:{port}/"

    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    webbrowser.open(url)

    done.wait()
    server_thread.join(timeout=5)

    return result["shape"]
