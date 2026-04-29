"""Calls the Gemini API to pick relevant bullets per role and skills per row."""

import json
import os
import re
from dataclasses import dataclass

from google import genai
from google.genai import types

from .parse_bullets import Bank


@dataclass
class Selection:
    bullets_per_role: dict[str, list[int]]
    skills_per_row: dict[str, list[int]]

_INSTRUCTIONS = (
    "You tailor resumes to job descriptions. Given a BANK of resume content "
    "and a JOB DESCRIPTION, return JSON selecting which bullets and skills to "
    "highlight.\n\n"
    "BULLET PRIORITY ORDER (rank bullets by this, highest first):\n"
    "1. Keyword overlap with the JD AND concrete metrics (numbers, scale, latency, "
    "cost, revenue, accuracy, throughput, time saved, user/customer impact).\n"
    "2. Strong fit for the role — its actual work, problems to solve, and implied "
    "seniority — without necessarily overlapping on keywords.\n"
    "3. Concrete metrics alone, even without keyword overlap.\n"
    "ATS filters rank resumes by exact keyword/phrase match. Cover distinct JD "
    "keywords rather than repeating the same ones.\n\n"
    "HARD RULES:\n"
    "1. Never invent or rewrite content — reference existing items by index only.\n"
    "2. Evaluate roles/projects as whole entries. Include a role only when the "
    "overall entry is among the strongest matches, not just because one bullet "
    "overlaps.\n"
    "3. Include ALL \"Experience\" roles in bullets_per_role. Never omit any.\n"
    "4. Include at most 4 \"Projects\" roles; 3 is typical. If more than 4 qualify, "
    "keep the 4 strongest and omit the rest. Order included projects by relevance "
    "to the JD, most relevant first; break ties by number of bullets, more first. "
    "Hackathon projects must never appear first in the projects list.\n"
    "5. Per included role: choose ≥3 bullets (or all if fewer than 3 exist). "
    "Older Experience roles may use 2 bullets if their top 2 already capture "
    "the strongest relevant evidence. Never exceed the role's max_bullets from "
    "the BANK. Order strongest fit first; break ties by quantified outcomes.\n"
    "6. Per skill row: return indices of skills the JD names or clearly implies, "
    "ordered by relevance. \n"
    "7. Avoid excessive repetition: do not select bullets/skill rows that cause "
    "the same skill, technology, or keyword to appear more than 2 times across "
    "the whole resume, unless the JD makes that skill central to the role. When "
    "repetition is unavoidable, prefer the strongest concrete evidence with "
    "metrics and drop weaker duplicate mentions.\n\n"
    "Output ONLY valid JSON:\n"
    '{"bullets_per_role": {"<role_id>": [<bullet_idx>, ...]}, '
    '"skills_per_row": {"<row_name>": [<skill_idx>, ...]}}'
)


_MODEL = "gemini-3.1-pro-preview"


def _build_bank_payload(bank: Bank) -> str:
    payload = {
        "roles": [
            {
                "role_id": r.role_id,
                "section": r.section,
                "company": r.company,
                "title": r.title,
                "max_bullets": r.max_bullets,
                "bullets": [{"idx": i, "text": b} for i, b in enumerate(r.bullets)],
            }
            for r in bank.roles
        ],
        "skill_rows": [
            {
                "name": row.name,
                "skills": [{"idx": i, "text": s} for i, s in enumerate(row.skills)],
            }
            for row in bank.skill_rows
        ],
    }
    return "BANK:\n" + json.dumps(payload, indent=2)


def _parse_response(text: str) -> Selection:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    data = json.loads(text)
    return Selection(
        bullets_per_role={k: list(v) for k, v in data.get("bullets_per_role", {}).items()},
        skills_per_row={k: list(v) for k, v in data.get("skills_per_row", {}).items()},
    )


def _cap_selected_projects(selection: Selection, bank: Bank, max_projects: int = 4) -> None:
    sections_by_role = {role.role_id: role.section for role in bank.roles}
    selected_projects = [
        role_id
        for role_id, bullets in selection.bullets_per_role.items()
        if bullets and sections_by_role.get(role_id) == "Projects"
    ]
    for role_id in selected_projects[max_projects:]:
        selection.bullets_per_role.pop(role_id, None)


def select_bullets(bank: Bank, job_description: str) -> Selection:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    system_instruction = f"{_INSTRUCTIONS}\n\n{_build_bank_payload(bank)}"
    response = client.models.generate_content(
        model=_MODEL,
        contents=f"JOB DESCRIPTION:\n{job_description}",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )
    selection = _parse_response(response.text)
    _cap_selected_projects(selection, bank)
    return selection
