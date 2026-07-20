# LoopEngine — 循环工程全家桶

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 **32** 个技能的开发引擎全家桶（**v2.0**：原 `orch` 已合并进 `go` Step 0 · family-first 路由）。

**Below is the full content of your 'loopengine:go' skill —— 你的全自动编排器（v2.0 · family-first · worktree 并发）。单技能任务由原生 description 匹配自动处理；跨模块/多步工程目标用 `/go`。**

go 在 Step 0 识别主 `scenario family`（review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test），组装 DAG，按 side-effect-first 委托 direct_skill / loop / go 自身。

## 安装方式

### 一键安装（推荐 · 所有平台）

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# 需要 Python ≥ 3.10；Windows 可用 python
```

`install.py` 自动 detect 本机 AI 工具，构建中央包，按官方插件路径部署 skills/hooks，并写入 MCP、AGENTS 规则与注册表（Claude / ZCode）。卸载：`python3 install.py uninstall`。

### 部署验证

```bash
python3 install.py install --check --json
python3 scripts/audit_tools.py
```

详见 [docs/INSTALL.md](docs/INSTALL.md) 与 [README.md](README.md)。

## 贡献

详见 CONTRIBUTING.md。
