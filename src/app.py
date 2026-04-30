"""Tiny Flask UI: paste a JD, pick a folder name, get the PDF back."""

import re
from pathlib import Path
from flask import Flask, abort, request, send_file

from .tailor import run_tailor

app = Flask(__name__)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_\-]+")

FORM_HTML = """
<!doctype html>
<html>
<head>
  <title>Resume Tailorer</title>
  <link rel="icon" type="image/png" href="/dorp.png" />
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; position: relative; }
    label { display: block; margin-top: 1rem; font-weight: 600; }
    input[type=text] { width: 100%; padding: 0.5rem; font-size: 1rem; }
    textarea { width: 100%; min-height: 300px; padding: 0.5rem; font-size: 0.95rem; font-family: inherit; }
    button { margin-top: 1rem; padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer; }
    .jay { position: fixed; pointer-events: none; opacity: 0.18; z-index: -1; }
  </style>
</head>
<body>
  <h1>Resume Tailorer</h1>
  <script>
    const COUNT = 70;
    for (let i = 0; i < COUNT; i++) {
      const img = document.createElement('img');
      img.src = '/dorp.png';
      img.className = 'jay';
      const size = 80 + Math.random() * 160;
      img.style.width = size + 'px';
      img.style.left = (Math.random() * 100) + 'vw';
      img.style.top = (Math.random() * 100) + 'vh';
      img.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';
      img.style.opacity = (0.08 + Math.random() * .8).toFixed(2);
      document.body.appendChild(img);
    }
  </script>
  <form id="tailor-form" method="post" action="/tailor">
    <label>Folder name</label>
    <input type="text" name="folder" required placeholder="acme_backend" />
    <label>Job description</label>
    <textarea name="job_description" required placeholder="Paste the JD here..."></textarea>
    <button type="submit" id="submit-btn">Tailor & Download</button>
    <span id="status" style="margin-left: 1rem; color: #555;"></span>
  </form>
  <script>
    const form = document.getElementById('tailor-form');
    const btn = document.getElementById('submit-btn');
    const status = document.getElementById('status');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      btn.disabled = true;
      status.textContent = 'Tailoring...';
      try {
        const res = await fetch('/tailor', { method: 'POST', body: new FormData(form) });
        if (!res.ok) throw new Error(await res.text() || res.statusText);

        const disposition = res.headers.get('Content-Disposition') || '';
        const match = disposition.match(/filename\\*?=(?:UTF-8'')?"?([^";]+)"?/i);
        const filename = match ? decodeURIComponent(match[1]) : 'resume.pdf';

        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        form.reset();
        status.textContent = 'Done.';
      } catch (err) {
        status.textContent = 'Error: ' + err.message;
      } finally {
        btn.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.get("/jaydurbss.png")
def jaydurbss():
    return send_file(Path(__file__).parent / "JAYDURBSS.png", mimetype="image/png")


@app.get("/dorp.png")
def dorp():
    return send_file(Path(__file__).parent / "DORP.png", mimetype="image/png")


@app.get("/")
def index() -> str:
    return FORM_HTML


@app.post("/tailor")
def tailor():
    folder = (request.form.get("folder") or "").strip()
    jd = (request.form.get("job_description") or "").strip()
    if not folder or not jd:
        abort(400, "folder and job_description are required")

    safe_folder = _SAFE_NAME.sub("_", folder).strip("_")
    if not safe_folder:
        abort(400, "folder name must contain letters, numbers, _ or -")

    output_path = run_tailor(folder_name=safe_folder, job_description=jd)
    download_name = f"{safe_folder}{output_path.suffix}"
    return send_file(output_path, as_attachment=True, download_name=download_name)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=3125, debug=True)
