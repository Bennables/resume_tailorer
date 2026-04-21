# Resume Tailorer

Generates a job-specific LaTeX resume by selecting the most relevant bullets from your master bullet bank for a given job description.

## Setup

1. `pip install -r requirements.txt`
2. `cp .env.example .env` and add your `GEMINI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/apikey))
3. Fill in the one-time inputs:
   - [inputs/bullets.tex](inputs/bullets.tex) — your master bank of all experiences and bullets
   - [inputs/template.tex](inputs/template.tex) — your resume layout with `<<PLACEHOLDER>>` markers

## Usage

1. Paste the target job description into [inputs/job_description.txt](inputs/job_description.txt)
2. Run `python -m src.tailor`
3. Copy `output/resume.tex` into your LaTeX editor

## How it works

- Parses the bullet bank into structured roles
- Sends the full bank + job description to Gemini
- Gemini returns a selection of bullets per role, tuned to the JD
- Renders the selection into your template and writes `output/resume.tex`
