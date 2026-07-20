# P0 Spike: Cursor `plugins/local`

> **日期**: 2026-07-20  
> **分支**: `go-plugin-shaped-install-py`  
> **状态**: **PASS via install.py** — 2026-07-20 用 `python3 install.py install --only=cursor,claude,zcode` 实装验证通过（见同批验证记录）

## 环境

- macOS · Cursor plugins 根：`~/.cursor/plugins/`
- 官方插件样例：`~/.cursor/plugins/cache/cursor-public/postman/...`（含 `.cursor-plugin/plugin.json` + `skills/`）
- `~/.cursor/plugins/local/` 原先为空目录（系统已预留）

## 步骤 1：最小包（已执行）

路径：`~/.cursor/plugins/local/loopengine-spike/`

```
.cursor-plugin/plugin.json   # name=loopengine-spike, skills=./skills/
skills/using-loopengine/SKILL.md
```

对照 Postman：官方包亦为「包根 + `.cursor-plugin/plugin.json` + `skills/`」；local 与 cache 布局对齐。

## 步骤 2：人工验证（待你）

请 **新开一个 Cursor Agent 会话**，发送：

> Load the skill `using-loopengine` from the loopengine-spike local plugin (if available) and summarize LoopEngine’s core instincts in 3 bullets.

判定：

| 结果 | 条件 |
|------|------|
| **PASS** | Agent 能引用/加载 `using-loopengine` 内容（或明确来自 local plugin） |
| **FAIL** | 完全找不到该 skill / 仅能从旧平铺 `~/.cursor/skills/` 加载且 local 无效 |

把结果回我：`Cursor spike: PASS` 或 `Cursor spike: FAIL`（可附 Cursor 版本）。

## 闸门

- FAIL → **停止**整份 plan（不删除平铺部署）。  
- PASS → 本文件改状态为 PASS 并 commit，继续 Task 2/3。

## 备注

尚未验证 hooks 是否从 `plugins/local` 加载；P1 Cursor Adapter 再补 hooks 抽检。
