#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# hooks/_lib.sh — SessionStart hook 公共库（v2026-06-30 抽取）
# ────────────────────────────────────────────────────────────
# 抽出 session-start 与 session-start-codex 的重复逻辑：
#   - orch SKILL.md 内容加载
#   - escape_for_json（bash 参数替换版，速度比 char-by-char 快数量级）
#   - session_context 模板拼装
# 调用方按 env var 分发 JSON schema：
#   CURSOR_PLUGIN_ROOT → additional_context（Cursor）
#   CLAUDE_PLUGIN_ROOT → hookSpecificOutput.additionalContext（Claude Code）
#   其他              → additionalContext（Copilot CLI / SDK 标准）
# ────────────────────────────────────────────────────────────

set -euo pipefail

# 自动初始化 PLUGIN_ROOT（消除调用方 3 行 boilerplate）
# 用法：source _lib.sh [auto|skip]
#   auto（默认）：从本脚本位置反推 PLUGIN_ROOT，导出到当前 shell
#   skip：不自动设置（调用方自己定义 PLUGIN_ROOT）
case "${1:-auto}" in
    auto)
        PLUGIN_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
        export PLUGIN_ROOT
        ;;
    skip) ;;
    *) echo "Usage: source _lib.sh [auto|skip]" >&2; return 1 ;;
esac

# 加载 orch SKILL.md 到变量
load_orch_content() {
    local plugin_root="${1:-}"
    if [ -z "$plugin_root" ]; then
        echo "Error: plugin_root is empty" >&2
        return 1
    fi
    cat "${plugin_root}/skills/orch/SKILL.md" 2>&1 || echo "Error reading orch skill"
}

load_orch_runtime_bundle() {
    local plugin_root="${1:-}"
    if [ -z "$plugin_root" ]; then
        echo "Error: plugin_root is empty" >&2
        return 1
    fi

    local refs_root="${plugin_root}/skills/orch/references"
    local files=(
        "${plugin_root}/skills/orch/SKILL.md"
        "${refs_root}/intent-schema.json"
        "${refs_root}/capability-registry.yaml"
        "${refs_root}/dag-rules.yaml"
        "${refs_root}/handoff-orch-schema.json"
        "${refs_root}/executor-contracts/direct-skill.json"
        "${refs_root}/executor-contracts/loop.json"
        "${refs_root}/executor-contracts/go.json"
    )
    # families/*.yaml — family-specific DAG rules (6 files)
    for fam_file in "${refs_root}/families"/*.yaml; do
        if [ -f "$fam_file" ]; then
            files+=("$fam_file")
        fi
    done
    # golden-traces/*.json — acceptance criteria examples (5 files)
    for trace_file in "${refs_root}/golden-traces"/*.json; do
        if [ -f "$trace_file" ]; then
            files+=("$trace_file")
        fi
    done

    for path in "${files[@]}"; do
        if [ -f "$path" ]; then
            printf '\n### %s ###\n' "${path#${plugin_root}/}"
            cat "$path"
            printf '\n'
        fi
    done
}

# Escape string for JSON embedding using bash parameter substitution.
# Each ${s//old/new} is a single C-level pass - orders of magnitude
# faster than the character-by-character loop this replaces.
escape_for_json() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\r'/\\r}"
    s="${s//$'\t'/\\t}"
    printf '%s' "$s"
}

# 构建 session_context 字符串（所有平台共享）
build_session_context() {
    local orch_content="$1"
    local orch_escaped
    orch_escaped=$(escape_for_json "$orch_content")
    printf '<EXTREMELY_IMPORTANT>\nYou have LoopEngine — the full-stack development engine with 33 skills.\n\norch v2 is a natural-language-first, family-first, rule-first multi-skill orchestrator.\nUse native description matching for single-skill tasks. Use orch behavior when the user goal clearly requires multiple complementary skills.\n\n**Below is the runtime orch bundle (skill + orchestration references). For all other skills, use the '\''Skill'\'' tool:**\n\n%s\n</EXTREMELY_IMPORTANT>' "$orch_escaped"
}

# 输出 SessionStart JSON（按 env var 路由 schema）
# Uses printf instead of heredoc to work around bash 5.3+ heredoc hang.
emit_session_start_json() {
    local session_context="$1"
    if [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
        # Cursor sets CURSOR_PLUGIN_ROOT (may also set CLAUDE_PLUGIN_ROOT)
        printf '{\n  "additional_context": "%s"\n}\n' "$session_context" | cat
    elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
        # Claude Code sets CLAUDE_PLUGIN_ROOT without COPILOT_CLI
        printf '{\n  "hookSpecificOutput": {\n    "hookEventName": "SessionStart",\n    "additionalContext": "%s"\n  }\n}\n' "$session_context" | cat
    else
        # Copilot CLI (sets COPILOT_CLI=1) or unknown platform — SDK standard format
        printf '{\n  "additionalContext": "%s"\n}\n' "$session_context" | cat
    fi
}