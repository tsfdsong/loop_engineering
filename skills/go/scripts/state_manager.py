"""
编排层状态管理模块(机制④ · 双轨制状态文件)

负责 .orchestrate-state.json 的读写、原子写入、一致性校验。
所有调度逻辑的基础。
"""
import json
import os
import tempfile
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
    原子写入状态文件(检查点机制 · 机制③A)

    写临时文件 → os.replace 原子替换,防写一半中断损坏。
    """
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    path = get_state_path(project_dir)

    # 原子写入: 临时文件 → rename
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, str(path))  # 原子操作(Windows 兼容)
    except Exception:
        # 出错时清理临时文件
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_state(project_dir):
    """读取状态文件"""
    path = get_state_path(project_dir)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_state(project_dir, orchestrate_id, feature, tier, acceptance_criteria=None):
    """创建初始状态文件"""
    state = {
        "orchestrate_id": orchestrate_id,
        "feature": feature,
        "tier": tier,
        "status": STATUS_PLANNING,
        "acceptance_criteria": acceptance_criteria or [],
        "tasks": [],
        "feature_branch": "",  # feature 分支名(断点恢复用)
        "base_branch": "",     # 从哪个分支切出(回滚用)
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
    """更新心跳(并发检测用,借鉴 loop owner 设计)"""
    state = read_state(project_dir)
    state["owner"]["heartbeat"] = datetime.now(timezone.utc).isoformat()
    write_state(project_dir, state)


def add_tasks(project_dir, tasks):
    """批量添加子任务到状态文件"""
    state = read_state(project_dir)
    state["tasks"].extend(tasks)
    write_state(project_dir, state)


def update_task(project_dir, task_id, **fields):
    """更新单个子任务的状态字段"""
    state = read_state(project_dir)
    for task in state["tasks"]:
        if task["id"] == task_id:
            task.update(fields)
            break
    else:
        raise KeyError(f"任务 {task_id} 不存在")
    write_state(project_dir, state)


def get_task(project_dir, task_id):
    """获取单个子任务"""
    state = read_state(project_dir)
    for task in state["tasks"]:
        if task["id"] == task_id:
            return task
    raise KeyError(f"任务 {task_id} 不存在")


def get_pending_tasks(project_dir):
    """获取所有未完成的子任务(拓扑序)"""
    state = read_state(project_dir)
    return [t for t in state["tasks"] if t["status"] in (TASK_PENDING, TASK_IN_PROGRESS, TASK_FAILED)]


def get_ready_tasks(project_dir):
    """
    获取所有可执行的任务(依赖已全部完成的 pending 任务)。
    无依赖任务可并发(机制① L3 多智能体并行)。
    """
    state = read_state(project_dir)
    completed_ids = {t["id"] for t in state["tasks"] if t["status"] == TASK_COMPLETED}
    ready = []
    for task in state["tasks"]:
        if task["status"] != TASK_PENDING:
            continue
        # 检查所有依赖是否已完成
        if all(dep in completed_ids for dep in task.get("depends_on", [])):
            ready.append(task)
    return ready


def set_status(project_dir, status):
    """设置编排任务整体状态"""
    state = read_state(project_dir)
    state["status"] = status
    write_state(project_dir, state)


def append_decision(project_dir, decision):
    """追加决策记录(可追溯)"""
    state = read_state(project_dir)
    state["decision_log"].append({
        "at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
    })
    write_state(project_dir, state)


def remove_state(project_dir):
    """清理状态文件(任务完成后)"""
    path = get_state_path(project_dir)
    if path.exists():
        path.unlink()
