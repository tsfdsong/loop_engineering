# 桥接契约说明（v6.1 · opt-in）

> 本文件定义 `bridges/contract.py` 6 个核心桥接函数的输入/输出契约，
> 以及与 go / loop 技能的集成模式。

## 1. 灰度开关

```bash
# 默认（不启用）
export LOOPENGINE_BRIDGES=disabled    # 默认值
# → 任何 dispatch_* 调用抛 NotImplementedError

# 启用桥接（alpha）
export LOOPENGINE_BRIDGES=alpha
# → 允许调 6 个桥接函数
```

**铁律**：
- 默认关闭（100% 兼容 v5.4/v6.0）
- 启用时仅加载桥接组件，**不改变** go/loop 原有 G9/G10 默认实现
- 桥接失败时**自动降级**到原 G9/G10，不报错中断

## 2. 6 个核心桥接函数

### 2.1 `dispatch_implementer`

**对应 prompt**：`implementer-prompt.md`

**输入**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `task_text` | str | ✅ | 任务完整文本（**不引用 plan 文件**，直接注入） |
| `context` | str | ✅ | 场景上下文（依赖、架构、归属） |
| `workdir` | str | ✅ | 工作目录 |
| `model_tier` | str | 🟡 | `cheap` / `standard` / `capable` / `auto`（默认 `auto`） |

**输出**：`ImplementerReport`（含 `ImplementerStatus` 4 状态枚举）

**生产实现**（alpha 后）：
```python
# subprocess 调 zcode + implementer-prompt.md 注入
def dispatch_implementer(task_text, context, workdir, model_tier="auto"):
    require_bridge_enabled()
    
    # 1. 选模型档位
    if model_tier == "auto":
        model_tier = model_select({
            "file_count": len(extract_files(task_text)),
            "has_integration": "集成" in task_text,
            "requires_design_judgment": "设计" in task_text,
        })
    
    # 2. 注入 prompt
    prompt = render_prompt("implementer-prompt.md", {
        "task_text": task_text,
        "context": context,
        "workdir": workdir,
    })
    
    # 3. 派遣 subagent
    result = zcode_dispatch(prompt, model=model_tier, workdir=workdir)
    
    # 4. 解析 4 状态
    return parse_implementer_report(result)
```

### 2.2 `dispatch_spec_reviewer`

**对应 prompt**：`spec-reviewer-prompt.md`

**输入**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `requirements` | str | ✅ | 任务原始需求（来自 plan 文档） |
| `implementer_report` | `ImplementerReport` | ✅ | implementer 派遣结果 |

**输出**：`SpecVerdict`（✅/❌ + file:line 引用 + Missing/Extra/Misunderstandings 三类）

**生产实现**：
```python
def dispatch_spec_reviewer(requirements, implementer_report):
    require_bridge_enabled()
    
    # 1. 注入 prompt
    prompt = render_prompt("spec-reviewer-prompt.md", {
        "requirements": requirements,
        "implementer_report": implementer_report.summary,
    })
    
    # 2. 派遣 subagent（**独立读代码**，不信任 implementer 声明）
    result = zcode_dispatch(prompt, model="standard")
    
    # 3. 解析 ✅/❌
    return parse_spec_verdict(result)
```

### 2.3 `dispatch_code_quality_reviewer`

**对应 prompt**：`code-quality-reviewer-prompt.md`

**输入**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `task_summary` | str | ✅ | 任务摘要 |
| `base_sha` | str | ✅ | 任务开始前的 commit SHA |
| `head_sha` | str | ✅ | 当前 commit SHA |
| `plan_ref` | str | 🟡 | plan 文件路径（可选） |

**输出**：`QualityAssessment`（Strengths + 3 层 Issues + Assessment）

**生产实现**：
```python
def dispatch_code_quality_reviewer(task_summary, base_sha, head_sha, plan_ref=""):
    require_bridge_enabled()
    
    # 1. 强顺序：先过 spec ✅
    if not review_gate(current_spec_verdict):
        raise SpecReviewNotPassedError("spec 未通过，禁止 code quality 审查")
    
    # 2. 注入 prompt（用 git SHAs 限定审查范围）
    prompt = render_prompt("code-quality-reviewer-prompt.md", {
        "task_summary": task_summary,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "plan_ref": plan_ref,
    })
    
    # 3. 派遣 subagent
    result = zcode_dispatch(prompt, model="capable")
    
    # 4. 解析 3 层 Issues
    return parse_quality_assessment(result)
```

### 2.4 `model_select`

**依据**：`SKILL.md §Model Selection`

**输入**：`task_signals: dict`
```python
{
    "file_count": int,                # 涉及文件数
    "has_integration": bool,          # 是否有跨文件集成
    "requires_design_judgment": bool, # 是否需要设计判断
}
```

