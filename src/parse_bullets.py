"""Parses inputs/bullets.tex into structured roles and skill rows."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Role:
    role_id: str
    company: str
    title: str
    dates: str
    location: str
    size: str
    section: str
    bullets: list[str] = field(default_factory=list)

    @property
    def max_bullets(self) -> int:
        return 4 if self.size == "big" else 3


@dataclass
class SkillRow:
    name: str
    skills: list[str]


@dataclass
class Bank:
    roles: list[Role]
    skill_rows: list[SkillRow]


_ROLE_FIELDS = ("ROLE_ID", "COMPANY", "TITLE", "DATES", "LOCATION", "SIZE")


def _strip_marker(line: str, key: str) -> str | None:
    prefix = f"%%% {key}:"
    if line.startswith(prefix):
        return line[len(prefix):].strip()
    return None


def parse_bullets(path: Path) -> Bank:
    lines = path.read_text().splitlines()
    roles: list[Role] = []
    skill_rows: list[SkillRow] = []

    i = 0
    current: dict[str, str] | None = None
    bullets: list[str] = []
    in_skills = False
    current_row: SkillRow | None = None
    current_section = "Experience"

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.lstrip()

        section_value = _strip_marker(stripped, "SECTION")
        if section_value is not None and not in_skills:
            current_section = section_value or current_section
        elif stripped.startswith("%%% SKILLS_START"):
            in_skills = True
            current_row = None
        elif stripped.startswith("%%% SKILLS_END"):
            in_skills = False
            current_row = None
        elif in_skills:
            row_name = _strip_marker(stripped, "ROW")
            if row_name is not None:
                current_row = SkillRow(name=row_name, skills=[])
                skill_rows.append(current_row)
            elif current_row is not None and stripped and not stripped.startswith("%"):
                current_row.skills.extend(
                    s.strip() for s in line.split(",") if s.strip()
                )
        elif stripped.startswith("%%% END_ROLE"):
            if current is not None:
                roles.append(Role(
                    role_id=current.get("ROLE_ID", ""),
                    company=current.get("COMPANY", ""),
                    title=current.get("TITLE", ""),
                    dates=current.get("DATES", ""),
                    location=current.get("LOCATION", ""),
                    size=current.get("SIZE", "small").lower(),
                    section=current_section,
                    bullets=bullets,
                ))
            current = None
            bullets = []
        else:
            matched = False
            for key in _ROLE_FIELDS:
                value = _strip_marker(stripped, key)
                if value is not None:
                    if current is None:
                        current = {}
                    current[key] = value
                    matched = True
                    break
            if not matched and current is not None and stripped.startswith(r"\item"):
                bullets.append(stripped[len(r"\item"):].strip())

        i += 1

    return Bank(roles=roles, skill_rows=skill_rows)
