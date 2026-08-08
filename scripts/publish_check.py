#!/usr/bin/env python3
"""Fail when publishable project files appear to contain candidate-specific data."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".md", ".py", ".json", ".yaml", ".yml", ".txt", ".toml"}
IGNORED_PARTS = {".git", ".venv", "__pycache__"}
ALLOWED_EMAILS = {"candidate@example.com"}
ALLOWED_PHONE = "138-0000-0000"

CHECKS = {
    "可能的绝对 Windows 路径": re.compile(r"[A-Za-z]:[\\/](?:Users|Documents|Desktop|04resume)\b", re.I),
    "可能的身份证号": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "可能的真实手机号": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "可能的真实邮箱": re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I),
}


def iter_publishable_files() -> list[Path]:
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in IGNORED_PARTS for part in path.parts):
            continue
        result.append(path)
    return result


def main() -> int:
    findings: list[str] = []
    for path in iter_publishable_files():
        rel = path.relative_to(ROOT)
        if path.suffix.lower() == ".tex":
            findings.append(f"仍存在 TeX 模板：{rel}")
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8")
        for label, pattern in CHECKS.items():
            for match in pattern.finditer(text):
                value = match.group(0)
                if value in ALLOWED_EMAILS or value == ALLOWED_PHONE:
                    continue
                findings.append(f"{label}：{rel} -> {value}")

    if findings:
        print("Publish check failed:")
        print("\n".join(f"- {item}" for item in findings))
        return 1
    print("Publish check passed: no candidate-specific data or TeX templates found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
