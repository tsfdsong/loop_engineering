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

# 加载 lessons-learned.md 最近 7 天的 L# 条目（教训段）
# 目的：让每个新会话自动"记得"最近的真实事故，避免重复犯错
# v1.3.2 新增（背景：specs 卡死事故 L#002 揭示 AI 不会主动读教训库）
#
# 行为契约：
#   - 解析 docs/lessons-learned.md 中所有 `## 📚 L#NNN · YYYY-MM-DD · ...` 标题
#   - 取日期 >= (今天 - 7 天) 的条目
#   - 每条只保留"教训（X 条）"段（避免 token 爆炸）
#   - 找不到任何匹配 → 输出提示信息而非静默（透明降级）
load_recent_lessons() {
    local plugin_root="${1:-}"
    local lessons_file="${plugin_root}/docs/lessons-learned.md"
    local days="${LE_LESSONS_DAYS:-7}"

    if [ -z "$plugin_root" ] || [ ! -f "$lessons_file" ]; then
        printf '<!-- lessons-learned.md unavailable at %s -->\n' "$lessons_file"
        return 0
    fi

    local cutoff
    cutoff=$(date -u -d "${days} days ago" +%Y-%m-%d 2>/dev/null || date -u -v-${days}d +%Y-%m-%d 2>/dev/null)
    if [ -z "$cutoff" ]; then
        # date 命令两个版本都失败时降级（Git Bash / BSD 都支持其一）
        printf '<!-- lessons-learned.md: date command unavailable, skipping -->\n'
        return 0
    fi

    # 找所有 L# 标题 + 起始行号
    local in_recent=0
    local in_lessons_section=0
    local output=""
    local printed_header=0

    while IFS= read -r line; do
        # 匹配 L# 标题：## 📚 L#NNN · YYYY-MM-DD · ...
        if [[ "$line" =~ ^##\ 📚\ L#[0-9]+\ ·\ ([0-9]{4}-[0-9]{2}-[0-9]{2}) ]]; then
            local entry_date="${BASH_REMATCH[1]}"
            if [[ "$entry_date" > "$cutoff" || "$entry_date" == "$cutoff" ]]; then
                in_recent=1
                in_lessons_section=0
                if [ $printed_header -eq 0 ]; then
                    output+=$'\n### 最近事故教训（最近 '"$days"' 天，AGENTS.md §1.10 测试纪律）###\n'
                    output+='<!-- 自动注入（hooks/_lib.sh load_recent_lessons），AI 必读 -->\n'
                    printed_header=1
                fi
                output+=$'\n'"$line"$'\n'
            else
                in_recent=0
                in_lessons_section=0
            fi
            continue
        fi

        # 只在 recent 条目内处理
        if [ $in_recent -eq 1 ]; then
            # 遇到下一个 L# → 结束当前
            if [[ "$line" =~ ^##\ 📚\ L#[0-9]+ ]]; then
                in_recent=0
                in_lessons_section=0
                continue
            fi
            # 进入"教训"段
            if [[ "$line" =~ ^###\ 教训 ]]; then
                in_lessons_section=1
                output+="$line"$'\n'
                continue
            fi
            # 离开教训段（进入验证或下一个 ###）
            if [ $in_lessons_section -eq 1 ] && [[ "$line" =~ ^###\ 验证 || "$line" =~ ^###\ [^\ ] ]] && [[ ! "$line" =~ ^###\ 教训 ]]; then
                in_lessons_section=0
                # 教训段结束，再继续读但丢弃（直到下一个 L#）
            fi
            if [ $in_lessons_section -eq 1 ]; then
                output+="$line"$'\n'
            fi
        fi
    done < "$lessons_file"

    if [ $printed_header -eq 0 ]; then
        printf '<!-- lessons-learned.md: 无最近 %s 天的 L# 条目（cutoff=%s） -->\n' "$days" "$cutoff"
    else
        printf '%s' "$output"
    fi
}

# 构建 session_context 字符串（所有平台共享）
# v1.3.2 扩展：注入 lessons 到 EXTREMELY_IMPORTANT 块尾部
#
# 注意：格式串里的换行必须用字面 \\n（两字符），不能用 \n。
# 原因：printf 会把 \n 解释成真实 0x0a，但 orch_escaped/lessons_escaped 里的换行
# 已是字面 \\n（经 escape_for_json 转义）。若格式串产生真实 0x0a，整个 session_context
# 塞进 JSON 字符串值后会违反 JSON 规范（控制字符 0x00-0x1F 必须转义），导致 ZCode
# strict schema 校验失败（diagnosing-hooks pitfall #8）。详见 L#006 根因 B。
build_session_context() {
    local orch_content="$1"
    local lessons_content="${2:-}"
    local orch_escaped lessons_escaped=""
    orch_escaped=$(escape_for_json "$orch_content")
    if [ -n "$lessons_content" ]; then
        lessons_escaped=$(escape_for_json "$lessons_content")
    fi
    printf '<EXTREMELY_IMPORTANT>\\nYou have LoopEngine — the full-stack development engine with 33 skills.\\n\\norch v2 is a natural-language-first, family-first, rule-first multi-skill orchestrator.\\nUse native description matching for single-skill tasks. Use orch behavior when the user goal clearly requires multiple complementary skills.\\n\\n**Below is the runtime orch bundle (skill + orchestration references). For all other skills, use the '\''Skill'\'' tool:**\\n\\n%s\\n%s\\n</EXTREMELY_IMPORTANT>' "$orch_escaped" "$lessons_escaped"
}

# 输出 SessionStart JSON（按 env var 路由 schema）
# Uses printf instead of heredoc to work around bash 5.3+ heredoc hang.
#
# 路由优先级（关键：ZCode 必须在 Claude 之前判断）：
#   ZCode 同时设置 ZCODE_PLUGIN_ROOT 和 CLAUDE_PLUGIN_ROOT。若 CLAUDE 分支在前，
#   ZCode 会误入 Claude 嵌套 schema（hookSpecificOutput），触发 ZCode strict JSON
#   校验失败（diagnosing-hooks pitfall #8），导致 hook.run.failed。
#   因此 ZCode 分支必须置顶。详见 L#006。
emit_session_start_json() {
    local session_context="$1"
    if [ -n "${ZCODE_PLUGIN_ROOT:-}" ] && [ -z "${COPILOT_CLI:-}" ]; then
        # ZCode sets ZCODE_PLUGIN_ROOT (同时也会设 CLAUDE_PLUGIN_ROOT，必须优先匹配)
        # ZCode strict schema 期望顶层 additionalContext（非 hookSpecificOutput 嵌套）
        printf '{\n  "additionalContext": "%s"\n}\n' "$session_context" | cat
    elif [ -n "${CURSOR_PLUGIN_ROOT:-}" ]; then
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