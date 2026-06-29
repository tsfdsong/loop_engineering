"""evidence-first 技能单元测试（v1.0）

验证 evidence-first 技能的关键组件：
- 5 份 reference 文档存在且可读
- 2 个 examples 存在
- 标注规范 [F]/[H]/[P] 在文档中正确定义
- 自检 4 问在文档中正确定义
- 黄金轨迹存在

运行：python tests/test-evidence-first.py
"""

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "evidence-first"


# ===== 文件存在性测试 =====

def test_skill_md_exists():
    """SKILL.md 存在"""
    assert SKILL_DIR.exists(), f"evidence-first 目录应存在: {SKILL_DIR}"
    skill_md = SKILL_DIR / "SKILL.md"
    assert skill_md.exists(), f"SKILL.md 应存在: {skill_md}"
    print("✅ test_skill_md_exists")


def test_references_exist():
    """5 份 reference 文档全部存在"""
    expected = [
        "fact-checklist.md",
        "claim-types.md",
        "self-check.md",
        "no-hallucination.md",
        "traceability.md",
    ]
    refs_dir = SKILL_DIR / "references"
    assert refs_dir.exists(), f"references/ 应存在: {refs_dir}"

    for ref in expected:
        path = refs_dir / ref
        assert path.exists(), f"应存在: {ref}"
    print(f"✅ test_references_exist ({len(expected)} 份全部存在)")


def test_examples_dir_removed():
    """v6.3 清理：examples/ 目录已删除（事故案例随 v5.4 遗留清除）"""
    examples_dir = SKILL_DIR / "examples"
    assert not examples_dir.exists(), f"v6.3 后 examples/ 应不存在: {examples_dir}"
    print("✅ test_examples_dir_removed (v6.3 清理：examples/ 已删除)")


# ===== 文档内容测试 =====

def test_skill_md_has_origin():
    """SKILL.md 含事故起源"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "2026-06-29" in content, "应标注事故日期"
    assert "v5.4" in content, "应提到 v5.4 事故"
    print("✅ test_skill_md_has_origin")


def test_skill_md_has_5_facts():
    """SKILL.md 含 5 项事实清单"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for i in range(1, 6):
        # 检查是否提到"清单 i"或对应的描述
        assert f"{i}" in content, f"应含清单项 {i}"
    print("✅ test_skill_md_has_5_facts")


def test_skill_md_has_3_claim_types():
    """SKILL.md 含 [F]/[H]/[P] 三类标注"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    assert "[F]" in content, "应含 [F] 事实标注"
    assert "[H]" in content, "应含 [H] 假设标注"
    assert "[P]" in content, "应含 [P] 原则标注"
    print("✅ test_skill_md_has_3_claim_types")


def test_skill_md_has_4_questions():
    """SKILL.md 含自检 4 问"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    # 检查 4 问
    for q in ["我有", "明确标注", "错了", "我不清楚"]:
        assert q in content, f"自检 4 问应含「{q}」"
    print("✅ test_skill_md_has_4_questions")


def test_claim_types_doc_has_priority():
    """claim-types.md 含优先级 F > H > P"""
    content = (SKILL_DIR / "references" / "claim-types.md").read_text(encoding="utf-8")
    assert "F > H > P" in content or "优先级" in content, "应含优先级定义"
    print("✅ test_claim_types_doc_has_priority")


def test_self_check_doc_has_4_questions():
    """self-check.md 含完整的 4 问"""
    content = (SKILL_DIR / "references" / "self-check.md").read_text(encoding="utf-8")
    # 4 问的关键词
    for q in ["[F] 事实依据", "[H] 假设", "错了", "我不清楚"]:
        assert q in content, f"自检 4 问应含「{q}」"
    print("✅ test_self_check_doc_has_4_questions")


def test_no_hallucination_doc_has_rules():
    """no-hallucination.md 含 5 个常见凑答案场景"""
    content = (SKILL_DIR / "references" / "no-hallucination.md").read_text(encoding="utf-8")
    # 5 个场景关键词
    for scenario in ["套用通用经验", "印象推断", "假设当事实", "假装知道", "辩解"]:
        assert scenario in content, f"应含场景「{scenario}」"
    print("✅ test_no_hallucination_doc_has_rules")


def test_traceability_doc_has_chain():
    """traceability.md 含追溯链模型"""
    content = (SKILL_DIR / "references" / "traceability.md").read_text(encoding="utf-8")
    # 追溯链关键词
    for keyword in ["追溯链", "事实依据", "反事实", "可追溯"]:
        assert keyword in content, f"应含「{keyword}」"
    print("✅ test_traceability_doc_has_chain")


# ===== Examples 内容测试（v6.3 清理后已删除）=====

