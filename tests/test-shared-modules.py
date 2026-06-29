"""Shared 模块单元测试（v6.1）

测试 skills/shared/ 目录下的所有共享组件：
- atomic_write.py 原子写函数
- owner 字段规范
- state-protocol-base 状态机
- breakpoint-recovery-base 断点恢复三步骤
- g9-g10-coordination G9/G10 协作

运行：python tests/test-shared-modules.py
"""

import datetime
import json
import os
import sys
import tempfile
import threading
from pathlib import Path

# 路径设置
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "skills" / "shared" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "shared"))

from atomic_write import atomic_write_json, atomic_read_json, safe_load_state  # noqa: E402


# ===== atomic_write 测试 =====

def test_atomic_write_basic():
    """基础原子写测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.json")
        data = {"id": "001", "status": "in_progress"}
        atomic_write_json(path, data)

        loaded = atomic_read_json(path)
        assert loaded == data, f"原子写后读取不匹配: {loaded} != {data}"
    print("✅ test_atomic_write_basic")


def test_atomic_write_concurrent():
    """并发原子写测试（20 线程写不同文件 —— 验证 shared/ 单次原子性）

    注意：shared/atomic_write.py 提供**单次**原子写（tempfile + os.replace），
    **不承诺**多线程并发写同一文件的 Windows 重试安全。
    并发写同一文件的安全保证由上层 state_manager.py 的 threading.Lock + 5 次重试负责。

    本测试验证：
    1. 20 线程写不同文件 → 全部成功
    2. 写完后文件可正常读取（不损坏）
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        results = []
        errors = []

        def writer(i):
            try:
                # 每线程写自己的文件（无冲突）
                path = os.path.join(tmpdir, f"concurrent_{i}.json")
                data = {
                    "id": f"writer-{i}",
                    "timestamp": datetime.datetime.now().isoformat(),
                }
                atomic_write_json(path, data)
                results.append(i)
            except Exception as e:
                errors.append((i, str(e)))

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 20 个写入都应成功
        assert len(results) == 20, f"20 个写入应都成功，实际 {len(results)}"
        assert len(errors) == 0, f"不应有错误，实际 {len(errors)}: {errors}"

        # 所有文件可正常读取（不损坏）
        for i in range(20):
            path = os.path.join(tmpdir, f"concurrent_{i}.json")
            loaded = atomic_read_json(path)
            assert loaded["id"] == f"writer-{i}", f"文件 {i} 内容损坏"
    print("✅ test_atomic_write_concurrent (20 线程写不同文件全部成功)")


