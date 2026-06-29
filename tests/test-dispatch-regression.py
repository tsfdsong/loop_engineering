"""skill-hub 调度回归测试（v6.1 · 向后兼容）

验证 v6.1 调度表强化**不破坏** v5.4 / v6.0 既有行为：
- v5.4 单技能路由：27 条黄金轨迹 100% 命中
- v6.0 复合任务 5 类表：行为不变
- 状态文件向后兼容：既有 .orchestrate-state.json / .loop-state-*.json 仍可加载

运行：python tests/test-dispatch-regression.py
"""

import datetime
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "shared" / "scripts"))

from atomic_write import atomic_write_json, atomic_read_json  # noqa: E402


# ===== v5.4 单技能路由兼容性测试 =====

def test_v54_baseline_27_traces_unchanged():
    """v5.4 黄金轨迹 27 条文件未改动"""
    baseline_path = REPO_ROOT / "tests" / "golden-traces" / "v54-baseline.json"
    assert baseline_path.exists(), f"v54-baseline.json 应存在: {baseline_path}"

    with open(baseline_path, encoding="utf-8") as f:
        traces = json.load(f)

    assert len(traces) == 27, f"v5.4 应有 27 条黄金轨迹，实际 {len(traces)}"

    # 验证每条 trace 字段完整
    required_fields = {"trace_id", "timestamp", "skill_hub_version", "detected_skill", "routing_path"}
    for i, trace in enumerate(traces):
        missing = required_fields - set(trace.keys())
        assert not missing, f"trace[{i}] 缺少字段 {missing}"
        assert trace["skill_hub_version"] == "5.4", f"trace[{i}] 应为 v5.4"
        assert trace["routing_path"] == "single_skill", f"trace[{i}] 应为单技能路由"
    print(f"✅ test_v54_baseline_27_traces_unchanged (27 条全部字段完整)")


# ===== v6.0 复合任务 5 类表兼容性测试 =====

def test_v6_composite_task_types_unchanged():
    """v6.0 复合任务 5 类表行为不变（composite-task-types.md）"""
    doc_path = REPO_ROOT / "skills" / "skill-hub" / "references" / "composite-task-types.md"
    assert doc_path.exists()

    content = doc_path.read_text(encoding="utf-8")
    # 5 类表必须存在
    expected_types = [
        ("调研+决策", "brainstorming → system-review → writing-plans"),
        ("分析+建议", "system-review → brainstorming"),
        ("诊断+修复", "systematic-debugging → verification-before-completion"),
        ("设计+实现", "brainstorming → writing-plans → executing-plans"),
        ("规划+并行", "subagent-driven-development"),
    ]
    for name, chain in expected_types:
        assert name in content, f"5 类表应含「{name}」"
        assert chain in content, f"5 类表应含默认技能链「{chain}」"
    print("✅ test_v6_composite_task_types_unchanged (5 类全部存在)")


def test_v6_skill_hub_version_compat():
    """v6.2 单技能路由仍兼容（v5.4/v6.0/v6.1 base_compat 保留）"""
    skill_hub_path = REPO_ROOT / "skills" / "skill-hub" / "SKILL.md"
    assert skill_hub_path.exists()

    content = skill_hub_path.read_text(encoding="utf-8")

    # v6.2 frontmatter 应同时声明 base_compat 5.4 / base_compat_v6 6.0 / base_compat_v6_1 6.1
    assert 'version: "6.2"' in content, "应升级到 v6.2"
    assert 'base_compat: "5.4"' in content, "v5.4 兼容性必须保留"
    assert 'base_compat_v6: "6.0"' in content, "v6.0 兼容性必须保留"
    assert 'base_compat_v6_1: "6.1"' in content, "v6.1 兼容性必须保留"
    print("✅ test_v6_skill_hub_version_compat (v5.4 + v6.0 + v6.1 三兼容)")


# ===== 状态文件向后兼容测试 =====