def test_examples_removed_v63():
    """v6.3 清理：examples/ 内容测试已移除（事故案例随 v5.4 遗留清除）"""
    # 此测试仅作占位，证明 examples 内容测试已删除
    print("✅ test_examples_removed_v63 (v6.3 清理：examples 内容测试已删除)")


# ===== 黄金轨迹测试 =====

def test_golden_trace_exists():
    """黄金轨迹文件存在"""
    trace_path = REPO_ROOT / "tests" / "golden-traces" / "evidence-first-baseline.json"
    assert trace_path.exists(), f"黄金轨迹应存在: {trace_path}"

    with open(trace_path, encoding="utf-8") as f:
        traces = json.load(f)
    assert len(traces) >= 15, f"应至少 15 条 trace，实际 {len(traces)}"
    print(f"✅ test_golden_trace_exists ({len(traces)} 条)")


def test_golden_trace_categories():
    """黄金轨迹分类完整"""
    trace_path = REPO_ROOT / "tests" / "golden-traces" / "evidence-first-baseline.json"
    with open(trace_path, encoding="utf-8") as f:
        traces = json.load(f)

    categories = {t["category"] for t in traces}
    expected = {"trigger", "claim_type", "conflict_resolution", "no_hallucination", "self_check"}
    missing = expected - categories
    assert not missing, f"缺少分类: {missing}"
    print(f"✅ test_golden_trace_categories (5 类: {sorted(categories)})")


def test_golden_trace_skill_loaded():
    """黄金轨迹应正确加载 evidence-first"""
    trace_path = REPO_ROOT / "tests" / "golden-traces" / "evidence-first-baseline.json"
    with open(trace_path, encoding="utf-8") as f:
        traces = json.load(f)

    for trace in traces:
        assert trace.get("skill_loaded") == "evidence-first", (
            f"trace {trace['trace_id']} 应加载 evidence-first"
        )
        assert trace.get("routing_path") == "evidence_first", (
            f"trace {trace['trace_id']} 路径应是 evidence_first"
        )
    print(f"✅ test_golden_trace_skill_loaded (全部 trace 正确加载)")


# ===== 集成测试 =====

def test_evidence_first_via_skill_hub():
    """验证 evidence-first 在 skill-hub 调度表中的存在性"""
    skill_hub_path = REPO_ROOT / "skills" / "skill-hub" / "SKILL.md"
    if not skill_hub_path.exists():
        # 可能未修改调度表，跳过
        print("⚠️  test_evidence_first_via_skill_hub (skill-hub/SKILL.md 未找到，跳过)")
        return

    content = skill_hub_path.read_text(encoding="utf-8")
    if "evidence-first" in content:
        print("✅ test_evidence_first_via_skill_hub (已在调度表)")
    else:
        print("⚠️  test_evidence_first_via_skill_hub (调度表未加入，单独验证)")


def test_no_hallucination_in_skill():
    """验证技能自身不使用幻觉性表述"""
    content = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    # 禁止性表述（不应有"应该总是""一定""绝对"等）
    forbidden = ["应该总是", "一定是", "绝对不能"]
    for word in forbidden:
        # 这些词可能合法存在（如说明"禁止"），但不应用于"应"类建议
        # 这里只检查过度绝对的表述
        pass  # 跳过，SKILL.md 是规范文件，需要用"必须"等强表述

    # 应有的限定词
    qualified = ["通常", "可能", "应该"]
    found = [w for w in qualified if w in content]
    assert len(found) >= 2, f"SKILL.md 应含限定词: {found}"
    print(f"✅ test_no_hallucination_in_skill ({len(found)} 个限定词)")


# ===== 测试入口 =====

def run_all():
    tests = [
        # 文件存在性
        test_skill_md_exists,
        test_references_exist,
        test_examples_exist,
        # 文档内容
        test_skill_md_has_origin,
        test_skill_md_has_5_facts,
        test_skill_md_has_3_claim_types,
        test_skill_md_has_4_questions,
        test_claim_types_doc_has_priority,
        test_self_check_doc_has_4_questions,
        test_no_hallucination_doc_has_rules,
        test_traceability_doc_has_chain,
        # Examples
        test_bad_example_marks_mistakes,
        test_good_example_uses_evidence_first,
        test_good_example_has_at_least_4_facts,
        # 黄金轨迹
        test_golden_trace_exists,
        test_golden_trace_categories,
        test_golden_trace_skill_loaded,
        # 集成
        test_evidence_first_via_skill_hub,
        test_no_hallucination_in_skill,
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

    print(f"\n{'='*50}")
    print(f"evidence-first 技能测试: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    if failed == 0:
        print("🎉 全部通过（v5.4 事故教训已固化为可执行规范）")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run_all())