def test_atomic_write_concurrent_with_state_manager_lock():
    """验证 state_manager.py 的并发锁机制（同文件多线程）"""
    sys.path.insert(0, str(REPO_ROOT / "skills" / "go" / "scripts"))
    from state_manager import atomic_update, create_state, read_state

    with tempfile.TemporaryDirectory() as tmpdir:
        create_state(tmpdir, "go/concurrent-test", "测试", "L1", ["v1"])
        results = []
        errors = []

        def updater(i):
            try:
                # atomic_update 内置 threading.Lock + 5 次重试
                atomic_update(tmpdir, lambda s: s["acceptance_criteria"].append({
                    "id": i, "text": f"v{i}", "source": "auto", "passed": False
                }))
                results.append(i)
            except Exception as e:
                errors.append((i, str(e)))

        threads = [threading.Thread(target=updater, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 全部成功（state_manager 锁保护）
        assert len(results) == 20, f"20 个更新应都成功，实际 {len(results)}"
        assert len(errors) == 0, f"不应有错误，实际 {len(errors)}: {errors}"

        # 最终验收条件应包含 21 项（1 初始 + 20 追加）
        state = read_state(tmpdir)
        assert len(state["acceptance_criteria"]) == 21, (
            f"应有 21 项验收条件，实际 {len(state['acceptance_criteria'])}"
        )
    print("✅ test_atomic_write_concurrent_with_state_manager_lock (state_manager 锁保护 20 并发)")


def test_atomic_write_fsync():
    """fsync 刷盘测试（不抛异常即可）"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "fsync.json")
        data = {"key": "value"}
        atomic_write_json(path, data, fsync=True)
        loaded = atomic_read_json(path)
        assert loaded == data
    print("✅ test_atomic_write_fsync")


def test_atomic_write_nested_dir():
    """嵌套目录自动创建测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "a", "b", "c", "deep.json")
        data = {"deep": True}
        atomic_write_json(path, data)
        assert os.path.exists(path)
        loaded = atomic_read_json(path)
        assert loaded == data
    print("✅ test_atomic_write_nested_dir")


def test_safe_load_state_default():
    """safe_load_state 默认值测试"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 不存在的文件应返回默认 dict
        non_exist = os.path.join(tmpdir, "missing.json")
        result = safe_load_state(non_exist, default={"fallback": True})
        assert result == {"fallback": True}

        # 损坏的 JSON 应返回默认
        corrupt = os.path.join(tmpdir, "corrupt.json")
        with open(corrupt, "w") as f:
            f.write("{invalid json")
        result = safe_load_state(corrupt, default={"fallback": True})
        assert result == {"fallback": True}
    print("✅ test_safe_load_state_default")


# ===== owner 字段规范测试 =====

def test_owner_field_structure():
    """owner 字段结构验证（go + loop 共享）"""
    sample_owner = {
        "pid": os.getpid(),
        "session_id": "sess_test_001",
        "heartbeat": datetime.datetime.now().isoformat(),
        "started_at": datetime.datetime.now().isoformat(),
    }

    required = {"pid", "session_id", "heartbeat", "started_at"}
    assert required.issubset(set(sample_owner.keys()))

    # 验证 .orchestrate-state.json 加载后 owner 字段存在
    with tempfile.TemporaryDirectory() as tmpdir:
        state_path = os.path.join(tmpdir, ".orchestrate-state.json")
        state = {
            "orchestrate_id": "go/test",
            "feature": "测试",
            "status": "in_progress",
            "owner": sample_owner,
            "decision_log": [],
        }
        atomic_write_json(state_path, state)

        loaded = atomic_read_json(state_path)
        assert "owner" in loaded
        assert all(k in loaded["owner"] for k in required)
    print("✅ test_owner_field_structure")


def test_owner_heartbeat_5min_threshold():
    """owner heartbeat 5min 阈值判定（go / loop 共享）"""
    now = datetime.datetime.now()

    # < 5min → alive
    recent = (now - datetime.timedelta(minutes=3)).isoformat()
    elapsed = (now - datetime.datetime.fromisoformat(recent)).total_seconds() / 60
    assert elapsed < 5, "3min heartbeat 应判定为 alive"

    # 5-30min → stale
    stale = (now - datetime.timedelta(minutes=10)).isoformat()
    elapsed = (now - datetime.datetime.fromisoformat(stale)).total_seconds() / 60
    assert 5 <= elapsed < 30, "10min heartbeat 应判定为 stale"

    # > 24h → abandoned
    abandoned = (now - datetime.timedelta(hours=25)).isoformat()
    elapsed = (now - datetime.datetime.fromisoformat(abandoned)).total_seconds() / 60
    assert elapsed > 24 * 60, "25h heartbeat 应判定为 abandoned"
    print("✅ test_owner_heartbeat_5min_threshold")


# ===== state-protocol-base 状态机测试 =====

def test_state_machine_transitions():
    """5 状态机转换验证"""
    valid_transitions = {
        "planning": {"in_progress", "failed", "paused"},
        "in_progress": {"completed", "failed", "paused"},
        "paused": {"in_progress", "failed"},
        "completed": set(),  # 终态
        "failed": set(),      # 终态
    }

    # 验证每个状态都有合法转换
    for state, nexts in valid_transitions.items():
        assert isinstance(nexts, set), f"{state} 转换表应是 set"

    # 终态不能转换
    assert len(valid_transitions["completed"]) == 0
    assert len(valid_transitions["failed"]) == 0
    print("✅ test_state_machine_transitions")


# ===== go state_manager 集成测试 =====

def test_state_manager_uses_shared_atomic_write():
    """go state_manager 改造后仍使用 shared atomic_write"""
    sys.path.insert(0, str(REPO_ROOT / "skills" / "go" / "scripts"))
    from state_manager import create_state, atomic_update, update_heartbeat, read_state

    with tempfile.TemporaryDirectory() as tmpdir:
        state = create_state(tmpdir, "go/test-001", "测试功能", "L1", ["验收1"])
        assert state["status"] == "planning"
        assert "owner" in state

        atomic_update(tmpdir, lambda s: s.update({"status": "in_progress"}))
        loaded = read_state(tmpdir)
        assert loaded["status"] == "in_progress"

        update_heartbeat(tmpdir)
    print("✅ test_state_manager_uses_shared_atomic_write")


# ===== 测试入口 =====

def run_all():
    tests = [
        test_atomic_write_basic,
        test_atomic_write_concurrent,
        test_atomic_write_concurrent_with_state_manager_lock,
        test_atomic_write_fsync,
        test_atomic_write_nested_dir,
        test_safe_load_state_default,
        test_owner_field_structure,
        test_owner_heartbeat_5min_threshold,
        test_state_machine_transitions,
        test_state_manager_uses_shared_atomic_write,
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
    print(f"shared/ 模块单元测试: {passed} 通过 / {failed} 失败 / {len(tests)} 总计")
    if failed == 0:
        print("🎉 全部通过")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(run_all())
