#!/usr/bin/env python3
# ────────────────────────────────────────────────────────────
# skills/drawio-skill/scripts/_graph_utils.py — drawio-skill 脚本公共图工具
# ────────────────────────────────────────────────────────────
# 单一真源（clean-code 维度 4 · DRY 真义）：
#   - transitive_reduce：原 5 份 100% 重复实现（pyimports / pyclasses / jsimports /
#     rustimports / goimports），统一为 1 处
#
# 5 个 import scanner 通过 `from _graph_utils import transitive_reduce` 复用
# ────────────────────────────────────────────────────────────

import re
import subprocess
import sys


def transitive_reduce(nodes, edges):
    """Drop edges implied by a longer path, via Graphviz `tred`.

    原 5 份相同实现的单一真源。失败时（tred 不可用）保留全部 edges 并 stderr 告警。
    """
    idx = {n: i for i, n in enumerate(nodes)}
    dot = "digraph{" + "".join(f"{idx[s]}->{idx[t]};" for s, t in edges) + "}"
    try:
        out = subprocess.run(
            ["tred"], input=dot, capture_output=True,
            text=True, check=True
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        sys.stderr.write(f"warning: tred unavailable, keeping all edges ({exc})\n")
        return edges
    rev = {i: n for n, i in idx.items()}
    return [
        (rev[int(a)], rev[int(b)])
        for a, b in re.findall(r"(\d+)\s*->\s*(\d+)", out)
    ]