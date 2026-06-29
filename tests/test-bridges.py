"""Bridge 组件契约测试（v6.1 · opt-in）

测试 subagent-driven-development/bridges/contract.py 的 6 个核心桥接函数 +
3 个 dataclass + 灰度开关。

运行：python tests/test-bridges.py
"""

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "subagent-driven-development" / "bridges"))

# 保存环境变量以便恢复
ORIG_ENV = os.environ.get("LOOPENGINE_BRIDGES", "disabled")

from contract import (  # noqa: E402
    ImplementerStatus,
    ImplementerReport,
    SpecVerdict,
    QualitySeverity,
    QualityIssue,
    QualityAssessment,
    is_bridge_enabled,
    require_bridge_enabled,
    model_select,
    handle_implementer_status,
    review_gate,
    dispatch_implementer,
    dispatch_spec_reviewer,
    dispatch_code_quality_reviewer,
)


# ===== 灰度开关测试 =====

def test_bridge_disabled_by_default():
    """默认 LOOPENGINE_BRIDGES=disabled"""
    if "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]
    assert is_bridge_enabled() is False
    print("✅ test_bridge_disabled_by_default")


def test_bridge_enabled_with_alpha():
    """LOOPENGINE_BRIDGES=alpha 启用"""
    os.environ["LOOPENGINE_BRIDGES"] = "alpha"
    assert is_bridge_enabled() is True
    print("✅ test_bridge_enabled_with_alpha")


def test_require_bridge_enabled_raises():
    """禁用时 require_bridge_enabled 抛 NotImplementedError"""
    if "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]
    try:
        require_bridge_enabled()
        assert False, "应抛 NotImplementedError"
    except NotImplementedError:
        pass
    print("✅ test_require_bridge_enabled_raises")


def test_dispatch_raises_when_disabled():
    """禁用时 dispatch_* 抛 NotImplementedError（不执行实际派遣）"""
    if "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]
    try:
        dispatch_implementer("task", "ctx", "/tmp")
        assert False, "应抛 NotImplementedError"
    except NotImplementedError:
        pass

    try:
        dispatch_spec_reviewer("req", ImplementerReport(
            status=ImplementerStatus.DONE, summary=""))
        assert False, "应抛 NotImplementedError"
    except NotImplementedError:
        pass

    try:
        dispatch_code_quality_reviewer("summary", "base", "head")
        assert False, "应抛 NotImplementedError"
    except NotImplementedError:
        pass
    print("✅ test_dispatch_raises_when_disabled")


# ===== 数据契约测试 =====

def test_implementer_status_enum():
    """ImplementerStatus 4 状态枚举完整"""
    assert ImplementerStatus.DONE.value == "DONE"
    assert ImplementerStatus.DONE_WITH_CONCERNS.value == "DONE_WITH_CONCERNS"
    assert ImplementerStatus.BLOCKED.value == "BLOCKED"
    assert ImplementerStatus.NEEDS_CONTEXT.value == "NEEDS_CONTEXT"
    assert len(ImplementerStatus) == 4
    print("✅ test_implementer_status_enum")


def test_implementer_report_dataclass():
    """ImplementerReport 默认值 + 必填字段"""
    report = ImplementerReport(
        status=ImplementerStatus.DONE,
        summary="实现完成",
    )
    assert report.status == ImplementerStatus.DONE
    assert report.files_changed == []  # 默认空 list
    assert report.test_results == ""
    assert report.concerns == []
    print("✅ test_implementer_report_dataclass")


def test_spec_verdict_dataclass():
    """SpecVerdict 三分类字段（missing/extra/misunderstandings）"""
    verdict = SpecVerdict(
        compliant=False,
        issues=["file:42: 缺少分页参数"],
        rationale="缺 2 个验收点",
        missing=["分页参数", "总数对"],
        extra=["--json flag"],
        misunderstandings=["把 POST 当成 PUT"],
    )
    assert not verdict.compliant
    assert len(verdict.missing) == 2
    assert len(verdict.extra) == 1
    assert len(verdict.misunderstandings) == 1
    print("✅ test_spec_verdict_dataclass")


def test_quality_assessment_dataclass():
    """QualityAssessment 3 层 Issues + Strengths + Assessment"""
    issues = [
        QualityIssue(severity=QualitySeverity.CRITICAL, file="x.py", line=10, description="bug"),
        QualityIssue(severity=QualitySeverity.IMPORTANT, file="y.py", line=20, description="refactor"),
        QualityIssue(severity=QualitySeverity.MINOR, file="z.py", line=30, description="style"),
    ]
    assessment = QualityAssessment(
        strengths=["简洁", "测试覆盖好"],
        issues=issues,
        assessment="Needs Fixes",
    )
    assert len(assessment.issues) == 3
    assert assessment.issues[0].severity == QualitySeverity.CRITICAL
    assert len(assessment.strengths) == 2
    print("✅ test_quality_assessment_dataclass")


