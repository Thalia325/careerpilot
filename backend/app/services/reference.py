from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.core.config import get_settings


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache
def load_job_profile_templates() -> list[dict]:
    settings = get_settings()
    return _load_json(settings.data_dir / "job_profile_templates.json")


@lru_cache
def load_job_graph_seed() -> dict:
    settings = get_settings()
    return _load_json(settings.data_dir / "job_graph_seed.json")


def find_best_template(title: str) -> dict:
    title_lower = title.lower()
    for template in load_job_profile_templates():
        if template["title"].lower() in title_lower or title_lower in template["title"].lower():
            return template
    for template in load_job_profile_templates():
        if any(keyword.lower() in title_lower for keyword in template["skills"][:2]):
            return template
    return load_job_profile_templates()[0]

