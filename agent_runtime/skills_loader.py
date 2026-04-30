from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict

from .skill_parser import parse_frontmatter


@dataclass
class Skill:
    filename: str
    meta: Dict[str, Any]
    title: str
    goal: str
    body: str
    raw: str

    PLANNING_FIELDS = {"step_id", "depends_on"}

    @property
    def schema_meta(self) -> Dict[str, Any]:
        """
        Return meta with planning-only fields stripped (for schema validation).
        """
        return {k: v for k, v in self.meta.items() if k not in self.PLANNING_FIELDS}


def load_skill_file(skills_dir: str, filename: str) -> Skill:
    path = os.path.join(skills_dir, filename)
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    meta, body = parse_frontmatter(raw)

    title = ""
    goal = ""

    # Lightweight parsing from markdown BODY (not YAML):
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# ") and not title:
            title = s[2:].strip()
        if s.lower().startswith("goal:") and not goal:
            goal = s.split(":", 1)[1].strip()

    return Skill(
        filename=filename,
        meta=meta,
        title=title or filename,
        goal=goal,
        body=body,
        raw=raw,
    )


def load_all_skills(skills_dir: str) -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    if not os.path.isdir(skills_dir):
        return skills

    # Recursively walk through all subdirectories
    for root, _, files in os.walk(skills_dir):
        for filename in sorted(files):
            if filename.endswith(".md"):
                rel_path = os.path.relpath(os.path.join(root, filename), skills_dir)
                skill = load_skill_file(skills_dir, rel_path)
                skills[rel_path] = skill
    return skills