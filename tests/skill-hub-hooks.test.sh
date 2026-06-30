#!/usr/bin/env bash
# tests/skill-hub-hooks.test.sh
# 验证 session-start hook 输出符合 schema

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Testing skillhub-bootstrap.sh ==="

# Test 1: 输出是有效 JSON
OUTPUT=$(bash "${PLUGIN_ROOT}/skills/skill-hub/hooks/skillhub-bootstrap.sh" 2>&1)
if echo "$OUTPUT" | node -e "try { JSON.parse(require('fs').readFileSync(0, 'utf8')); console.log('valid'); } catch(e) { console.error('invalid'); process.exit(1); }" 2>/dev/null; then
  echo "Test 1: Output is valid JSON"
else
  echo "Test 1 FAIL: Output is not valid JSON"
  echo "First 200 chars: $(echo "$OUTPUT" | head -c 200)"
  exit 1
fi

# Test 2: 包含 skill-hub 内容
if echo "$OUTPUT" | grep -q "skill-hub"; then
  echo "Test 2: Contains skill-hub content"
else
  echo "Test 2 FAIL: Missing skill-hub content"
  exit 1
fi

# Test 3: 包含 EXTREMELY_IMPORTANT 包装
if echo "$OUTPUT" | grep -q "EXTREMELY_IMPORTANT"; then
  echo "Test 3: Contains EXTREMELY_IMPORTANT wrapper"
else
  echo "Test 3 FAIL: Missing EXTREMELY_IMPORTANT wrapper"
  exit 1
fi

echo ""
echo "All skill-hub-hooks tests passed"
