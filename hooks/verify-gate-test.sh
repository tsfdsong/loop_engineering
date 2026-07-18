#!/usr/bin/env bash
# ────────────────────────────────────────────────────────────
# hooks/verify-gate-test.sh — 验证 Gate 自测脚本（固化 Phase 1 的 16 项检查）
# ────────────────────────────────────────────────────────────
# 用途：CI 可调 / 改动 gate 逻辑后回归验证 / 确保阻断判定不退化
# 运行：bash hooks/verify-gate-test.sh
# 退出码：0 = 全部通过，1 = 有失败
# ────────────────────────────────────────────────────────────
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

PASS=0; FAIL=0; TOTAL=0

check() {
    TOTAL=$((TOTAL + 1))
    if [ "$1" = "$2" ]; then
        printf '  ✅ %s\n' "$3"
        PASS=$((PASS + 1))
    else
        printf '  ❌ %s (got=%s want=%s)\n' "$3" "$1" "$2"
        FAIL=$((FAIL + 1))
    fi
}

# 测试用 session ID（带 test- 前缀，便于清理）
TEST_SID="gate-test-$$"
export CLAUDE_SESSION_ID="$TEST_SID"
export CLAUDE_PROJECT_DIR="$PROJECT_ROOT"

cleanup() {
    rm -rf "$PROJECT_ROOT/.verify-state/$TEST_SID" 2>/dev/null || true
}
trap cleanup EXIT

printf '═══ 验证 Gate 自测（PID=%s）═══\n\n' "$$"

# ── T1: verify-state-init.sh ──
printf 'T1: SessionStart 初始化\n'
rm -rf ".verify-state/$TEST_SID"
bash hooks/verify-state-init.sh
check "$(cat ".verify-state/$TEST_SID/has_code_changes" 2>/dev/null)" "false" "init: has_code_changes=false"
check "$(cat ".verify-state/$TEST_SID/block_count" 2>/dev/null)" "0" "init: block_count=0"
check "$([ -f ".verify-state/$TEST_SID/session_started_at" ] && echo yes || echo no)" "yes" "init: session_started_at 存在"
check "$([ -f ".verify-state/$TEST_SID/verdict.json" ] && echo yes || echo no)" "no" "init: verdict.json 不预创建"

# ── T2: collector Write → has_code_changes=true ──
printf '\nT2: PostToolUse collector — Write 标记代码改动\n'
echo '{"tool_name":"Write","tool_input":{"file_path":"src/app.py","content":"x=1"}}' | bash hooks/verify-collector.sh
check "$(cat ".verify-state/$TEST_SID/has_code_changes")" "true" "collector Write → has_code_changes=true"

# ── T3: gate 无 verdict → 阻断 exit 2 ──
printf '\nT3: Stop gate — 有改动无 verdict → 阻断\n'
GATE_OUT="$(bash hooks/verify-gate.sh 2>/dev/null)"; GATE_EXIT=$?
check "$GATE_EXIT" "2" "gate 无verdict → exit 2"
check "$(cat ".verify-state/$TEST_SID/block_count")" "1" "gate block_count=1"
# JSON 有效性（独立验证，不用管道）
echo "$GATE_OUT" | python3 -c "import json,sys; d=json.loads(sys.stdin.readline()); assert sorted(d.keys())==['additionalContext']" 2>/dev/null
check "$?" "0" "gate JSON 有效 (strict schema: 只有 additionalContext)"

# ── T4: VERIFIED verdict → 放行 exit 0 + 重置计数 ──
printf '\nT4: Stop gate — VERIFIED verdict → 放行\n'
printf '{"status":"VERIFIED","reason":"","verifier":"self","timestamp":"2026-07-15T00:00:00Z"}' > ".verify-state/$TEST_SID/verdict.json"
printf '2' > ".verify-state/$TEST_SID/block_count"  # 模拟之前阻断过
bash hooks/verify-gate.sh >/dev/null 2>&1; GATE_EXIT=$?
check "$GATE_EXIT" "0" "gate VERIFIED → exit 0"
check "$(cat ".verify-state/$TEST_SID/block_count")" "0" "gate VERIFIED → block_count 重置"

# ── T5: FAILED verdict → 阻断 exit 2 ──
printf '\nT5: Stop gate — FAILED verdict → 阻断\n'
printf '{"status":"FAILED","reason":"2 tests failed","verifier":"self","timestamp":"2026-07-15T00:00:00Z"}' > ".verify-state/$TEST_SID/verdict.json"
printf '0' > ".verify-state/$TEST_SID/block_count"
bash hooks/verify-gate.sh >/dev/null 2>&1; GATE_EXIT=$?
check "$GATE_EXIT" "2" "gate FAILED → exit 2"

