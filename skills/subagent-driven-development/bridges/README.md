# subagent-dd 桥接组件（v6.1 · opt-in）

> 本目录是 `subagent-driven-development` 技能的可桥接接口层，
> 让 go / loop 技能可选用 subagent-dd 的 3 阶段审查循环（implementer → spec → code quality）
> 作为 G9/G10 的增强实现。

## 目录结构

```
bridges/
├── README.md                          # 本文件
├── contract.py                        # 6 个核心桥接函数 + 3 个 dataclass
├── dispatcher.md                      # 桥接契约说明（输入/输出 schema）
└── examples/
    └── loop-g9-with-bridge.md         # loop G9 启用桥接的示例
```

## 与主技能的关系

| 主技能文件 | 桥接层改动 |
|----------|----------|
| `SKILL.md` | frontmatter +5 字段；新增 §Bridgeable Components 章节 +20 行 |
| `implementer-prompt.md` | **不动**（保持原状） |
| `spec-reviewer-prompt.md` | **不动**（保持原状） |
| `code-quality-reviewer-prompt.md` | **不动**（保持原状） |
| `bridges/contract.py` | **新增**（6 个桥接函数 + 3 个 dataclass） |
| `bridges/dispatcher.md` | **新增**（契约说明文档） |

**铁律**：原 3 个 prompt template 零修改；bridges/ 是**纯增量**。

## 6 个核心桥接函数

| 函数 | 对应 prompt | 替换关系 |
|------|------------|---------|
| `dispatch_implementer` | implementer-prompt.md | 替代 G9 内的 commit 前自审 |
| `dispatch_spec_reviewer` | spec-reviewer-prompt.md | 替代 G9 内的 spec 审查 |
| `dispatch_code_quality_reviewer` | code-quality-reviewer-prompt.md | 替代 G9/G10 内的质量审查 |
| `model_select` | SKILL.md §Model Selection | 提供模型选型信号 |
| `handle_implementer_status` | SKILL.md §Handling Status | 4 状态应对动作 |
| `review_gate` | SKILL.md §Red Flags | 强顺序约束 |

## 灰度开关

```bash
# 默认
export LOOPENGINE_BRIDGES=disabled    # 不加载 bridges/

# 启用
export LOOPENGINE_BRIDGES=alpha       # 允许 dispatch_* 调用
```

**铁律**：
- 默认关闭（100% 兼容 v5.4/v6.0）
- 启用时**不改变** go/loop 原有 G9/G10 默认实现
- 需在 go/loop 命令显式传 `--reviewer=subagent-dd` 才触发桥接
- 桥接失败时**自动降级**到原 G9/G10

## 集成模式（速查）

### go G10 桥接

```bash
# 默认
/go 实现订单管理功能
  └─ G10 = system-review

# 启用
LOOPENGINE_BRIDGES=alpha /go --reviewer=subagent-dd 实现订单管理功能
  └─ G10 = bridges/dispatch_code_quality_reviewer
```

### loop G9 桥接

```bash
# 默认
/loop 实现分页功能
  └─ G9 = code-reviewer

# 启用
LOOPENGINE_BRIDGES=alpha /loop --reviewer=subagent-dd 实现分页功能
  └─ G9 = bridges 三阶段循环
```

## 失败降级

| 场景 | 降级动作 |
|------|---------|
| 桥接未启用（`disabled`） | 不加载 bridges/，走原 G9/G10 |
| `dispatch_*` 抛异常 | 降级到原 G9/G10 + 记录 `bridge_error` |
| `BLOCKED` / 持续 ❌ | 降级 + 记录 `degraded_reason` |
| 任何时候 | **不阻塞**主流程 |

## 兼容性

- ✅ v5.4 完全兼容（subagent-dd 原 4 文件不动）
- ✅ v6.0 完全兼容（go/loop 默认行为不变）
- ✅ 桥接默认关闭，opt-in 启用
- ✅ 桥接失败自动降级

## 完整规范

详见 `dispatcher.md` 第 2 节（6 个桥接函数契约）和第 3 节（集成模式）。
