from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

import yaml


@dataclass
class ParsedSkill:
    filename: str
    meta: Dict[str, Any]
    body: str


def parse_frontmatter(md_text: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter of the form:

    ---
    key: value
    ---
    markdown body...

    Returns (meta, body). If no frontmatter, meta={} and body=whole text.
    """
    text = md_text.lstrip()
    if not text.startswith("---"):
        return {}, md_text

    lines = md_text.splitlines()
    if not lines:
        return {}, md_text

    if lines[0].strip() != "---":
        return {}, md_text

    # find closing ---
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        # malformed frontmatter; treat as no frontmatter
        return {}, md_text

    yaml_block = "\n".join(lines[1:end_idx]).strip()
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")

    meta = yaml.safe_load(yaml_block) if yaml_block else {}
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ValueError("YAML frontmatter must be a mapping/dict.")

    return meta, body