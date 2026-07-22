# Design: Cursor 专用 AskUserQuestion MCP（本地网页点选）

> **日期**: 2026-07-22  
> **状态**: Approved（brainstorming）  
> **路径**: `docs/`（本仓库 `docs/superpowers/` 被 gitignore；与既有 `docs/2026-07-*-design.md` 对齐）  
> **范围**: **仅 Cursor**；共享 C2 / 其它平台安装与 MCP 默认集不受影响  
> **动机**: Cursor 无宿主 `AskUserQuestion`，却注入与 Claude/ZCode 相同的 C2（必须调该工具），导致决策点空转或 markdown 逃逸。

## Goal

在 Cursor 上提供 MCP 工具 `AskUserQuestion`（单选 + 多选、本地网页按钮点选），使 C2 决策点可真实完成，且其它平台与共享 `AGENTS.md` C2 正文不变。

## Acceptance Contract

- [ ] 经 Cursor 安装路径后，`~/.cursor/mcp.json`（及 Cursor plugin `mcp.json` 若同步）含 `loopengine-ask` server，工具列表可见 `AskUserQuestion`
- [ ] 单选：传入 2–4 选项且含推荐标记时，本地网页点选一项后，工具返回对应选项标识
- [ ] 多选：`multiSelect=true` 时，勾选 ≥1 项并确认后，工具返回所选列表
- [ ] 非法参数、超时、busy（并发第二次调用）时工具返回 error；文档与 Cursor 注入规则明确 **禁止** 因此改用 markdown 列出决策选项继续
- [ ] ZCode/Claude 安装合并结果及共享 `.plugin-template.json` 默认 `mcpServers` **不**包含 `loopengine-ask`；共享 `AGENTS.md` 的 INTERACTION-RULES（C2）正文无改动
- [ ] 单元/集成测试覆盖校验、HTTP 模拟点选、安装隔离；相关测试退出码 0

## Non-goals

- 不修改共享 `AGENTS.md` C2 文案，不引入跨平台「等价工具」抽象层
- 不把该能力挂进 jcodemunch / repomix / headroom
- 不做自由文本输入框；不将 markdown 决策点合法化为 Cursor 兜底
- 不支持单次调用多题；不依赖 Cursor `cursor_dialog`（当前仅 user rules，无选项 UI）
- 不为无浏览器/沙箱环境实现自动降级（见 Stop Escalation）

## Stop Escalation

- Cursor 若提供原生 `AskUserQuestion` 或等价选项 UI → 停止扩展本 MCP，评估退役或薄封装
- 无法在目标环境稳定打开系统浏览器 → 停止假设「网页即唯一交互」；回问是否接受受控降级（本 spec **默认不降级**）
- 发现其它平台误装或共享 template 被改入该 server → 视为隔离失败，先修安装边界再继续功能
- 工具 schema 与 Claude/ZCode 宿主字段严重冲突且技能大量硬编码 → 回问是否做「输入适配层」还是保持最小字段集

---

## 1. 背景与问题

| 事实 | 来源 |
|------|------|
| C2 要求决策必须调用 `AskUserQuestion`，禁止 markdown 文字列决策点 | `AGENTS.md` INTERACTION-RULES |
| Cursor 安装把同一段红线注入 `~/.cursor/rules/loopengine-interaction.mdc` | `scripts/loopengine_install/adapters/cursor.py` |
| Cursor 工具集无 `AskUserQuestion` | 本会话 MCP/工具枚举 |
| Kimi 等平台用 `skillInstructions` 做工具映射；Cursor overlay 无等价兜底 | `.kimi-plugin/plugin.json` vs `.cursor-plugin/plugin.json` |
| `cursor_dialog` 仅支持 user rule CRUD，无选项弹窗 | `cursor-app-control` 工具描述 |

结果：Cursor 上 Agent 要么空调失败，要么改用 markdown 选项却仍被 C2 判违规。

## 2. 已确认决策

