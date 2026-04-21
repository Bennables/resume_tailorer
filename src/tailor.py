"""Entry point: reads inputs, calls Gemini, writes output/resume.tex."""

from pathlib import Path

from dotenv import load_dotenv

from .parse_bullets import parse_bullets
from .render import render_resume
from .select_bullets import select_bullets

ROOT = Path(__file__).resolve().parent.parent
BULLETS_PATH = ROOT / "inputs" / "bullets.tex"
TEMPLATE_PATH = ROOT / "inputs" / "template.tex"
JD_PATH = ROOT / "inputs" / "job_description.txt"
OUTPUT_PATH = ROOT / "output" / "resume.tex"


def main() -> None:
    load_dotenv()

    bank = parse_bullets(BULLETS_PATH)
    template = TEMPLATE_PATH.read_text()
    job_description = JD_PATH.read_text()

    selection = select_bullets(bank, job_description)
    resume_tex = render_resume(template, bank, selection)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(resume_tex)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
