# P0 Spike: Claude `installed_plugins.json`

> **日期**: 2026-07-20  
> **分支**: `go-plugin-shaped-install-py`  
> **状态**: **LIVE_REGISTERED · PENDING_SESSION** — 已写入 known_marketplaces + installed_plugins；需 Claude Code 新会话确认加载

## 本机官方条目（只读取证）

`~/.claude/plugins/installed_plugins.json`：

```json
{
  "version": 2,
  "plugins": {
    "document-skills@anthropic-agent-skills": [
      {
        "scope": "user",
        "installPath": "/Users/tangsong/.claude/plugins/cache/anthropic-agent-skills/document-skills/<hash>",
        "version": "<hash>",
        "installedAt": "<iso8601>",
        "lastUpdated": "<iso8601>",
        "gitCommitSha": "<optional>"
      }
    ]
  }
}
```

`known_marketplaces.json` 条目形：

```json
{
  "anthropic-agent-skills": {
    "source": { "source": "github", "repo": "anthropics/skills" },
    "installLocation": "~/.claude/plugins/marketplaces/anthropic-agent-skills",
    "lastUpdated": "<iso8601>"
  }
}
```

Marketplace 元数据：`marketplaces/<id>/.claude-plugin/marketplace.json`（`plugins[]` 含 `name` / `source` / `skills`）。

## 计划写入形状（与 plan 锁定一致）

| 字段 | 值 |
|------|-----|
| marketplace id | `loopengine-local` |
| plugin key | `loopengine@loopengine-local` |
| installPath | `~/.claude/plugins/cache/loopengine-local/loopengine/<version>/` |
| known_marketplaces.source | `{ "source": "directory", "path": "<marketplace dir>" }` |

## 步骤：Live 注册（已执行 2026-07-20）

已创建：

- `~/.claude/plugins/marketplaces/loopengine-local/`（marketplace.json + plugins/loopengine）
- `~/.claude/plugins/cache/loopengine-local/loopengine/0.0.1-spike/`（含 using-loopengine）
- `known_marketplaces.json` 键 `loopengine-local`（`source.directory`）
- `installed_plugins.json` 键 `loopengine@loopengine-local`

**待你**：新开 Claude Code 会话，确认能否使用/看到 loopengine / using-loopengine。回：`Claude spike: PASS` 或 `FAIL`。

## 闸门

- Schema + 磁盘注册已完成。  
- **Session PASS** 建议在删旧安装路径前确认；若 directory source 被拒，改试其它 installPath 并更新本文件。
