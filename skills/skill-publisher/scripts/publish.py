#!/usr/bin/env python3
"""发布一个本地技能到平台。支持指定目录路径或 .zip 压缩包。"""

from __future__ import annotations

import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _lib import (  # noqa: E402
    SKILL_MD, APIError,
    extract_slug_from_path, format_details, load_config,
    pack_skill_dir, parse_skill_md, publish_skill_api, validate_before_publish,
)


def _resolve_publish_input(p: Path) -> tuple[bytes, Path, str]:
    """解析发布输入：目录或 zip。返回 (zip_bytes, source_dir, slug)。

    - 目录：就地校验 SKILL.md → 打包 → 返回 zip
    - zip 文件：打开校验 SKILL.md 存在且格式正确 → 直接使用该 zip
    """
    if p.suffix.lower() == ".zip":
        if not p.is_file():
            print(f"❌ 文件不存在: {p}")
            sys.exit(1)
        zip_bytes = p.read_bytes()
        # 校验 zip 中包含 SKILL.md
        with zipfile.ZipFile(p) as zf:
            names = zf.namelist()
            # 考虑包裹一层目录的情况（my-skill/SKILL.md）
            candidates = [n for n in names if n.endswith("/" + SKILL_MD) or n == SKILL_MD]
            if not candidates:
                print(f"❌ zip 中未找到 {SKILL_MD} 文件")
                sys.exit(1)
            md_entry = min(candidates, key=len)  # 优先根目录
            content = zf.read(md_entry).decode("utf-8")
            # 提取 slug（从 SKILL.md 或 zip 内容目录名）
            slug = ""
            if md_entry != SKILL_MD:
                slug = md_entry.split("/")[0]
            source_dir = p  # 无实际目录，用 zip 路径标识
        return zip_bytes, source_dir, slug

    # 目录模式（现有逻辑）
    skill_dir = p.expanduser().resolve()
    if not skill_dir.is_dir():
        print(f"❌ 路径不存在或不是目录: {p}")
        sys.exit(1)
    md_path = skill_dir / SKILL_MD
    if not md_path.exists():
        print(f"❌ 目录中未找到 {SKILL_MD}: {skill_dir}")
        sys.exit(1)
    content = md_path.read_text(encoding="utf-8")
    slug = extract_slug_from_path(skill_dir)
    zip_bytes = pack_skill_dir(skill_dir)
    print(f"📦 已打包 {skill_dir.name}（{len(zip_bytes):,} bytes）")
    return zip_bytes, skill_dir, slug


def publish(
    skill_path: str,
    slug_override: str = "",
    version: str = "1.0.0",
    category: str = "general",
    kind: str = "tool",
) -> None:
    # 解析输入
    zip_bytes, source, inferred_slug = _resolve_publish_input(Path(skill_path))

    # 从打包结果中读 SKILL.md 内容用于预校验
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        md_names = [n for n in zf.namelist() if n.endswith("/" + SKILL_MD) or n == SKILL_MD]
        content = zf.read(min(md_names, key=len)).decode("utf-8") if md_names else ""

    slug = slug_override or inferred_slug

    # 本地预校验
    errors = validate_before_publish(content, slug)
    if errors:
        print("❌ 本地预校验未通过，请修改后重试：")
        print(format_details(errors))
        sys.exit(1)

    # 调 API 发布
    url, token = load_config()
    if not token:
        print("❌ 未配置 Token，请先运行: python config.py set --token <你的token>")
        sys.exit(2)

    try:
        publish_skill_api(
            url=url, token=token,
            slug=slug, version=version, zip_bytes=zip_bytes,
            category=category, kind=kind,
        )
    except APIError as e:
        if e.status_code == 401:
            print("❌ 认证失败，Token 无效或已过期，请在平台重新生成")
            sys.exit(2)
        if isinstance(e.detail, dict):
            msg = e.detail.get("message", str(e))
            details = e.detail.get("details", [])
            print(f"❌ {msg}")
            if details:
                print(format_details(details))
        else:
            print(f"❌ 发布失败: {e.detail}")
        sys.exit(1)

    platform_url = url.rstrip("/")
    print(f"✅ 发布成功！")
    print(f"   技能页: {platform_url}/skills/{slug}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="发布本地技能到平台，支持目录或 .zip 文件。"
    )
    parser.add_argument("path", type=str, help="技能目录路径或 .zip 压缩包")
    parser.add_argument("--slug", type=str, default="", help="slug（默认从 SKILL.md 读取）")
    parser.add_argument("--version", type=str, default="1.0.0", help="版本号，默认 1.0.0")
    parser.add_argument("--category", type=str, default="general", help="分类")
    parser.add_argument("--kind", type=str, default="tool", help="类型 tool/agent/framework")
    args = parser.parse_args()

    publish(
        args.path,
        slug_override=args.slug,
        version=args.version,
        category=args.category,
        kind=args.kind,
    )
