# 贡献指南

面向**本仓库贡献者**。终端用户看 `README.md`；AI 规则看 `AGENTS.md`。

---

## 硬约束：工具 / 模型无关

| 允许 | 禁止 |
|------|------|
| SKILL 主流程写「宿主工具 / 主 agent」 | 主流程写死 ZCode / Claude / Cursor |
| MCP 主推项目根 `.mcp.json`，附录列已测路径 | 主流程只认某一个用户级路径 |
| 降级用 Primary / Secondary / Tertiary + `.loopengine.yaml` | 写死具体模型名 |
| hooks 覆盖多工具 | 只注册单一工具 |

附录路径可写在 `skills/go/references/runtime-config.md` 等。

### PR 自检

- [ ] 主流程无具体工具名（附录除外）  
- [ ] 降级链无具体模型名  
- [ ] MCP 不写死单一工具路径  
- [ ] hooks 支持多目标  

---

## 开发

```bash
git clone https://github.com/tsfdsong/loop_engineering
cd loop_engineering
python3 install.py install --force
python3 scripts/audit_tools.py
python3 install.py install --dry-run
```

- 改 `AGENTS.md` 的 H2 标题 → 同步 `scripts/_lib/redline_markers.txt`  
- commit 用 conventional commits（`feat:` / `fix:` / `docs:` …）

---

## 文档分工

| 文件 | 给谁 | 内容 |
|------|------|------|
| `README.md` | 用户 | 介绍、安装、上手 |
| `AGENTS.md` | AI | 红线与自检 |
| `CONTRIBUTING.md` | 贡献者 | 本文件 |
| `docs/INSTALL.md` | 用户/开发 | 安装详规 |
| `docs/mcp-setup-guide.md` | 用户 | MCP 配置 |
| `docs/lessons-learned.md` | 开发 | 事故教训 |
| `docs/*-design.md` | 开发 | 仍有效的设计真源 |

不要把安装说明、历史流水账塞进 `AGENTS.md`。

---

## 联系

- Issues: https://github.com/tsfdsong/loop_engineering/issues  
- Discussions: https://github.com/tsfdsong/loop_engineering/discussions  