# ── T6: 无代码改动 → 放行 exit 0 ──
printf '\nT6: Stop gate — 无改动 → 放行（纯对话场景）\n'
printf 'false' > ".verify-state/$TEST_SID/has_code_changes"
bash hooks/verify-gate.sh >/dev/null 2>&1; GATE_EXIT=$?
check "$GATE_EXIT" "0" "gate 无改动 → exit 0"

# ── T7: 阻断 ≥3 次 → 软警告放行 exit 0 ──
printf '\nT7: Stop gate — 3次阻断后 → 软警告放行（防无限循环）\n'
printf 'true' > ".verify-state/$TEST_SID/has_code_changes"
rm -f ".verify-state/$TEST_SID/verdict.json"
printf '3' > ".verify-state/$TEST_SID/block_count"
SOFT_OUT="$(bash hooks/verify-gate.sh 2>/dev/null)"; GATE_EXIT=$?
check "$GATE_EXIT" "0" "gate 3次 → exit 0 (软警告)"
echo "$SOFT_OUT" | grep -q '已阻断 3 次' 2>/dev/null
check "$?" "0" "gate 软警告含 '已阻断 3 次'"

# ── T8: 目录不存在 → 降级放行 ──
printf '\nT8: 降级 — 状态目录不存在 → 静默放行\n'
export CLAUDE_SESSION_ID="gate-nonexistent-$$"
rm -rf ".verify-state/gate-nonexistent-$$" 2>/dev/null
bash hooks/verify-gate.sh >/dev/null 2>&1; GATE_EXIT=$?
check "$GATE_EXIT" "0" "gate 目录不存在 → exit 0"
export CLAUDE_SESSION_ID="$TEST_SID"  # 恢复

# ── T9: collector 空 stdin → 静默 exit 0 ──
printf '\nT9: 降级 — collector 空 stdin → 静默退出\n'
printf '' | bash hooks/verify-collector.sh; COLLECTOR_EXIT=$?
check "$COLLECTOR_EXIT" "0" "collector 空 stdin → exit 0"

# ── T10: collector Agent verdict 签名提取 ──
printf '\nT10: PostToolUse collector — Agent verdict 签名\n'
TEST_SID2="gate-test-agent-$$"
export CLAUDE_SESSION_ID="$TEST_SID2"
mkdir -p ".verify-state/$TEST_SID2"
echo '{"tool_name":"Agent","tool_result":"验证完成 <verdict:VERIFIED:全部通过>"}' | bash hooks/verify-collector.sh
STATUS=$(python3 -c "import json; print(json.load(open('.verify-state/$TEST_SID2/verdict.json'))['status'])" 2>/dev/null)
check "$STATUS" "VERIFIED" "collector Agent → status=VERIFIED"
REASON=$(python3 -c "import json; print(json.load(open('.verify-state/$TEST_SID2/verdict.json'))['reason'])" 2>/dev/null)
check "$REASON" "全部通过" "collector Agent → reason 干净提取"
rm -rf ".verify-state/$TEST_SID2"
export CLAUDE_SESSION_ID="$TEST_SID"

# ── T11: collector Bash test 命令 → evidence-log ──
printf '\nT11: PostToolUse collector — Bash test 命令 → 证据日志\n'
EVIDENCE_BEFORE=$(wc -l < ".verify-state/$TEST_SID/evidence-log.jsonl" 2>/dev/null | tr -d ' ' || printf '0')
echo '{"tool_name":"Bash","tool_input":{"command":"pytest -x tests/"}}' | bash hooks/verify-collector.sh
EVIDENCE_AFTER=$(wc -l < ".verify-state/$TEST_SID/evidence-log.jsonl" 2>/dev/null | tr -d ' ')
check "$((EVIDENCE_AFTER > EVIDENCE_BEFORE))" "1" "collector Bash pytest → evidence-log 追加"

# ── T12: collector Bash 非 test 命令 → 不追加 ──
printf '\nT12: PostToolUse collector — Bash 非验证命令 → 不追加\n'
EVIDENCE_BEFORE2=$(wc -l < ".verify-state/$TEST_SID/evidence-log.jsonl" 2>/dev/null | tr -d ' ')
echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | bash hooks/verify-collector.sh
EVIDENCE_AFTER2=$(wc -l < ".verify-state/$TEST_SID/evidence-log.jsonl" 2>/dev/null | tr -d ' ')
check "$EVIDENCE_BEFORE2" "$EVIDENCE_AFTER2" "collector Bash ls → evidence-log 不变"

# ── 结果汇总 ──
printf '\n═══════════════════════════════════════════\n'
printf '结果: \033[32m%s 通过\033[0m, \033[31m%s 失败\033[0m / 共 %s 项\n' "$PASS" "$FAIL" "$TOTAL"
printf '═══════════════════════════════════════════\n'

[ "$FAIL" -eq 0 ]
