# Fallback Chain（降级兜底机制 · v2.0 工具/模型无关化）

> 配额耗尽 / loop exhausted 时自动切换。**本插件不绑定任何特定工具或模型**。
> 用户在项目根 `.loopengine.yaml` 自配（可选 · 不配则无降级）。

## 三档抽象降级链

```
Primary Tier（主力 · 用户配置或宿主默认）
   ↓ 配额耗尽 / loop exhausted
Secondary Tier（次选 · 用户可配）
   ↓ 仍失败
Tertiary Tier（兜底 · 用户可配）
   ↓ 仍失败
R4 上报用户（必走 AskUserQuestion · 不静默放弃）
```

## 配置（`.loopengine.yaml` · 项目根 · 可选）

用户在项目根创建 `.loopengine.yaml`（可选 · 不配则无降级）：

```yaml
fallback_chain:
  primary:
    description: "主力模型（宿主工具默认）"
    # 例：zcode + GLM / cursor + Claude / trae + 豆包 / codex + GPT
    # 留空 = 使用宿主工具默认模型
  secondary:
    description: "次选（主力配额耗尽时）"
    # 留空 = 无次选，直接 R4 上报
  tertiary:
    description: "兜底（全部失败时）"
    # 留空 = 无兜底
```

## 示例场景（不限于特定工具/模型）

| 场景 | primary | secondary | tertiary |
|---|---|---|---|
| 单工具用户 | 宿主默认 | （留空）| （留空）|
| 多 API 用户 | API-A | API-B | API-C |
| 多工具用户 | 工具-X | 工具-Y | 工具-Z |
| 单模型用户 | 模型-α | （留空）| （留空）|

## 不配置时的行为

`.loopengine.yaml` 不存在或 fallback_chain 留空 → 无降级 · loop exhausted 直接 R4 上报（AskUserQuestion 问用户）。

## 与 supervisor 的协同

supervisor 监控到 loop exhausted 时：
1. 读 `.loopengine.yaml` 的 fallback_chain
2. 按配置决定 R2 降级到哪个 tier
3. 记录到 `.supervisor-state.json` 的 interventions 字段
4. 多次失败后进 R4 上报

详见 `skills/supervisor/SKILL.md`。

## v2.0 工具/模型双无关性原则

本机制严格遵循 v2.0 双无关性硬约束：
- 不预设特定工具（适配 ZCode/Cursor/Claude Code/TRAE 等所有宿主）
- 不预设特定模型（适配能力较弱到较强的各种模型）
- 用户自配 fallback_chain · 插件只提供框架
