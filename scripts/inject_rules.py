#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# scripts/inject_rules.py — 把 LOOPENGINE-MANAGED 规则块注入目标文件
# ────────────────────────────────────────────────────────────
# 用法：python inject_rules.py <target_file> <block_dir>
#   - block_dir 下每个文件 = 一个规则块（含 BEGIN/END LOOPENGINE-MANAGED marker）
#   - 目标文件已存在则替换旧块（UPDATED），否则追加（APPENDED）
#   - 保留用户在其他章节的自定义内容
# 由 _common.sh::common_inject_rules_to_target() 调用（替代原内嵌 heredoc）。
# ────────────────────────────────────────────────────────────

import os
import re
import sys


def parse_marker(block_text: str) -> str | None:
    """从块文本提取 marker 类型（INTERACTION-RULES / MCP-RULES 等）。"""
    m = re.search(r'<!-- BEGIN LOOPENGINE-MANAGED (.+?) -->', block_text)
    return m.group(1) if m else None


def inject_block(content: str, marker_type: str, block: str) -> tuple[str, str]:
    """替换或追加单个 marker 块，返回 (新内容, 'UPDATED'|'APPENDED')。"""
    begin_marker = f"<!-- BEGIN LOOPENGINE-MANAGED {marker_type} -->"
    end_marker = f"<!-- END LOOPENGINE-MANAGED {marker_type} -->"
    # DOTALL 让 . 匹配换行；re.escape 避免特殊字符
    pattern = re.compile(
        re.escape(begin_marker) + r".*?" + re.escape(end_marker),
        re.DOTALL,
    )

    if pattern.search(content):
        # lambda 避免 re.sub 把 block 中的反斜杠（如 \U）当转义序列
        return pattern.sub(lambda _m: block, content), "UPDATED"

    # 追加模式：保证块前有足够空行
    if content and not content.endswith("\n"):
        content += "\n"
    if content and not content.endswith("\n\n"):
        content += "\n"
    return content + block + "\n", "APPENDED"


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <target_file> <block_dir>", file=sys.stderr)
        sys.exit(2)

    target, block_dir = sys.argv[1], sys.argv[2]

    if not os.path.isdir(block_dir):
        print(f"  ❌ 块目录不存在: {block_dir}", file=sys.stderr)
        sys.exit(1)

    content = ""
    if os.path.isfile(target):
        with open(target, 'r', encoding='utf-8') as f:
            content = f.read()

    applied = 0
    for fname in sorted(os.listdir(block_dir)):
        block_path = os.path.join(block_dir, fname)
        if not os.path.isfile(block_path):
            continue
        with open(block_path, 'r', encoding='utf-8') as f:
            block = f.read()
        marker = parse_marker(block)
        if not marker:
            continue
        content, action = inject_block(content, marker, block)
        print(f"  [{marker}] {action}")
        applied += 1

    if applied == 0:
        print(f"  ⚠ 未应用任何块到 {target}", file=sys.stderr)
        sys.exit(1)

    # 原子写
    tmp = target + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(content)
        os.replace(tmp, target)
    except OSError as e:
        print(f"  ❌ 写入 {target} 失败: {e}", file=sys.stderr)
        if os.path.exists(tmp):
            os.remove(tmp)
        sys.exit(1)

    print(f"✅ Applied {applied} blocks to {target}")


if __name__ == '__main__':
    main()