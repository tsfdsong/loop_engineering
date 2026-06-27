#!/usr/bin/env python3
"""扫描本地技能目录，返回技能清单（JSON）。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    SCAN_DIRS, SKILL_MD, SkillPreview, ValidationFailed,
    extract_slug_from_path, parse_skill_md, validate_before_publish,
)


def scan_dir(d: Path) -> list[SkillPreview]:
    results: list[SkillPreview] = []
    if not d.exists():
        return results

    for child in sorted(d.iterdir()):
        if not child.is_dir():
            continue
        md = child / SKILL_MD
        if not md.exists():
            # 嵌套一层（如 .hermes/skills/category/skill-name）
            for grandchild in sorted(child.iterdir()):
                if grandchild.is_dir() and (grandchild / SKILL_MD).exists():
                    results.append(make_preview(grandchild))
            continue
        results.append(make_preview(child))
    return results


def make_preview(skill_dir: Path) -> SkillPreview:
    md = skill_dir / SKILL_MD
    content = md.read_text(encoding="utf-8") if md.exists() else ""
    slug = extract_slug_from_path(skill_dir)
    file_count = sum(1 for _ in skill_dir.rglob("*") if _.is_file())

    sp = SkillPreview(path=str(skill_dir), name=slug, file_count=file_count)

    try:
        fm, _ = _parse_frontmatter_safe(content)
        sp.name = fm.get("name", slug) if isinstance(fm, dict) else slug
        sp.description = fm.get("description", "") if isinstance(fm, dict) else ""
    except Exception:
        sp.description = "(无法读取 frontmatter)"

    errors = validate_before_publish(content, slug)
    if errors:
        sp.valid = False
        sp.errors = errors

    return sp


def _parse_frontmatter_safe(content: str) -> tuple:
    """容错版 frontmatter 解析，不抛异常。"""
    try:
        return parse_skill_md(content)
    except ValidationFailed:
        return ({}, "")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="扫描本地技能目录")
    parser.add_argument("--dir", type=str, nargs="*", default=[], help="额外扫描的自定义路径")
    args = parser.parse_args()

    dirs = list(SCAN_DIRS)
    for d in args.dir:
        dirs.append(Path(d).expanduser().resolve())

    all_skills: list[SkillPreview] = []
    seen: set[str] = set()
    for d in dirs:
        for sp in scan_dir(d):
            if sp.path not in seen:
                seen.add(sp.path)
                all_skills.append(sp)

    output = []
    for sp in all_skills:
        item: dict = {
            "path": sp.path,
            "name": sp.name,
            "description": sp.description[:200],
            "file_count": sp.file_count,
            "valid": sp.valid,
        }
        if not sp.valid:
            item["errors"] = [{"field": e.field, "reason": e.reason} for e in sp.errors]
        output.append(item)

    print(json.dumps(output, ensure_ascii=False, indent=2))
