"""Renders selected bullets and skills into the LaTeX template."""

import re

from .parse_bullets import Bank, Role, SkillRow
from .select_bullets import Selection


def _render_role(role: Role, chosen_indices: list[int]) -> str:
    lines = [
        f"\\textbf{{{role.title}}} \\hfill {role.dates} \\\\",
        f"\\textit{{{role.company}}} \\hfill {role.location}",
        "\\begin{itemize}",
    ]
    for idx in chosen_indices:
        if 0 <= idx < len(role.bullets):
            lines.append(f"  \\item {role.bullets[idx]}")
    lines.append("\\end{itemize}")
    return "\n".join(lines)


def _render_sections(bank: Bank, selection: Selection) -> str:
    section_order: list[str] = []
    by_section: dict[str, list[str]] = {}
    for role in bank.roles:
        chosen = selection.bullets_per_role.get(role.role_id, [])
        if not chosen:
            continue
        block = _render_role(role, chosen[: role.max_bullets])
        if role.section not in by_section:
            by_section[role.section] = []
            section_order.append(role.section)
        by_section[role.section].append(block)

    parts: list[str] = []
    for section in section_order:
        parts.append(f"\\section*{{{section}}}")
        parts.append("\n\n".join(by_section[section]))
    return "\n".join(parts)


def _render_skill_row(row: SkillRow, highlighted: list[int]) -> str:
    seen: set[int] = set()
    ordered: list[str] = []
    for idx in highlighted:
        if 0 <= idx < len(row.skills) and idx not in seen:
            seen.add(idx)
            ordered.append(f"\\textbf{{{row.skills[idx]}}}")
    for i, skill in enumerate(row.skills):
        if i not in seen:
            ordered.append(skill)
    return f"\\textbf{{{row.name}}}: {', '.join(ordered)} \\\\"


def _render_skills(bank: Bank, selection: Selection) -> str:
    return "\n".join(
        _render_skill_row(row, selection.skills_per_row.get(row.name, []))
        for row in bank.skill_rows
    )


def render_resume(template: str, bank: Bank, selection: Selection) -> str:
    result = template.replace("<<SECTIONS>>", _render_sections(bank, selection))
    result = result.replace("<<SKILLS>>", _render_skills(bank, selection))

    def _one_role(match: re.Match[str]) -> str:
        role_id = match.group(1)
        for role in bank.roles:
            if role.role_id == role_id:
                chosen = selection.bullets_per_role.get(role_id, [])
                return _render_role(role, chosen[: role.max_bullets])
        return match.group(0)

    result = re.sub(r"<<ROLE:([^>]+)>>", _one_role, result)
    return result
