# LoopEngine — 循环工程全家桶

## 如果你是 AI 代理

你有 LoopEngine：约 32 个技能。

- **单技能** → 靠 description 自动匹配  
- **跨模块 / 多步** → `/go`（Step 0 做 family-first 路由）  
- **单任务落地** → `/loop`（目标 + 验收 → 编码 ↔ 门禁 ↔ 自愈）

family 示例：`review` · `debug_fix` · `design_build` · `research_compare` · `web_qa` · `parallel_investigation` · `refactor` · `test`。

只读节点可直调技能；写节点委托 `loop` / `go`。

## 安装

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
# Python ≥ 3.10；Windows 可用 python
```

卸载：`python3 install.py uninstall`  
自检：`python3 install.py install --check --json` · `python3 scripts/audit_tools.py`

详见 [`docs/INSTALL.md`](docs/INSTALL.md)、[`README.md`](README.md)。贡献见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。
