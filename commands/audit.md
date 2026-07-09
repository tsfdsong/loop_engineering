---
description: 运行 LoopEngine 6 维度部署审计
allowed-tools: Bash
---

使用 `python3 scripts/audit_tools.py` 运行部署审计。

## 参数

- `--json`：CI 友好 JSON 输出
- `--tool <claude-code|zcode|cursor>`：只检查单工具
- `--verbose`：显示详细 detail

## 退出码

- `0`：OK / 仅 warnings
- `1`：有 error 级问题（schema 不合规）
- `2`：参数错误

## 6 维度

| 维度 | 检查 | 严重度 |
|------|------|--------|
| A | 工具部署目录完整性 | 高 |
| B | 技能 SKILL.md frontmatter | info |
| C | 9 条红线 marker 哨兵 | info |
| D | MCP 工具可用性（jcodemunch/repomix/headroom） | 中 |
| E | 版本一致性（template/package/marketplace） | 中 |
| F | 渲染后 plugin.json schema | 低 |
