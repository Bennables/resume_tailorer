"""Tiny Flask UI: paste a JD, pick a folder name, get the PDF back."""

import re
from flask import Flask, abort, request, send_file

from .tailor import run_tailor

app = Flask(__name__)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9_\-]+")

FORM_HTML = """
<!doctype html>
<html>
<head>
  <title>Resume Tailorer</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
    label { display: block; margin-top: 1rem; font-weight: 600; }
    input[type=text] { width: 100%; padding: 0.5rem; font-size: 1rem; }
    textarea { width: 100%; min-height: 300px; padding: 0.5rem; font-size: 0.95rem; font-family: inherit; }
    button { margin-top: 1rem; padding: 0.6rem 1.2rem; font-size: 1rem; cursor: pointer; }
  </style>
</head>
<body>
  <h1>Resume Tailorer</h1>
  <form method="post" action="/tailor">
    <label>Folder name</label>
    <input type="text" name="folder" required placeholder="acme_backend" />
    <label>Job description</label>
    <textarea name="job_description" required placeholder="Paste the JD here..."></textarea>
    <button type="submit">Tailor & Download</button>
  </form>
</body>
</html>
"""


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
