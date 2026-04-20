"""Calls the Claude API to pick relevant bullets per role and skills per row."""

import json
import re
from dataclasses import dataclass

from anthropic import Anthropic

from .parse_bullets import Bank


@dataclass
class Selection:
    bullets_per_role: dict[str, list[int]]
    skills_per_row: dict[str, list[int]]

_INSTRUCTIONS = (
    "You tailor resumes to a job description. You are given a BANK of resume "
    "content and a JOB DESCRIPTION. Return JSON choosing which bullets and "
    "skills to highlight.\n\n"
    "Primary goal: pick the bullets and skills that best demonstrate the "
    "candidate is a strong fit for THIS specific role — the work the JD "
    "actually describes, the problems it asks the candidate to solve, and "
    "the seniority level implied.\n\n"
    "Keyword overlap with the JD is a strong secondary signal because:\n"
    "(a) ATS (Applicant Tracking System) filters rank resumes partly by exact "
    "keyword and phrase overlap, so JD terminology in the selected bullets "
    "helps the resume get past automated screens, and\n"
    "(b) shared terminology usually indicates genuine topical fit.\n\n"
    "Use keyword overlap as a tiebreaker and a coverage check, not as the "
    "objective itself. A bullet about genuinely relevant work beats a bullet "
    "that just happens to share words with the JD. Where several bullets are "
    "similarly relevant, prefer the one that uses the JD's exact terminology, "
    "and try to cover distinct JD keywords across the selected bullets rather "
    "than hitting the same keyword repeatedly.\n\n"
    "Hard rules:\n"
    "- Never invent or rewrite content. Only reference existing items by index.\n"
    "- For each role, pick up to max_bullets bullets. Order indices in the order "
    "they should appear on the resume, strongest fit first.\n"
    "- For each skill row, return indices of skills the JD actually names or "
    "clearly implies, ordered by relevance. These get bolded and moved to the "
    "front of the row. Do not mark skills just because they are generally "
    "impressive.\n\n"
    "Output ONLY JSON with this exact shape and nothing else:\n"
    '{"bullets_per_role": {"<role_id>": [<bullet_idx>, ...]}, '
    '"skills_per_row": {"<row_name>": [<skill_idx>, ...]}}'
)


def _build_bank_payload(bank: Bank) -> str:
    payload = {
        "roles": [
            {
                "role_id": r.role_id,
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


def select_bullets(bank: Bank, job_description: str) -> Selection:
    client = Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=[
            {"type": "text", "text": _INSTRUCTIONS},
            {
                "type": "text",
                "text": _build_bank_payload(bank),
                "cache_control": {"type": "ephemeral"},
            },
        ],
        messages=[
            {"role": "user", "content": f"JOB DESCRIPTION:\n{job_description}"}
        ],
    )
    return _parse_response(message.content[0].text)
