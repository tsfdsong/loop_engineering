# Goal-first 子任务执行路由（go 编排）

> 状态：**已对齐 · 待 implementation plan**  
> 日期：2026-07-21  
> 范围：ZCode / Claude Code / OpenCode 桌面·TUI 交互；**不含** ZCode CLI headless（`--prompt` / `--target`）集成。

---

## 1. 背景与问题

LoopEngine `/go` 负责多任务编排（family、DAG、worktree、汇合）。子任务落地需要**执行器**：谁负责「跑完、验完、续轮」。

此前讨论偏了方向（CLI spike、用户手选 `/goal` vs `/loop`）。本设计采用统一范式：

- **Goal-first**：宿主若支持原生 Goal 机制，子任务**默认**走 Goal。
- **loop 降级**：Goal 失败或停滞时，再切 LoopEngine **loop** 技能。
- **loop-default**：不支持 Goal 的宿主（如 Cursor），子任务**默认** loop。

---

## 2. 目标与非目标

### 目标

- 定义 go → 子任务的**执行器路由**（Goal vs loop）。
- 列出 Goal-capable 宿主及 OpenCode 的 core / 插件分档。
- 定义 Goal → loop **降级触发**与 handoff 字段。
- 避免 Goal 与 loop **双主控**重复验证。

### 非目标

- 不在 LoopEngine 插件内复制 Goal runtime。
- 不集成 ZCode CLI `--target` / `zcode_runner` 程序化调用。
- 不改变 go 上游（brainstorming、DAG 拆分、L0 复杂度）职责边界。

---

## 3. 核心范式

```
/go 拆分子任务（每包含 goal + acceptance · thin-loop 契约）
        │
        ▼
 detect_executor(host)
        │
   ┌────┴────┐
   │ Goal-   │  loop-default
   │ first   │  (Cursor 等)
   └────┬────┘
        │
        ▼
 /goal replace <objective>     （或平台等价命令）
 objective 含可验证验收条件
        │
   ┌────┴────────────────────────┐
   │ achieved                    │ fail / stagnation
   ▼                             ▼
 handoff 回 go              clear/pause goal
                             → loop 技能（degraded_from=goal）
                             → handoff 回 go
```

**一层一主控**：Goal 活跃期间不得同时以 loop 门禁为主控；降级到 loop 前须 clear/pause Goal。

---

## 4. Goal-capable 宿主表

| 宿主 | Goal-first | 入口 | 备注 |
|------|------------|------|------|
| **ZCode 桌面** | ✅ | 内置 `/goal`、`/goal replace` | ADE session goal + 系统 completion 验证 |
| **Claude Code** | ✅ | 内置 `/goal <condition>` | Session 级；独立 evaluator（默认 Haiku）；新 goal 替换旧 goal |
| **OpenCode** | ✅ | 见 §5 | core 与插件两条路径均算 Goal-capable |
| **Cursor** | ❌ | — | 无原生 Goal → **默认 loop** |
| **其他** | ❌ 直至探测 | — | 默认 loop；探测到 Goal 能力后升格 |

### Claude Code 前置条件

Goal-first **仅当**以下条件满足；否则**跳过 Goal，直接 loop**：

- Trusted workspace（已接受安全提示）。
- Hooks 未在 settings 层 `disableAllHooks` / 企业策略未 `allowManagedHooksOnly` 阻断。

无人值守长任务：Goal（turn 间续跑）常与 **auto mode**（turn 内工具批准）配合；go 文档应提示，但不强制。

### Cursor

- 子任务：`/loop` 或加载 `loop` skill + 任务包（`--auto` 语义由 skill 承担）。
- go 不在 Cursor 上尝试 `/goal`。

---

## 5. OpenCode 规则（已确认）

**「core 必支持、插件也算」**：

| 档位 | 条件 | 路由 |
|------|------|------|
| **Tier A · core** | OpenCode 内置 `/goal`（或等价 session goal API）可用 | Goal-first |
| **Tier B · plugin** | 已安装 Goal 插件（如 opencode-goal-plugin、goal-x 等），且 `/goal` 或 agent goal 工具可用 | Goal-first |
| **Tier C · none** | core 无 Goal 且未装插件 | loop-default |

**探测顺序（建议）**：

1. 检测 core `/goal` / session goal 命令是否存在且可用。  
2. 若无，检测已配置插件是否注册 Goal 能力。  
3. 皆无 → `supports_native_goal: false`。

go / using-loopengine 文档应列出**推荐插件**（Tier B），但不绑定单一插件厂商实现。

