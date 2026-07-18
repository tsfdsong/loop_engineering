# Runtime Config（运行时配置说明 · v2.0）

> LoopEngine 运行时配置项的说明文档。**本配置与具体工具/模型无关**。
> 用户在项目根创建 `.loopengine.yaml`（可选 · 不配则走宿主默认 + 无降级）。
> 配套示例文件：项目根 `.loopengine.example.yaml`（复制后改名即可）。

## `.loopengine.yaml`（项目根 · 可选）

用户在项目根自配运行时参数。**不配置则走默认值**：无降级链、L1 不启动 supervisor。

### 快速上手

```bash
cp .loopengine.example.yaml .loopengine.yaml
# 编辑 .loopengine.yaml 按需修改
```

---

## 字段说明

### `fallback_chain`（降级链 · 三档抽象）

配额耗尽或 loop exhausted 时自动按 primary → secondary → tertiary 顺序切换。
任一档留空（或注释掉）= 跳过该档，直接进入下一档；全部失败 → R4 上报用户（不静默放弃）。

| 档位 | 何时启用 | 留空含义 |
|---|---|---|
| `primary` | 主力模型（默认）| 使用宿主工具默认模型，不强制切换 |
| `secondary` | primary 配额耗尽 / loop exhausted | 无次选，直接 R4 上报 |
| `tertiary` | primary + secondary 均失败 | 无兜底，继续失败则 R4 上报 |

每个档位支持以下字段（均可选）：

| 字段 | 类型 | 说明 |
|---|---|---|
| `description` | string | 人类可读描述（仅注释作用，不被代码消费） |
| `model` | string | 显式指定模型 ID（留空 = 走该档默认） |
| `tool` | string | 跨工具调度场景下显式指定宿主工具（留空 = 当前工具） |

#### 配置示例

```yaml
fallback_chain:
  primary:
    description: "主力模型（宿主工具默认）"
    # 留空 = 使用宿主工具默认模型
  secondary:
    description: "次选（主力配额耗尽时）"
    # model: "..."   # 可选 · 显式指定模型 ID
    # tool: "..."    # 可选 · 跨工具调度
  tertiary:
    description: "兜底（全部失败时）"
    # 留空 = 无兜底
```

> `primary` / `secondary` / `tertiary` 均为抽象档位，不绑定任何具体工具/模型。
> 三档是否填 `model` / `tool` 完全由用户决定，未填则采用宿主默认。

---

### `supervisor`（监控进程参数）

supervisor（编排层监控）在 L2/L3 任务启动，负责 R1-R4 渐进式干预（详见 `state-protocol.md`）。

| 字段 | 默认 | 说明 |
|---|---|---|
| `enabled_levels` | `[L2, L3]` | 哪些 L 级别启动 supervisor。L1（简单任务）默认不启动。可选 `L1` / `L2` / `L3` 任意组合。 |
| `r4_threshold` | `default` | R4（上报用户）触发阈值。`default = R1×2 + R2×1 ≈ 3-5 分钟渐进式干预后仍无进展`。也可传具体数字（单位：次）。 |
| `polling_interval` | `30` | supervisor polling 间隔（秒）。越短越敏感、token 开销越大。 |

#### 配置示例

```yaml
supervisor:
  enabled_levels: [L2, L3]
  r4_threshold: default      # 或传具体数字，如 3
  polling_interval: 30       # 秒
```

---

## 示例场景（不限于特定工具/模型）

### 场景 1：单工具用户（最简）

只用一个宿主工具 + 一个模型，不需要降级。**可以完全不创建 `.loopengine.yaml`**。

如果显式写：

```yaml
fallback_chain:
  primary:
    description: "宿主工具默认模型"
supervisor:
  enabled_levels: [L2, L3]
```

### 场景 2：多 API Key 用户（同工具内切换模型）

同一宿主工具，但有多个 API Key 对应不同模型，希望配额耗尽自动切换：

```yaml
fallback_chain:
  primary:
    description: "主力模型 A"
    model: "provider-A/model-fast"
  secondary:
    description: "次选模型 B"
    model: "provider-B/model-standard"
  tertiary:
    description: "兜底模型 C"
    model: "provider-C/model-cheap"
supervisor:
  enabled_levels: [L2, L3]
  polling_interval: 30
```

### 场景 3：多工具用户（跨工具调度）

多个 AI 编码工具并行使用，希望失败时切到另一个工具：

```yaml
fallback_chain:
  primary:
    description: "主力工具 X"
    tool: "tool-X"
  secondary:
    description: "次选工具 Y"
    tool: "tool-Y"
  tertiary:
    description: "兜底工具 Z"
    tool: "tool-Z"
```

### 场景 4：轻量任务（只 L3 启 supervisor）

希望 L1/L2 跑轻量、只有 L3 复杂任务才上 supervisor 监控：

```yaml
fallback_chain:
  primary:
    description: "宿主默认"
supervisor:
  enabled_levels: [L3]           # 只 L3 启动 supervisor
  r4_threshold: 5                # 允许 5 次渐进干预后才 R4
  polling_interval: 60           # 1 分钟 polling 一次（省 token）
```

---

## 不配置时的行为

`.loopengine.yaml` 不存在 → **全部走默认**：

- `fallback_chain`：无降级 · primary 走宿主默认，loop exhausted 直接 R4 上报（AskUserQuestion 问用户）
- `supervisor`：`enabled_levels = [L2, L3]`，`r4_threshold = default`，`polling_interval = 30`

---

## 与其它协议的协同

- **降级链 + R4 协议**：见 `state-protocol.md` 的 R1-R4 渐进式干预
- **supervisor 与编排层**：见 `dag-assembly.md` / `state-protocol.md`
- **工具/模型无关性原则**：见 `degradation.md`（v2.0 三档抽象说明）

## 相关文件

- `.loopengine.example.yaml`（项目根）：可直接复制的示例
- `skills/go/references/degradation.md`：降级机制设计文档
- `skills/go/references/state-protocol.md`：R1-R4 协议