**输出**：`'cheap' | 'standard' | 'capable'`

**规则**：

| 条件 | 档位 |
|------|------|
| `requires_design_judgment = True` | `capable` |
| `has_integration = True` 或 `file_count > 3` | `standard` |
| 其他 | `cheap` |

### 2.5 `handle_implementer_status`

**依据**：`SKILL.md §Handling Implementer Status`

**输入**：`status: ImplementerStatus` + `report: ImplementerReport`

**输出**：下一动作指令（str）

| 状态 | 动作 |
|------|------|
| `DONE` | `PROCEED_TO_SPEC_REVIEW` |
| `DONE_WITH_CONCERNS` | `PROCEED_WITH_CONCERNS_NOTED` |
| `NEEDS_CONTEXT` | `PROVIDE_CONTEXT_AND_REDISPATCH` |
| `BLOCKED` | `ESCALATE_TO_HUMAN` |

### 2.6 `review_gate`

**依据**：`SKILL.md §Red Flags`（强顺序约束）

**输入**：`spec_verdict: SpecVerdict` + `quality_assessment: Optional[QualityAssessment]`

**输出**：`bool`

| 条件 | 结果 |
|------|------|
| `spec_verdict.compliant = False` | `False`（禁止继续） |
| `spec ✅ + quality 未执行` | `True`（可继续 quality） |
| `spec ✅ + quality = Approved/Needs Fixes` | `True`（可标完成） |
| `spec ✅ + quality = Rejected` | `False`（需重审） |

## 3. 与 go / loop 的集成模式

### 3.1 go G10 集成点（Step ⑦.5）

```bash
# 默认（v6.1 行为不变）
/go 实现订单管理功能
  └─ G10 = system-review 审查整特性分支

# 启用桥接
LOOPENGINE_BRIDGES=alpha /go --reviewer=subagent-dd 实现订单管理功能
  └─ G10 = bridges/dispatch_code_quality_reviewer 审查整特性分支
       （3 层问题分级 + Assessment 字段）
```

**go 内集成位置**：`skills/go/scripts/orchestrator.py` Step ⑦.5

```python
# orchestrator.py 伪代码（v6.1）
if reviewer == "subagent-dd":
    from subagent_driven_development.bridges.contract import (
        dispatch_code_quality_reviewer, is_bridge_enabled
    )
    if not is_bridge_enabled():
        # 降级到原 system-review
        return system_review(feature_branch)
    
    assessment = dispatch_code_quality_reviewer(
        task_summary=state["feature"],
        base_sha=state["base_sha"],
        head_sha=get_head_sha(),
    )
    
    # 3 层 Issues 处理
    for issue in assessment.issues:
        if issue.severity == QualitySeverity.CRITICAL:
            return DeliveryBlocked(assessment)
    return DeliveryApproved(assessment)
```

### 3.2 loop G9 集成点（commit 前）

```bash
# 默认（v6.1 行为不变）
/loop 实现分页功能
  └─ G9 = code-reviewer 审查单次提交

# 启用桥接
LOOPENGINE_BRIDGES=alpha /loop --reviewer=subagent-dd 实现分页功能
  └─ G9 = bridges 三阶段循环
       （dispatch_implementer → dispatch_spec_reviewer → dispatch_code_quality_reviewer）
```

**loop 内集成位置**：`skills/loop/scripts/commit_gate.py`（待创建）

## 4. 失败降级策略

| 桥接调用结果 | 降级动作 |
|------------|---------|
| `dispatch_implementer` 抛 `NotImplementedError`（桥接未启用） | 降级到原 G9/G10 实现 |
| `dispatch_implementer` 返回 `BLOCKED` | 降级 + 记录 `degraded_reason="implementer_blocked"` |
| `dispatch_spec_reviewer` 持续 `❌`（> 3 次） | 降级到原 G9/G10 + 记录 `specs_stuck=true` |
| `dispatch_code_quality_reviewer` 抛异常 | 降级到原 G9/G10 + 记录 `bridge_error` |
| `LOOPENGINE_BRIDGES=disabled` | **不加载** bridges/，走原 G9/G10 |

**铁律**：桥接**永远不阻塞**主流程；失败必须降级到原实现。

## 5. 兼容性承诺

- ✅ 默认关闭（`disabled`），go/loop 行为 100% 不变
- ✅ 启用桥接时，原 G9/G10 实现保留，桥接仅作**增强**选项
- ✅ 三个 prompt template（implementer / spec-reviewer / code-quality-reviewer）**不动**
- ✅ bridges/contract.py 是**新增**，不改 subagent-dd 任何现有文件
- ✅ 桥接失败自动降级，**不破坏**既有交付流程