---

## 6. 子任务 objective 构造

thin-loop 任务包仍必填 **goal + acceptance**（go 侧不变）。派发到 Goal 时合并为**一条可验证 objective**：

```text
/goal replace <goal 简述>。验收：<acceptance 1>；<acceptance 2>。…
```

- loop 工法（门禁要点）可**写入 objective**，不在 Goal 主控期间再开 `/loop` 第二主控。
- 需要完整 LoopEngine 门禁矩阵 + 验证官时，不走 Goal-first，或等 Goal 降级后再 loop。

---

## 7. Goal → loop 降级（触发条件 · 已选 B）

| 触发 | 动作 |
|------|------|
| Goal **achieved**（平台判定条件满足） | 正常 handoff，`executor=goal`，`degraded=false` |
| 用户 **`/goal clear`** / 取消 | 视 go 策略：abort 或降级 loop |
| **Budget / turn 上限**触顶（平台支持时） | 降级 loop |
| **Evaluator 多轮 NO** 或 **无实质进展 N 轮** | 降级 loop（防空转） |
| Goal **不可用**（Claude 非 trusted、OpenCode Tier C） | **跳过 Goal**，直接 loop |

降级步骤：

1. `/goal clear` 或平台等价 pause/stop。  
2. 加载 **loop** skill，携带**原任务包** acceptance。  
3. handoff 标记 `degraded=true`，`degraded_from=goal`，`degraded_reason=<枚举>`。

建议 `degraded_reason` 枚举：`goal_unmet` | `goal_stagnation` | `goal_budget` | `goal_unavailable` | `user_cleared`。

---

## 8. 与现有 go 概念的关系

| 现有 | 本设计 |
|------|--------|
| go → 派 loop / `--auto` | go → **Goal-first** → 失败再 loop |
| `profile: cursor \| zcode` | 扩展 **`supports_native_goal`**（或 capability registry） |
| `degradation.md` 模型/API 降级 | **并列**：执行器降级 goal→loop；模型降级仍走 fallback_chain |
| thin-loop 任务包 | **不变**；执行层路由变 |

**go 仍负责**：family、L0、DAG、worktree、汇合、G10。  
**Goal 负责**：单子任务 turn 间续跑 + 平台 completion 验证。  
**loop 负责**：LoopEngine 门禁、自愈、验证官（含降级路径）。

---

## 9. 能力探测（implementation 指引 · 非本阶段实现）

建议在 `.loopengine.yaml` 或宿主探测逻辑中支持：

```yaml
executor_routing:
  goal_first_hosts:
    - zcode
    - claude-code
    - opencode   # Tier A or B
  stagnation_rounds: 3   # 可选，默认 3
```

运行时：

- `detect_host()` → `goal_capable: bool` + `goal_tier: core|plugin|none`  
- 写入 `.orchestrate-state` 子任务字段：`assigned_executor: goal|loop`

---

## 10. 反模式

| 反模式 | 后果 |
|--------|------|
| Goal + loop 双主控 | 双重验证、token 浪费、结论冲突 |
| 在插件内实现 `/goal` | 与 ZCode/Claude/OpenCode 产品重复 |
| OpenCode 仅认插件不认 core | 与「core 必支持」冲突 |
| Cursor 上尝试 Goal-first | 无原生能力，应 loop-default |
| CLI `--target` 作为 go 默认路径 | 与用户桌面交互场景不符（已废弃） |

---

## 11. 验收标准（design 完成度）

- [x] 三宿主 Goal-first + Cursor loop-default 已定义  
- [x] OpenCode core + 插件均算 Goal-capable  
- [x] 降级触发含 stagnation（B）  
- [x] 排除 CLI 集成与双主控  
- [ ] implementation plan（writing-plans 技能 · 下一步）  
- [ ] `go/SKILL.md`、`using-loopengine` 引用本设计（实施时）  

---

## 12. 参考

- 讨论摘要：ZCode 内置 `/goal` vs 插件 `/loop`/`/go` 分层（2026-07-21 会话）  
- Claude Code：`https://code.claude.com/docs/en/goal`  
- OpenCode：native goal PR / 社区 goal 插件（实施前需再验证当前版本）  
- LoopEngine：`skills/go/SKILL.md` thin-loop 契约 · `skills/loop/SKILL.md`  

---

## 修订史

| 日期 | 变更 |
|------|------|
| 2026-07-21 | 初稿；废弃 CLI spike 方案；OpenCode core+插件确认 |