# ===== model_select 信号测试 =====

def test_model_select_cheap():
    """1 文件 + 无集成 + 无设计判断 → cheap"""
    tier = model_select({
        "file_count": 1,
        "has_integration": False,
        "requires_design_judgment": False,
    })
    assert tier == "cheap"
    print("✅ test_model_select_cheap")


def test_model_select_standard():
    """多文件 / 有集成 → standard"""
    tier = model_select({
        "file_count": 5,
        "has_integration": True,
        "requires_design_judgment": False,
    })
    assert tier == "standard"
    print("✅ test_model_select_standard")


def test_model_select_capable():
    """需设计判断 → capable"""
    tier = model_select({
        "file_count": 10,
        "has_integration": True,
        "requires_design_judgment": True,
    })
    assert tier == "capable"
    print("✅ test_model_select_capable")


# ===== handle_implementer_status 状态机测试 =====

def test_handle_status_done():
    """DONE → PROCEED_TO_SPEC_REVIEW"""
    report = ImplementerReport(status=ImplementerStatus.DONE, summary="")
    action = handle_implementer_status(ImplementerStatus.DONE, report)
    assert action == "PROCEED_TO_SPEC_REVIEW"
    print("✅ test_handle_status_done")


def test_handle_status_blocked():
    """BLOCKED → ESCALATE_TO_HUMAN"""
    report = ImplementerReport(status=ImplementerStatus.BLOCKED, summary="")
    action = handle_implementer_status(ImplementerStatus.BLOCKED, report)
    assert action == "ESCALATE_TO_HUMAN"
    print("✅ test_handle_status_blocked")


def test_handle_status_needs_context():
    """NEEDS_CONTEXT → PROVIDE_CONTEXT_AND_REDISPATCH"""
    report = ImplementerReport(status=ImplementerStatus.NEEDS_CONTEXT, summary="")
    action = handle_implementer_status(ImplementerStatus.NEEDS_CONTEXT, report)
    assert action == "PROVIDE_CONTEXT_AND_REDISPATCH"
    print("✅ test_handle_status_needs_context")


# ===== review_gate 强顺序测试 =====

def test_review_gate_spec_passed():
    """spec ✅ → True（可继续 code quality）"""
    verdict = SpecVerdict(compliant=True, issues=[], rationale="OK")
    assert review_gate(verdict) is True
    print("✅ test_review_gate_spec_passed")


def test_review_gate_spec_failed():
    """spec ❌ → False（必须修复重审）"""
    verdict = SpecVerdict(compliant=False, issues=["file:42"], rationale="缺 1 项")
    assert review_gate(verdict) is False
    print("✅ test_review_gate_spec_failed")


def test_review_gate_quality_rejected():
    """spec ✅ + quality Rejected → False"""
    verdict = SpecVerdict(compliant=True, issues=[], rationale="OK")
    quality = QualityAssessment(
        strengths=[], issues=[], assessment="Rejected"
    )
    assert review_gate(verdict, quality) is False
    print("✅ test_review_gate_quality_rejected")


def test_review_gate_all_passed():
    """spec ✅ + quality Approved → True"""
    verdict = SpecVerdict(compliant=True, issues=[], rationale="OK")
    quality = QualityAssessment(
        strengths=["好"], issues=[], assessment="Approved"
    )
    assert review_gate(verdict, quality) is True
    print("✅ test_review_gate_all_passed")


# ===== 测试入口 =====

def run_all():
    tests = [
        test_bridge_disabled_by_default,
        test_bridge_enabled_with_alpha,
        test_require_bridge_enabled_raises,
        test_dispatch_raises_when_disabled,
        test_implementer_status_enum,
        test_implementer_report_dataclass,
        test_spec_verdict_dataclass,
        test_quality_assessment_dataclass,
        test_model_select_cheap,
        test_model_select_standard,
        test_model_select_capable,
        test_handle_status_done,
        test_handle_status_blocked,
        test_handle_status_needs_context,
        test_review_gate_spec_passed,
        test_review_gate_spec_failed,
        test_review_gate_quality_rejected,
        test_review_gate_all_passed,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: 异常 {type(e).__name__}: {e}")
            failed += 1

    # 恢复环境变量
    if ORIG_ENV:
        os.environ["LOOPENGINE_BRIDGES"] = ORIG_ENV
    elif "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]

    print(f"\n{'='*50}")
    print(f"bridges/ 契约测试: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    if failed == 0:
        print("🎉 全部通过")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run_all())