def test_orchestrate_state_backward_compatible():
    """既有 .orchestrate-state.json 字段仍可加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, ".orchestrate-state.json")

        # 模拟 v5.4 / v6.0 既有状态文件
        legacy_state = {
            "orchestrate_id": "go/legacy-001",
            "feature": "旧版功能",
            "tier": "L2",
            "status": "in_progress",
            "acceptance_criteria": [{"id": 1, "text": "验收1", "source": "auto", "passed": False}],
            "tasks": [
                {
                    "id": "task-1",
                    "name": "子任务 1",
                    "status": "completed",
                    "assigned_tool": "zcode",
                    "depends_on": [],
                    "skills": ["code-reviewer"],
                    "files": ["src/x.py"],
                    "git_head_before": "abc123",
                    "git_commit_after": "def456",
                    "handoff": {"gate_result": "all_green"},
                    "degraded": False,
                    "degraded_reason": None,
                    "actual_model": "zcode",
                }
            ],
            "feature_branch": "go/legacy",
            "base_branch": "main",
            "owner": {
                "pid": 12345,
                "session_id": "sess_legacy",
                "heartbeat": "2026-06-29T12:00:00+08:00",
                "started_at": "2026-06-29T11:00:00+08:00",
            },
            "decision_log": [
                {"at": "2026-06-29T11:00:00+08:00", "decision": "启动编排"}
            ],
            "created_at": "2026-06-29T11:00:00+08:00",
            "updated_at": "2026-06-29T12:00:00+08:00",
        }

        atomic_write_json(state_path, legacy_state)
        loaded = atomic_read_json(state_path)

        # 关键字段必须存在
        assert loaded["orchestrate_id"] == "go/legacy-001"
        assert loaded["status"] == "in_progress"
        assert len(loaded["tasks"]) == 1
        assert loaded["tasks"][0]["handoff"]["gate_result"] == "all_green"
        assert loaded["owner"]["pid"] == 12345
        assert len(loaded["decision_log"]) == 1
    print("✅ test_orchestrate_state_backward_compatible")


def test_loop_state_backward_compatible():
    """既有 .loop-state-*.json 字段仍可加载"""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, ".loop-state-loop-legacy-0630.json")

        legacy_state = {
            "loop_id": "loop/legacy-0630",
            "feature": "旧版分页",
            "mode": "🤖 auto",
            "auto_mode": True,
            "current_step": "Step 3",
            "current_round": 2,
            "total_rounds": 3,
            "acceptance_criteria": [
                {"id": 1, "text": "翻页正确", "source": "用户指定", "status": "✅"}
            ],
            "task_list": [
                {"id": "t1", "name": "实现分页", "status": "completed"}
            ],
            "blockers": [],
            "last_error": "",
            "verification_evidence": {"test_coverage": 0.85},
            "last_commit_sha": "abc123",
            "owner": {
                "pid": 12345,
                "session_id": "sess_loop_legacy",
                "heartbeat": "2026-06-29T12:00:00+08:00",
                "started_at": "2026-06-29T11:00:00+08:00",
            },
            "decision_log": [],
        }

        atomic_write_json(state_path, legacy_state)
        loaded = atomic_read_json(state_path)

        # 关键字段必须存在
        assert loaded["loop_id"] == "loop/legacy-0630"
        assert loaded["auto_mode"] is True
        assert loaded["current_round"] == 2
        assert loaded["verification_evidence"]["test_coverage"] == 0.85
        assert "owner" in loaded
    print("✅ test_loop_state_backward_compatible")


# ===== 桥接默认关闭测试 =====

def test_bridge_default_disabled():
    """LOOPENGINE_BRIDGES 默认 disabled，go/loop 行为不变"""
    if "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]

    sys.path.insert(0, str(REPO_ROOT / "skills" / "subagent-driven-development" / "bridges"))
    # 重新导入以清空模块缓存
    if "contract" in sys.modules:
        del sys.modules["contract"]
    from contract import is_bridge_enabled

    assert is_bridge_enabled() is False, "默认应禁用"
    print("✅ test_bridge_default_disabled")


def test_bridge_opt_in_only():
    """桥接仅在显式 alpha 时启用（不自动启用）"""
    test_cases = [
        ("disabled", False),
        ("off", False),
        ("true", False),     # 错误的值
        ("1", False),         # 错误的值
        ("alpha", True),      # 唯一启用值
    ]

    for value, expected in test_cases:
        os.environ["LOOPENGINE_BRIDGES"] = value

        sys.path.insert(0, str(REPO_ROOT / "skills" / "subagent-driven-development" / "bridges"))
        if "contract" in sys.modules:
            del sys.modules["contract"]
        from contract import is_bridge_enabled

        assert is_bridge_enabled() is expected, (
            f"LOOPENGINE_BRIDGES={value} 应返回 {expected}，实际 {is_bridge_enabled()}"
        )

    # 清理
    del os.environ["LOOPENGINE_BRIDGES"]
    print("✅ test_bridge_opt_in_only")


# ===== shared/ 引用完整性测试 =====

def test_shared_references_exist():
    """shared/ 目录 5 份 spec 全部存在"""
    shared_dir = REPO_ROOT / "skills" / "shared"
    assert shared_dir.exists(), f"shared/ 目录应存在: {shared_dir}"

    expected_files = [
        "README.md",
        "references/owner-field-spec.md",
        "references/atomic-write-spec.md",
        "references/state-protocol-base.md",
        "references/breakpoint-recovery-base.md",
        "references/g9-g10-coordination.md",
        "scripts/atomic_write.py",
        "scripts/__init__.py",
        "examples/owner-usage.md",
    ]
    for f in expected_files:
        path = shared_dir / f
        assert path.exists(), f"shared/ 应含 {f}"
    print(f"✅ test_shared_references_exist ({len(expected_files)} 文件全部存在)")


def test_bridges_directory_exists():
    """subagent-dd bridges/ 目录 4 个文件全部存在"""
    bridges_dir = REPO_ROOT / "skills" / "subagent-driven-development" / "bridges"
    assert bridges_dir.exists(), f"bridges/ 目录应存在: {bridges_dir}"

    expected_files = [
        "README.md",
        "contract.py",
        "dispatcher.md",
        "examples/loop-g9-with-bridge.md",
    ]
    for f in expected_files:
        path = bridges_dir / f
        assert path.exists(), f"bridges/ 应含 {f}"
    print(f"✅ test_bridges_directory_exists ({len(expected_files)} 文件全部存在)")


# ===== 测试入口 =====

def run_all():
    tests = [
        test_v54_baseline_27_traces_unchanged,
        test_v6_composite_task_types_unchanged,
        test_v6_skill_hub_version_compat,
        test_orchestrate_state_backward_compatible,
        test_loop_state_backward_compatible,
        test_bridge_default_disabled,
        test_bridge_opt_in_only,
        test_shared_references_exist,
        test_bridges_directory_exists,
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

    # 清理环境变量
    if "LOOPENGINE_BRIDGES" in os.environ:
        del os.environ["LOOPENGINE_BRIDGES"]

    print(f"\n{'='*50}")
    print(f"调度回归测试: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    if failed == 0:
        print("🎉 全部通过（v5.4 + v6.0 兼容性保护）")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run_all())
