#!/usr/bin/env python3
"""Run lightweight structural checks for the standalone project."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "SKILL.md",
    "通用硬规则.md",
    "事实库.example.md",
    "deep-interview-candidate/SKILL.md",
    "job_selection/SKILL.md",
    "templates/resume_template.py",
    "templates/sample_resume.json",
]


def check_frontmatter(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise RuntimeError(f"Skill frontmatter invalid: {path.relative_to(ROOT)}")
    header = text.split("\n---\n", 1)[0]
    if "name:" not in header or "description:" not in header:
        raise RuntimeError(f"Skill metadata incomplete: {path.relative_to(ROOT)}")


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).exists()]
    if missing:
        raise RuntimeError(f"Missing required files: {', '.join(missing)}")

    for skill in ROOT.rglob("SKILL.md"):
        check_frontmatter(skill)

    with (ROOT / "templates/sample_resume.json").open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not data.get("profile") or not data.get("sections"):
        raise RuntimeError("Sample resume JSON lacks profile or sections")

    subprocess.run(
        [sys.executable, str(ROOT / "scripts/publish_check.py")],
        cwd=ROOT,
        check=True,
    )
    print("Project checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

