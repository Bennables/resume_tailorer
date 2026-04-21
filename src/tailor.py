"""Entry point: reads inputs, calls Gemini, writes a timestamped run dir under output/, fits to one page."""

import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from .parse_bullets import Bank, parse_bullets
from .render import render_resume
from .select_bullets import Selection, select_bullets

ROOT = Path(__file__).resolve().parent.parent
BULLETS_PATH = ROOT / "inputs" / "bullets.tex"
TEMPLATE_PATH = ROOT / "inputs" / "template.tex"
JD_PATH = ROOT / "inputs" / "job_description.txt"
OUTPUT_ROOT = ROOT / "output"

MAX_TRIM_ITERATIONS = 20


def _compile_page_count(tex_path: Path) -> int | None:
    """Run pdflatex and return the page count, or None if pdflatex is unavailable/failed."""
    if shutil.which("pdflatex") is None:
        return None
    prev_cwd = os.getcwd()
    try:
        os.chdir(tex_path.parent)
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            capture_output=True,
            text=True,
            timeout=60,
        )
    finally:
        os.chdir(prev_cwd)
    match = re.search(r"Output written on .+?\((\d+) pages?", result.stdout)
    if match:
        return int(match.group(1))
    return None


def _trim_one_bullet(selection: Selection, bank: Bank) -> bool:
    """Drop the last (weakest) bullet from the role with the most selected bullets.
    Ties go to the role appearing latest in bullets.tex. Returns False if nothing to trim."""
    target_idx = -1
    target_count = 0
    for i, role in enumerate(bank.roles):
        n = len(selection.bullets_per_role.get(role.role_id, []))
        if n > target_count or (n == target_count and n > 0 and i > target_idx):
            target_idx = i
            target_count = n
    if target_count == 0:
        return False
    selection.bullets_per_role[bank.roles[target_idx].role_id].pop()
    return True


def main() -> None:
    load_dotenv()

    bank = parse_bullets(BULLETS_PATH)
    template = TEMPLATE_PATH.read_text()
    job_description = JD_PATH.read_text()

    selection = select_bullets(bank, job_description)

    run_dir = OUTPUT_ROOT / datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    tex_path = run_dir / "resume.tex"
    pdf_path = run_dir / "resume.pdf"

    for attempt in range(MAX_TRIM_ITERATIONS + 1):
        resume_tex = render_resume(template, bank, selection)
        tex_path.write_text(resume_tex)

        pages = _compile_page_count(tex_path)
        if pages is None:
            print(f"Wrote {tex_path} (pdflatex unavailable or failed; skipped fit check, no PDF)")
            return
        if pages <= 1:
            trims = attempt
            suffix = f" after trimming {trims} bullet{'s' if trims != 1 else ''}" if trims else ""
            print(f"Wrote {tex_path}")
            print(f"Wrote {pdf_path} ({pages} page{suffix})")
            return
        if not _trim_one_bullet(selection, bank):
            print(f"Wrote {tex_path}")
            print(f"Wrote {pdf_path} ({pages} pages; nothing left to trim)")
            return

    print(f"Wrote {tex_path}")
    print(f"Wrote {pdf_path} (still overflowing after {MAX_TRIM_ITERATIONS} trims)")


if __name__ == "__main__":
    main()