| # | 决策 | 选择 |
|---|------|------|
| D1 | 成功标准 | 接近原生选择框体验（非纯 markdown） |
| D2 | 载体 | Cursor 专用独立 MCP |
| D3 | 点选 UI | 本地小网页（系统默认浏览器） |
| D4 | 命名与规则 | 工具名 `AskUserQuestion`；共享 C2 **一字不改**；仅 Cursor 安装接线 |
| D5 | 多选 | 首版同时支持单选 + 多选 |
| D6 | 实现形态 | 独立包/模块 `loopengine-ask`（不挂现有 MCP） |
| D7 | 失败策略 | 浏览器打不开 / 超时 → tool error；**不**降级 markdown |
| D8 | 并发 | 同时仅允许一个活跃提问；第二次 → busy error |
| D9 | 超时 | 默认 10 分钟 |

## 3. 架构

```
Cursor Agent 调用 AskUserQuestion
        │
        ▼
 loopengine-ask MCP（仅 ~/.cursor/mcp.json）
        │
        ├─ 校验：1 题 · 2–4 选项 · 推荐标记 · multiSelect?
        ├─ 起本地 HTTP（127.0.0.1 随机端口 + ephemeral token）
        ├─ 打开系统默认浏览器 → 按钮页
        └─ 阻塞等待选择（或超时 / busy）
                │
                ▼
        返回结构化 answers → Agent 继续
```

**隔离边界**

- 共享 `AGENTS.md` C2、其它平台 plugin/MCP 默认集不改
- 仅 `CursorAdapter.merge_mcp`（及 Cursor health）认识 `loopengine-ask`
- 不写入共享 `.plugin-template.json` 的 `mcpServers`

## 4. 组件

| 组件 | 职责 |
|------|------|
| MCP server `loopengine-ask` | 注册工具、参数校验、生命周期编排 |
| UI server | `127.0.0.1:<port>` 一页 HTML（单选按钮 / 多选 checkbox + 确认） |
| Browser opener | 打开该 URL（如 `webbrowser.open`） |
| Cursor install 接线 | `merge_mcp` 写入 command；health 校验在位 |
| 打包入口 | console_script 或 `python -m …`（实现期定） |

## 5. 工具契约

- **工具名**: `AskUserQuestion`
- **每次恰好 1 个问题**（多题分多次调用）
- **options**: 2–4 项；至少一项 label 含 `(推荐)` **或** 显式 `recommended: true`
- **multiSelect**: 默认 `false`（点一项即提交）；`true` 时至少选 1 项后点确认
- **返回**: 结构化 `answers`（含所选 option 标识列表）；具体字段名实现期可与常见宿主对齐，语义不变
- **禁止**: 自由文本输入

### 失败语义

| 情况 | 行为 |
|------|------|
| 参数非法 | 立即 tool error，不打开浏览器 |
| 浏览器打不开 | tool error；不降级 markdown |
| 超时（默认 10 min） | tool error `timeout`；可重试同一决策，不得改用 markdown 继续 |
| bind 失败 | 有限次换端口；仍失败 → tool error |
| 并发第二次 Ask | busy error |

### 安全

- 只监听 `127.0.0.1`
- URL 带一次性 token
- 默认不落盘用户选择（debug 日志默认关）

## 6. 安装与隔离

- Cursor：`scripts/loopengine_install/adapters/cursor.py` 的 `merge_mcp` 增加 `loopengine-ask`
- 共享 template / ZCode / Claude 合并逻辑：**不**添加该 server
- Health：Cursor 组件检查可验证 server 存在；其它平台检查不得要求该 server
- 可选：Cursor 侧短文说明「C2 在本平台由 MCP `AskUserQuestion` 兑现」——**不得**改写共享 C2 硬规则正文

## 7. 测试策略

| 层 | 内容 |
|----|------|
| 单元 | 参数校验、token、busy/超时状态机 |
| 集成 | 无真浏览器：HTTP 客户端模拟点选 → 返回正确 answers |
| 安装 | Cursor 写入该 server；其它平台/template 不含 |
| 回归 | 共享 C2 块与其它平台 inject 产物无无关 diff |

## 8. 否决的备选（R1.1）

| 备选 | 否决理由 |
|------|----------|
| 挂到 jcodemunch 等现有 MCP | 耦合 + 其它平台误装风险，违反「仅修 Cursor」 |
| 仅改 Cursor C2 为 markdown 合法 | 不符合「接近原生选择框」成功标准 |
| 复用 `cursor_dialog` | 当前无选项 UI API |

## 9. 机会成本（R1.2）

用「多一个 Cursor 专用 MCP 进程 + 小网页」换取：工具名对齐、共享红线零改、其它平台零波及、决策体验接近选择框。
