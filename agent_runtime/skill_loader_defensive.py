import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Any

@dataclass
class Skill:
    title: str
    meta: dict
    body: str
    goal: str | None = None
    validated_config: Any = None
    filename: str = ""

def load_skill(filepath: Path) -> Skill:
    raw = filepath.read_text(encoding="utf-8")
    parts = raw.split("---")
    if len(parts) < 3:
        raise ValueError(f"No valid YAML frontmatter found in {filepath.name}")
    header = yaml.safe_load(parts[1])
    if not isinstance(header, dict):
        raise ValueError(f"YAML frontmatter is not a dict in {filepath.name}")
    body = "---".join(parts[2:]).strip()
    title = str(header.get("title", filepath.stem))
    goal = header.get("goal")
    return Skill(title=title, meta=header, body=body, goal=goal, filename=filepath.name)
