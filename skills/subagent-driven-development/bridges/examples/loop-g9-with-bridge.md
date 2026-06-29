# loop G9 启用桥接示例（v6.1）

> 演示如何在 loop 技能中启用 subagent-dd 桥接作为 G9 增强。

## 场景

用户希望 loop 在每个 commit 前**走 subagent-dd 的三阶段审查循环**（implementer → spec → code quality），
而不是默认的 `code-reviewer` 单次审查。

## 命令

```bash
# 1. 启用桥接环境变量
export LOOPENGINE_BRIDGES=alpha

# 2. loop 命令带 --reviewer=subagent-dd
/loop --reviewer=subagent-dd 实现分页功能，验收：翻页正确、总数对、加载状态显示
```

## loop 内执行流程（启用桥接后）

```
Step 1: 模式判定
  └─ 检测到 --reviewer=subagent-dd
  └─ 加载 bridges/contract.py
  └─ 检查 LOOPENGINE_BRIDGES=alpha（已启用）

Step 2: 模式分发（--auto 子任务模式）
  └─ 进入 mode-auto.md 流程

Step 3: 子任务循环（每任务一次 G9 桥接）
  │
  ├─ 3.1 dispatch_implementer
  │   └─ 派遣 implementer subagent
  │   └─ 返回 ImplementerReport(status=DONE, ...)
  │
  ├─ 3.2 dispatch_spec_reviewer（仅 DONE* 时）
  │   └─ 派遣 spec reviewer subagent
  │   └─ 返回 SpecVerdict(compliant=True/False, ...)
  │   └─ ❌ → 自愈重试（最多 3 次）
  │   └─ 持续 ❌ → 降级到 code-reviewer
  │
  └─ 3.3 dispatch_code_quality_reviewer（仅 spec ✅ 时）
      └─ 派遣 code quality reviewer subagent
      └─ 返回 QualityAssessment(issues=[Critical/Important/Minor], ...)
      └─ Critical → 阻塞自愈
      └─ Important/Minor → 记录到 handoff

Step 4: 验收条件 + 自愈闭环
  └─ 正常完成 → commit + 写入 handoff.gate_result

Step 5: 交付
  └─ 报告含 3 层 Issues 统计
```

## 降级场景

### 场景 1: LOOPENGINE_BRIDGES=disabled

```bash
unset LOOPENGINE_BRIDGES
/loop --reviewer=subagent-dd 实现分页功能
# 警告：桥接未启用，将降级到 code-reviewer
# 行为等价于：/loop 实现分页功能
```

### 场景 2: dispatch_implementer 返回 BLOCKED

```
Step 3.1 → ImplementerStatus.BLOCKED
  └─ handle_implementer_status → "ESCALATE_TO_HUMAN"
  └─ 暂停子任务，提示用户
  └─ 用户决定：重试 / 改需求 / 人工接管
```

### 场景 3: dispatch_spec_reviewer 持续 ❌

```
Step 3.2 → SpecVerdict.compliant=False（连续 3 次）
  └─ 记录 specs_stuck=true 到 decision_log
  └─ 降级到 code-reviewer
  └─ 提示用户：subagent-dd 审查模式卡住
```

### 场景 4: Critical Issue

```
Step 3.3 → QualityAssessment.issues 含 Critical
  └─ 阻塞提交，触发自愈
  └─ 自愈成功后重新 review
```

## 关键代码（loop 内集成位置）

```python
# loop 内的 G9 桥接逻辑（伪代码）
import os
from subagent_driven_development.bridges.contract import (
    is_bridge_enabled,
    dispatch_implementer,
    dispatch_spec_reviewer,
    dispatch_code_quality_reviewer,
    handle_implementer_status,
    review_gate,
    ImplementerStatus,
)

def g9_with_bridge(task, requirements, base_sha, head_sha):
    """G9 桥接模式（替代默认 code-reviewer）"""
    
    if not is_bridge_enabled():
        return default_code_reviewer(task)  # 降级
    
    # 3.1 implementer
    report = dispatch_implementer(
        task_text=task.description,
        context=task.context,
        workdir=task.workdir,
        model_tier="auto",
    )
    
    action = handle_implementer_status(report.status, report)
    if action == "ESCALATE_TO_HUMAN":
        return G9Blocked(report.concerns)
    
    # 3.2 spec review
    spec_verdict = dispatch_spec_reviewer(
        requirements=requirements,
        implementer_report=report,
    )
    
    if not review_gate(spec_verdict):
        return G9SpecFailed(spec_verdict.issues)
    
    # 3.3 code quality
    quality = dispatch_code_quality_reviewer(
        task_summary=task.summary,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    
    return G9Result(
        spec_verdict=spec_verdict,
        quality=quality,
        approved=review_gate(spec_verdict, quality),
    )
```

## 何时用 / 何时不用

| 场景 | 推荐 |
|------|------|
| 单文件 / 单 PR / 紧急修复 | ❌ 默认 code-reviewer（更快） |
| 跨文件 / 复杂逻辑 / 需 TDD 纪律 | ✅ 桥接 subagent-dd |
| 需 spec/code 双审 / 团队重视质量门禁 | ✅ 桥接 subagent-dd |
| 性能优先 / token 预算紧 | ❌ 默认 code-reviewer |
| 多语言 / 架构级改动 | ✅ 桥接 subagent-dd（capable 模型） |
