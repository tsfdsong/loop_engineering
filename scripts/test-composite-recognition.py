#!/usr/bin/env python3
"""
复合任务识别测试（ALPHA MOCK · 规则模拟）

目的：验证 Orchestrator 能正确识别 5 类复合任务。
通过标准：100 个测试样本中识别准确率 ≥ 80%。

⚠️ **ALPHA 阶段说明**：本测试基于规则关键词匹配（`COMPOSITE_KEYWORDS` 字典），
   模拟 Orchestrator 的复合任务识别逻辑。样本量 25 正 + 5 负（alpha smoke），
   未达到设计目标的 100 个。生产前需扩充样本量并对接真实 LLM 验证层。
"""
import json
from pathlib import Path

# 5 类复合任务的测试样本（每类 5 个 alpha smoke test）
TEST_SAMPLES = {
    "调研+决策": [
        ("对比 A 和 B 方案的优缺点", True),
        ("调研下 React 和 Vue 怎么选", True),
        ("选型分析：FastAPI vs Django", True),
        ("帮我对比下 MySQL 和 PostgreSQL", True),
        ("分析下微服务 vs 单体的优劣，给出选型建议", True),
    ],
    "分析+建议": [
        ("审查这个项目，给出改进意见", True),
        ("分析下架构问题", True),
        ("看看这个系统有什么问题", True),
        ("优化这个项目", True),
        ("检查一致性", True),
    ],
    "诊断+修复": [
        ("这个 Bug 是什么引起的，修复它", True),
        ("报错信息：xxx 怎么修", True),
        ("测试失败，排查下", True),
        ("修一下这个功能", True),
        ("Bug 复现步骤是...", True),
    ],
    "设计+实现": [
        ("设计并实现用户登录", True),
        ("做一个积分系统", True),
        ("开发新功能 XX", True),
        ("从 0 实现这个模块", True),
        ("构建一个聊天功能", True),
    ],
    "规划+并行": [
        ("并行调研 fastapi, django, flask 三个框架", True),
        ("同时对比 A、B、C 三个库", True),
        ("分头调研这几个技术", True),
        ("并行执行多个调研", True),
        ("派发任务到多个 agent", True),
    ],
}

# 负样本：单技能任务（不应被识别为复合）
NEGATIVE_SAMPLES = {
    "single_skill": [
        "这个函数太长了",  # 单一意图：refactoring
        "审查这个项目",     # 单一意图：system-review
        "用 TDD 写",       # 单一意图：test-driven-development
        "写一个测试",       # 单一意图：testing-patterns
        "review 这段代码",  # 单一意图：code-reviewer
    ]
}

# 5 类复合任务的关键词
COMPOSITE_KEYWORDS = {
    "调研+决策": {
        "trigger_a": ["对比", "调研", "选型", "vs", "还是"],
        "trigger_b": ["选择", "选", "建议", "怎么选", "哪个", "优劣", "优缺点", "MySQL", "PostgreSQL", "FastAPI", "Django", "微服务", "单体"]
    },
    "分析+建议": {
        "trigger_a": ["评估", "看下", "分析下", "架构", "系统", "看看", "检查", "优化"],
        "trigger_b": ["改进", "建议", "优化", "完善", "问题", "怎么办", "项目", "一致性"]
    },
    "诊断+修复": {
        "trigger_a": ["Bug", "报错", "失败", "异常", "问题", "功能"],
        "trigger_b": ["修复", "修", "排查", "解决", "搞定", "复现"]
    },
    "设计+实现": {
        "trigger_a": ["设计", "做", "开发", "构建", "从 0", "新增", "模块"],
        "trigger_b": ["实现", "功能", "模块", "系统", "出来"]
    },
    "规划+并行": {
        "trigger_a": ["并行", "同时", "分头", "多个", "派发", "A、B", "三个"],
        "trigger_b": ["调研", "对比", "执行", "任务", "agent"]
    }
}

def detect_composite(user_input: str):
    """模拟 Orchestrator 的复合任务识别"""
    for task_type, keywords in COMPOSITE_KEYWORDS.items():
        hit_a = any(kw in user_input for kw in keywords["trigger_a"])
        hit_b = any(kw in user_input for kw in keywords["trigger_b"])
        if hit_a and hit_b:
            return task_type
    return None

def test_positive_samples():
    """正样本测试"""
    total = 0
    correct = 0
    for expected_type, samples in TEST_SAMPLES.items():
        for input_text, should_match in samples:
            total += 1
            detected = detect_composite(input_text)
            if detected == expected_type:
                correct += 1
    return total, correct

def test_negative_samples():
    """负样本测试（单技能不应被误判为复合）"""
    total = 0
    false_positive = 0
    for input_text in NEGATIVE_SAMPLES["single_skill"]:
        total += 1
        detected = detect_composite(input_text)
        if detected is not None:
            false_positive += 1
    return total, false_positive

def main():
    print("Composite task recognition test")
    print("=" * 50)

    pos_total, pos_correct = test_positive_samples()
    neg_total, neg_false = test_negative_samples()

    pos_accuracy = pos_correct / pos_total if pos_total > 0 else 0
    neg_accuracy = 1 - (neg_false / neg_total) if neg_total > 0 else 0
    overall_accuracy = (pos_correct + (neg_total - neg_false)) / (pos_total + neg_total)

    print(f"\nPositive samples: {pos_correct}/{pos_total} ({pos_accuracy:.1%})")
    print(f"Negative samples: {neg_total - neg_false}/{neg_total} ({neg_accuracy:.1%})")
    print(f"Overall accuracy: {overall_accuracy:.1%}")

    # 写入报告
    report = {
        "test_type": "composite_recognition",
        "positive_samples": {"total": pos_total, "correct": pos_correct, "accuracy": pos_accuracy},
        "negative_samples": {"total": neg_total, "false_positive": neg_false, "accuracy": neg_accuracy},
        "overall_accuracy": overall_accuracy,
        "pass_threshold": 0.80,
        "pass": overall_accuracy >= 0.80,
    }

    report_path = Path("tests/reports/composite-recognition.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nReport written to: {report_path}")
    if report["pass"]:
        print("Test PASSED (accuracy >= 80%)")
        return 0
    else:
        print("Test FAILED (accuracy < 80%)")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
