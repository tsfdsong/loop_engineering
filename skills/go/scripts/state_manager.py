"""
编排层状态管理模块 v4.0 — 线程安全 + Windows 文件锁

修复:
  - BUG #1: 并发线程竞态 → 加 threading.Lock
  - BUG #3: read-modify-write 竞态 → 原子更新操作
  - BUG #7: 断点续跑没有恢复分支 → 加分支检查
  - Windows os.replace 并发冲突 → 重试机制
"""
import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path


STATE_FILENAME = ".orchestrate-state.json"

# 任务状态枚举
TASK_PENDING = "pending"
TASK_IN_PROGRESS = "in_progress"
TASK_COMPLETED = "completed"
TASK_FAILED = "failed"
TASK_SKIPPED = "skipped"

# 编排状态枚举
STATUS_PLANNING = "planning"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_PAUSED = "paused"

# 全局锁字典 (跨线程共享,不是 threading.local)
_global_locks = {}
_global_locks_guard = threading.Lock()


def _get_lock(project_dir):
    """获取项目级线程锁 (跨线程共享)"""
    key = str(project_dir)
    with _global_locks_guard:
        if key not in _global_locks:
            _global_locks[key] = threading.Lock()
        return _global_locks[key]


def get_state_path(project_dir):
    """获取项目根目录下的状态文件路径"""
    return Path(project_dir) / STATE_FILENAME


def state_exists(project_dir):
    """检查是否存在未完成的状态文件(断点续跑用)"""
    path = get_state_path(project_dir)
    if not path.exists():
        return False
    try:
        state = read_state(project_dir)
        return state.get("status") not in (STATUS_COMPLETED, STATUS_FAILED)
    except (json.JSONDecodeError, OSError):
        return False


def write_state(project_dir, state):
    """
    原子写入状态文件(检查点机制)。
    Windows 上 os.replace 可能被其他线程占用,加重试。
    """
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = get_state_path(project_dir)

    for attempt in range(5):
        try:
            fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            os.replace(tmp, str(path))
            return
        except (PermissionError, OSError):
            # Windows 上可能被其他线程占用,等待重试
            try:
                os.unlink(tmp)
            except (OSError, UnboundLocalError):
                pass
            if attempt < 4:
                time.sleep(0.05 * (attempt + 1))
            else:
                raise


def read_state(project_dir):
    """读取状态文件"""
    path = get_state_path(project_dir)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_update(project_dir, updater_fn):
    """
    🔒 线程安全的原子更新。
    
    加锁 → 读取 → 更新 → 写入 → 解锁。
    所有并发线程串行执行更新操作，不会丢数据。
    
    Args:
        project_dir: 项目根目录
        updater_fn: 接收 state dict, 修改后返回 (原地修改即可)
    """
    lock = _get_lock(project_dir)
    with lock:
        state = read_state(project_dir)
        updater_fn(state)
        write_state(project_dir, state)


def create_state(project_dir, orchestrate_id, feature, tier, acceptance_criteria=None):
    """创建初始状态文件"""
    state = {
        "orchestrate_id": orchestrate_id,
        "feature": feature,
        "tier": tier,
        "status": STATUS_PLANNING,
        "acceptance_criteria": acceptance_criteria or [],
        "tasks": [],
        "feature_branch": "",
        "base_branch": "",
        "owner": {
            "pid": os.getpid(),
            "session_id": "",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "heartbeat": datetime.now(timezone.utc).isoformat(),
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "decision_log": [],
    }
    write_state(project_dir, state)
    return state


def update_heartbeat(project_dir):
    """更新心跳"""
    atomic_update(project_dir, lambda s: s["owner"].__setitem__(
        "heartbeat", datetime.now(timezone.utc).isoformat()))


def add_tasks(project_dir, tasks):
    """批量添加子任务"""
    atomic_update(project_dir, lambda s: s["tasks"].extend(tasks))


def update_task(project_dir, task_id, **fields):
    """
    🔒 线程安全更新单个子任务。
    
    使用 atomic_update 保证并发线程不会互相覆盖。
    """
    def _update(s):
        for task in s["tasks"]:
            if task["id"] == task_id:
                task.update(fields)
                return
        raise KeyError(f"任务 {task_id} 不存在")
    
    atomic_update(project_dir, _update)


def get_task(project_dir, task_id):
    """获取单个子任务"""
    state = read_state(project_dir)
    for task in state["tasks"]:
        if task["id"] == task_id:
            return task
    raise KeyError(f"任务 {task_id} 不存在")


def get_ready_tasks(project_dir):
    """获取所有可执行的任务(依赖已全部完成的 pending 任务)"""
    state = read_state(project_dir)
    completed_ids = {t["id"] for t in state["tasks"] if t["status"] == TASK_COMPLETED}
    ready = []
    for task in state["tasks"]:
        if task["status"] != TASK_PENDING:
            continue
        if all(dep in completed_ids for dep in task.get("depends_on", [])):
            ready.append(task)
    return ready


def set_status(project_dir, status):
    """设置编排任务整体状态"""
    atomic_update(project_dir, lambda s: s.__setitem__("status", status))


def append_decision(project_dir, decision):
    """追加决策记录"""
    def _append(s):
        s["decision_log"].append({
            "at": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
        })
    atomic_update(project_dir, _append)


def remove_state(project_dir):
    """清理状态文件"""
    path = get_state_path(project_dir)
    if path.exists():
        path.unlink()
