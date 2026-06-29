"""subagent-driven-development 桥接组件契约（v6.1 · opt-in）

提供 6 个核心桥接函数 + 3 个 dataclass，让 go / loop 技能可调用 subagent-dd
的审查能力作为 G9/G10 的增强实现。

**灰度开关**：`LOOPENGINE_BRIDGES=alpha` 启用，默认 `disabled`。

**与主技能的关系**：
- 三个 prompt template（implementer / spec-reviewer / code-quality-reviewer）**不动**
- bridges/ 目录是**新增**，提供可调用的 Python 接口
- 默认（不传 --reviewer）go/loop 行为 100% 不变

完整规范：bridges/dispatcher.md
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


# ===== 灰度开关 =====

def is_bridge_enabled() -> bool:
    """检查桥接是否启用。

    Returns:
        bool: True 当 `LOOPENGINE_BRIDGES=alpha` 且不为 `disabled`。
    """
    return os.environ.get("LOOPENGINE_BRIDGES", "disabled") == "alpha"


def require_bridge_enabled() -> None:
    """要求桥接启用，否则抛 NotImplementedError（防止意外调用）。"""
    if not is_bridge_enabled():
        raise NotImplementedError(
            "subagent-dd 桥接未启用。"
            "请设置环境变量 `LOOPENGINE_BRIDGES=alpha` 后重试。"
        )


# ===== 数据契约 =====

class ImplementerStatus(str, Enum):
    """Implementer subagent 4 状态枚举。

    来源：implementer-prompt.md §Report Format
    """
    DONE = "DONE"
    DONE_WITH_CONCERNS = "DONE_WITH_CONCERNS"
    BLOCKED = "BLOCKED"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"


@dataclass
class ImplementerReport:
    """Implementer 派遣结果。"""
    status: ImplementerStatus
    summary: str
    files_changed: List[str] = field(default_factory=list)
    test_results: str = ""
    self_review: str = ""
    concerns: List[str] = field(default_factory=list)
    base_sha: str = ""
    head_sha: str = ""


@dataclass
class SpecVerdict:
    """Spec Reviewer 派遣结果。"""
    compliant: bool          # True=✅, False=❌
    issues: List[str]        # file:line 引用列表
    rationale: str
    missing: List[str] = field(default_factory=list)      # 缺失的需求
    extra: List[str] = field(default_factory=list)        # 多余的实现
    misunderstandings: List[str] = field(default_factory=list)


class QualitySeverity(str, Enum):
    """Code Quality 3 层分级。"""
    CRITICAL = "Critical"
    IMPORTANT = "Important"
    MINOR = "Minor"


@dataclass
class QualityIssue:
    """Code Quality 单个问题。"""
    severity: QualitySeverity
    file: str
    line: int
    description: str


@dataclass
class QualityAssessment:
    """Code Quality Reviewer 派遣结果。"""
    strengths: List[str]
    issues: List[QualityIssue]
    assessment: str         # Approved/Needs Fixes/Rejected


# ===== 6 个核心桥接函数 =====

def dispatch_implementer(
    task_text: str,
    context: str,
    workdir: str,
    model_tier: str = "auto",
) -> ImplementerReport:
    """派遣 implementer subagent 执行单任务。

    对应 prompt：implementer-prompt.md
    行为：TDD 实现 + 自审 + commit + 报告 4 状态

    Args:
        task_text: 任务完整文本（不引用 plan 文件，直接注入）
        context: 场景上下文（依赖、架构、归属）
        workdir: 工作目录
        model_tier: cheap / standard / capable / auto（auto = model_select）

    Returns:
        ImplementerReport: 4 状态枚举 + 报告内容

    Raises:
        NotImplementedError: 桥接未启用时
    """
    require_bridge_enabled()
    # 实际实现：subprocess 调 zcode + implementer-prompt.md 注入
    # alpha 阶段返回 mock；生产实现见 dispatcher.md §3
    raise NotImplementedError(
        "dispatch_implementer alpha 阶段未实现真实派遣。"
        "生产实现参见 bridges/dispatcher.md §3 契约。"
    )


def dispatch_spec_reviewer(
    requirements: str,
    implementer_report: ImplementerReport,
) -> SpecVerdict:
    """派遣 spec reviewer subagent 做规格合规审查。

    对应 prompt：spec-reviewer-prompt.md
    行为：独立读代码验证，不信任 implementer 声明
          检查 Missing/Extra/Misunderstandings 三类

    Args:
        requirements: 任务原始需求（来自 plan 文档）
        implementer_report: implementer 派遣结果

    Returns:
        SpecVerdict: ✅/❌ + file:line 引用 + 三类问题清单

    Raises:
        NotImplementedError: 桥接未启用时
    """
    require_bridge_enabled()
    raise NotImplementedError(
        "dispatch_spec_reviewer alpha 阶段未实现真实派遣。"
    )


def dispatch_code_quality_reviewer(
    task_summary: str,
    base_sha: str,
    head_sha: str,
    plan_ref: str = "",
) -> QualityAssessment:
    """派遣 code quality reviewer subagent 做质量审查。

    对应 prompt：code-quality-reviewer-prompt.md
    行为：使用 BASE→HEAD SHA 限定审查范围
          返回 3 层问题分级（Critical/Important/Minor）

    Args:
        task_summary: 任务摘要（来自 implementer 报告）
        base_sha: 任务开始前的 commit SHA
        head_sha: 当前 commit SHA
        plan_ref: plan 文件路径（可选）

    Returns:
        QualityAssessment: Strengths + 3 层 Issues + Assessment

    Raises:
        NotImplementedError: 桥接未启用时
    """
    require_bridge_enabled()
    raise NotImplementedError(
        "dispatch_code_quality_reviewer alpha 阶段未实现真实派遣。"
    )


def model_select(task_signals: dict) -> str:
    """根据任务信号选择模型档位。

    对应 SKILL.md §Model Selection

    Args:
        task_signals: {
            "file_count": int,         # 涉及文件数
            "has_integration": bool,   # 是否有跨文件集成
            "requires_design_judgment": bool,  # 是否需要设计判断
        }

    Returns:
        str: 'cheap' / 'standard' / 'capable'

    Examples:
        >>> model_select({"file_count": 1, "has_integration": False, "requires_design_judgment": False})
        'cheap'
        >>> model_select({"file_count": 5, "has_integration": True, "requires_design_judgment": False})
        'standard'
        >>> model_select({"file_count": 10, "has_integration": True, "requires_design_judgment": True})
        'capable'
    """
    # 启发式规则（与 SKILL.md §Model Selection 一致）
    if task_signals.get("requires_design_judgment", False):
        return "capable"
    if task_signals.get("has_integration", False) or task_signals.get("file_count", 1) > 3:
        return "standard"
    return "cheap"


def handle_implementer_status(
    status: ImplementerStatus,
    report: ImplementerReport,
) -> str:
    """处理 implementer 4 状态返回的动作。

    对应 SKILL.md §Handling Implementer Status

    Args:
        status: implementer 报告的状态
        report: implementer 完整报告（用于 NEEDS_CONTEXT 时补全）

    Returns:
        str: 下一动作指令
            - 'PROCEED_TO_SPEC_REVIEW'
            - 'PROCEED_WITH_CONCERNS_NOTED'
            - 'PROVIDE_CONTEXT_AND_REDISPATCH'
            - 'ESCALATE_TO_HUMAN'

    Examples:
        >>> handle_implementer_status(ImplementerStatus.DONE, ImplementerReport(...))
        'PROCEED_TO_SPEC_REVIEW'
    """
    if status == ImplementerStatus.DONE:
        return "PROCEED_TO_SPEC_REVIEW"
    if status == ImplementerStatus.DONE_WITH_CONCERNS:
        return "PROCEED_WITH_CONCERNS_NOTED"
    if status == ImplementerStatus.NEEDS_CONTEXT:
        return "PROVIDE_CONTEXT_AND_REDISPATCH"
    if status == ImplementerStatus.BLOCKED:
        return "ESCALATE_TO_HUMAN"
    raise ValueError(f"未知的 Implementer 状态: {status}")


def review_gate(
    spec_verdict: SpecVerdict,
    quality_assessment: Optional[QualityAssessment] = None,
) -> bool:
    """强顺序约束：spec ✅ 才能进 code quality。

    对应 SKILL.md §Red Flags：「Start code quality review before spec compliance is ✅ (wrong order)」

    Args:
        spec_verdict: spec reviewer 派遣结果
        quality_assessment: code quality 派遣结果（可选，未执行时为 None）

    Returns:
        bool: True=可继续下一阶段, False=需修复重审

    Examples:
        >>> review_gate(SpecVerdict(compliant=True, ...))
        True
        >>> review_gate(SpecVerdict(compliant=False, issues=['file:42']))
        False
    """
    if not spec_verdict.compliant:
        return False
    if quality_assessment is None:
        return True  # spec 已过，等 code quality
    # code quality 也必须不是 Rejected
    return quality_assessment.assessment != "Rejected"


# ===== 单元测试（自检）=====

if __name__ == "__main__":
    # 1. 灰度开关测试
    assert is_bridge_enabled() is False, "默认应禁用"
    print("✅ is_bridge_enabled 默认 False")

    os.environ["LOOPENGINE_BRIDGES"] = "alpha"
    assert is_bridge_enabled() is True
    print("✅ LOOPENGINE_BRIDGES=alpha 时 True")
    del os.environ["LOOPENGINE_BRIDGES"]

    # 2. 数据契约类型测试
    report = ImplementerReport(
        status=ImplementerStatus.DONE,
        summary="实现完成",
    )
    assert report.status == ImplementerStatus.DONE
    print("✅ ImplementerReport 数据契约")

    verdict = SpecVerdict(compliant=True, issues=[], rationale="OK")
    assert verdict.compliant is True
    print("✅ SpecVerdict 数据契约")

    assessment = QualityAssessment(
        strengths=["简洁"],
        issues=[],
        assessment="Approved",
    )
    assert assessment.assessment == "Approved"
    print("✅ QualityAssessment 数据契约")

    # 3. model_select 信号测试
    assert model_select({"file_count": 1}) == "cheap"
    assert model_select({"file_count": 5, "has_integration": True}) == "standard"
    assert model_select({"file_count": 10, "has_integration": True, "requires_design_judgment": True}) == "capable"
    print("✅ model_select 三档信号")

    # 4. handle_implementer_status 状态机测试
    assert handle_implementer_status(ImplementerStatus.DONE, report) == "PROCEED_TO_SPEC_REVIEW"
    assert handle_implementer_status(ImplementerStatus.BLOCKED, report) == "ESCALATE_TO_HUMAN"
    print("✅ handle_implementer_status 状态机")

    # 5. review_gate 强顺序测试
    assert review_gate(verdict) is True
    bad_verdict = SpecVerdict(compliant=False, issues=["file:42"], rationale="差")
    assert review_gate(bad_verdict) is False
    print("✅ review_gate 强顺序")

    print("\n🎉 bridges/contract.py v6.1 自检通过")
