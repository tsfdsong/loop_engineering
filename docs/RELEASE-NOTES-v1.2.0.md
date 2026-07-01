# v1.2.0 — 一体化（首次安装 + 版本更新合一）

> 标签: `v1.2.0` · 提交: `6ae5f0c` · 日期: 2026-07-01

## 概述

v1.2.0 把 `update.sh` 的更新功能完全合并到 `install.sh`，实现**首次安装 + 版本更新**的一体化。重新跑 `install.sh` 即可升级，无需单独的 `update.sh` 入口。新增 `--dry-run` / `--force` / `--help` 三个参数，调试能力大幅提升。

## 用户视角的变更

### 新增（Added）

- `bash install.sh` 智能模式：自动判断「未装/已装同版/已装旧版」并执行对应逻辑
- `--dry-run` 参数：只检查版本不实际安装（拉源码 + 输出计划）
- `--force` 参数：跳过 5 秒等待，强制重装（同版本也执行）
- `-h` / `--help` 参数：显示帮助

### 变更（Changed）

- 同版本检测由"无感重跑"改为"5 秒等待（防误触）"，`--force` 跳过
- AGENTS.md 章节加 `1./2./3./4./5.` 数字前缀（v6.10 升级版），install.sh awk pattern 同步修复

### 废弃（Removed）

- `update.sh`（84 行）：功能完全合并到 `install.sh`，脚本已删除
- 旧 v1.0.2 时代的 `scripts/zcode-mcp-ensure.sh`（已在 v1.1.0 移到 `docs/legacy/`）

## 迁移指南（v1.1.0 → v1.2.0）

**无需任何手动操作** — 重跑 install.sh 即可：

```bash
# 旧（v1.1.0）两步走：
# bash update.sh
# bash install.sh

# 新（v1.2.0）一步走：
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

智能模式会自动：
- 检测到 v1.1.0（已装旧版）→ 升级到 v1.2.0
- 同版本（v1.2.0）→ 5 秒等待（`--force` 跳过）

## 用法示例

| 场景 | 命令 |
|------|------|
| 首次安装 | `curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash` |
| 升级到最新版 | `curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash` |
| 只检查不安装 | `bash install.sh --dry-run` |
| 强制重装同版本 | `bash install.sh --force` |
| 显示帮助 | `bash install.sh -h` |

## 验证证据

| 验证项 | 结果 |
|------|------|
| `bash -n install.sh` 语法 | ✅ OK |
| `--help` 输出 | ✅ 显示 v1.2.0 头部 + 4 个用法 |
| `--dry-run` 输出计划 | ✅ "状态/计划/远端版本/技能数/工作目录" 5 项 |
| 默认模式端到端 | ✅ Step 0-6 全部成功，47 路径部署 |
| 5 条红线提取 | ✅ 用户交互/MCP/事实优先/摘要输出/完成前验证 全部正确 |
| 同版本 5 秒等待 | ✅ 触发；`--force` 跳过 |
| GitHub v1.2.0 release | ✅ 自动创建（仓库配置 auto-release） |

## 关联 commit

- `6ae5f0c` feat(install): v1.2.0 一体化（首次安装 + 版本更新合一）
- `b467190` fix(redlines): v6.10 用户交互红线第 5 条
- `90e192a` feat(install): v1.1.0 全面同步 + plugin 模板+overlay
- `2b82e1f` fix(install): Step 2a render_plugins.py 显示 stderr
- `550c074` chore(install): v1.1.0 收尾

## 致谢

感谢所有使用 LoopEngine 的开发者反馈。v1.2.0 解决了"update.sh 形同虚设"（curl 用户用不上）和"5 红线章节编号不兼容"两个长期痛点。

---

**如何应用此 release notes 到 GitHub UI**：

1. 打开 https://github.com/tsfdsong/loop_engineering/releases/tag/v1.2.0
2. 点击右上角 "Edit release"
3. 把上面"## 概述"到"## 致谢"之间的内容复制到 Description 框
4. 点击 "Update release" 保存
