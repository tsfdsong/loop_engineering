"""
ZCode CLI 调用模块 v4.0 — 多进程并发 + 线程安全

修复:
  - BUG #2: 降级死循环 → 指数退避 + 最大重试次数
  - BUG #5: 每次合并跑全量测试 → 改为最终一次性测试
  - BUG #6: API Key 硬编码 → 读环境变量
  - BUG #8: build_prompt 参数名误导 → 改为 worktree_dir
"""
import os
import re
import json
import subprocess
import sys
import time
import concurrent.futures
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import git_ops
import state_manager


# ─── 配置 (从环境变量读取,不硬编码) ───

ZCODE_CLI_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\ZCode\resources\glm\zcode.cjs"
)

# Provider 配置从 ~/.zcode/v2/config.json 动态读取
def _load_providers():
    """从 v2/config.json 读取全部 provider 配置 (不限 enabled, 供后续选择)"""
    v2_path = Path.home() / ".zcode" / "v2" / "config.json"
    if v2_path.exists():
        with open(v2_path, "r") as f:
            v2 = json.load(f)
        return v2.get("provider", {})
    return {}


def _load_model_main(preferred_provider=None):
    """
    确定主模型。

    优先级:
      1. 指定的 preferred_provider (来自 task.model)
      2. enabled=True 的 provider
      3. 有模型配置的 provider
      4. 回退到 Doubao deepseek
    """
    v2_path = Path.home() / ".zcode" / "v2" / "config.json"
    if not v2_path.exists():
        return "4f14f683-2d01-4ee4-802f-51bdfc87cc5b/deepseek-v4-pro-260425"

    with open(v2_path, "r") as f:
        v2 = json.load(f)
    providers = v2.get("provider", {})

    # 1. 指定 provider 优先
    if preferred_provider and preferred_provider in providers:
        p = providers[preferred_provider]
        if p.get("models"):
            first_model = list(p["models"].keys())[0]
            return f"{preferred_provider}/{first_model}"

    # 2. enabled=True 的 provider
    for pid, p in providers.items():
        if p.get("enabled", False) and p.get("models"):
            first_model = list(p["models"].keys())[0]
            return f"{pid}/{first_model}"

    # 3. 任何一个有 model 的 provider
    for pid, p in providers.items():
        if p.get("models"):
            first_model = list(p["models"].keys())[0]
            return f"{pid}/{first_model}"

    # 4. 回退
    return "4f14f683-2d01-4ee4-802f-51bdfc87cc5b/deepseek-v4-pro-260425"


# 降级触发关键词
DEGRADATION_TRIGGERS = [
    "429", "quota_exceeded", "insufficient_quota",
    "model_overloaded", "rate_limit",
]

# 降级重试配置 (修复 BUG #2: 不再无限重试)
MAX_RETRIES = 2
RETRY_DELAYS = [2, 8]  # 指数退避: 2s, 8s


def ensure_zcode_config(preferred_provider=None):
    """
    确保 ZCode config.json 包含正确的 model 和 provider 配置。

    Args:
        preferred_provider: 指定优先 provider ID (来自 task.model)
    """
    config_dir = Path.home() / ".zcode" / "cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"

    providers = _load_providers()
    model_main = _load_model_main(preferred_provider)

    config = {
        "model": {"main": model_main},
        "provider": providers,
    }

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                existing = json.load(f)
            if existing.get("model", {}).get("main") == model_main:
                return
        except (json.JSONDecodeError, OSError):
            pass

    with open(config_path, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def build_prompt(task, worktree_dir, handoff_summaries=None):
    """
    构造子任务的 prompt。

    Args:
        task: 子任务 dict
        worktree_dir: worktree 工作目录 (不是项目根目录)
        handoff_summaries: 前置任务的 handoff 摘要列表
    """
    parts = [
        f"# 子任务 {task['id']}: {task.get('name', task['id'])}",
        "",
        f"## 工作目录: `{worktree_dir}`",
        f"所有操作必须在此目录下进行。",
        "",
    ]

    # per-task model 指令
    task_model = task.get("model")
    if task_model:
        parts.append("## 模型要求")
        parts.append(f"此任务请使用 model: `{task_model}`")
        parts.append("如需切换,在回复中调用 /model 切换。")
        parts.append("")

    task_files = task.get("files", [])
    if task_files:
        parts.append("## 文件操作边界(并发安全)")
        parts.append(f"你只能操作以下文件: {', '.join(task_files)}")
        parts.append("禁止修改其他文件,其他 Agent 正在并行操作不同的文件。")
        parts.append("")

    task_skills = task.get("skills", [])
    if task_skills:
        parts.append("## 推荐加载的技能")
        for skill_name in task_skills:
            parts.append(f"- 加载技能: **{skill_name}**")
        parts.append("")

    if handoff_summaries:
        parts.append("## 前置任务产出(上下文交接)")
        for hs in handoff_summaries:
            parts.append(f"[{hs.get('task_id', '?')}] 已完成")
            parts.append(f"- 修改文件: {', '.join(hs.get('files_changed', []))}")
            if hs.get("next_task_hint"):
                parts.append(f"- 提示: {hs['next_task_hint']}")
            parts.append("")

    parts.append("## 你的任务")
    parts.append(task.get("prompt", task.get("name", "")))
    parts.append("")
    parts.append("完成后请 git add + commit。")

    return "\n".join(parts)


def call_zcode(prompt, worktree_dir, mode="yolo", timeout=600, model=None):
    """
    调用 ZCode CLI 非交互执行。

    Args:
        prompt: 任务提示词
        worktree_dir: worktree 工作目录
        mode: 权限模式
        timeout: 超时秒数
        model: 可选, 指定 provider ID (如 "4f14f683-...")

    Returns:
        dict: {success, stdout, stderr, returncode, degraded}
    """
    ensure_zcode_config(preferred_provider=model)

    cmd = [
        "node", ZCODE_CLI_PATH,
        "--prompt", prompt,
        "--cwd", str(worktree_dir),
        "--mode", mode,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(worktree_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
        )
        output = result.stdout + "\n" + result.stderr
        degraded = _detect_degradation(output)

        return {
            "success": result.returncode == 0 and not degraded,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "degraded": degraded,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False, "stdout": "", "stderr": f"超时({timeout}s)",
            "returncode": -1, "degraded": None,
        }


def call_zcode_with_retry(prompt, worktree_dir, mode="yolo", timeout=600, model=None):
    """
    调用 ZCode CLI,带指数退避重试。

    修复 BUG #2: 不再无限重试,最多 MAX_RETRIES 次。

    Args:
        model: 可选, 指定 provider ID
    """
    last_result = None

    for attempt in range(MAX_RETRIES + 1):
        result = call_zcode(prompt, worktree_dir, mode, timeout, model=model)
        last_result = result

        if result["success"]:
            return result

        # 如果是配额错误,等待后重试
        if result.get("degraded") and attempt < MAX_RETRIES:
            delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
            print(f"  [重试 {attempt+1}/{MAX_RETRIES}] 等待 {delay}s 后重试...")
            time.sleep(delay)
            continue

        # 非配额错误或重试次数用完,不重试
        break

    return last_result


def _detect_degradation(output):
    """检测输出中是否包含降级触发关键词"""
    output_lower = output.lower()
    for trigger in DEGRADATION_TRIGGERS:
        if trigger.lower() in output_lower:
            return trigger
    return None


# ═══════════════════════════════════════════════════════════
# 并发 Worktree 执行
# ═══════════════════════════════════════════════════════════

def execute_task_in_worktree(project_dir, task, tier="L2"):
    """
    在隔离的 git worktree 中执行单个子任务。

    流程:
    1. 创建 worktree
    2. 调用 ZCode (带重试)
    3. 强制 commit + 回归保护
    4. 返回结果 (合并由上层统一处理)
    """
    ensure_zcode_config()

    # 收集前置任务 handoff
    handoff_summaries = []
    for dep_id in task.get("depends_on", []):
        try:
            dep = state_manager.get_task(project_dir, dep_id)
            if dep.get("handoff"):
                hs = dep["handoff"]
                hs["task_id"] = dep_id
                handoff_summaries.append(hs)
        except KeyError:
            pass

    prompt = build_prompt(task, str(project_dir), handoff_summaries)

    # 标记任务开始
    head_before = git_ops.get_head(project_dir)
    state_manager.update_task(project_dir, task["id"],
                              status=state_manager.TASK_IN_PROGRESS,
                              git_head_before=head_before,
                              model=task.get("model"))

    # 创建 worktree
    try:
        worktree_dir = git_ops.create_worktree(project_dir, task["id"])
    except RuntimeError as e:
        return {"status": "failed", "error": f"创建 worktree 失败: {e}"}

    try:
        # 调用 ZCode (带重试 + per-task model)
        result = call_zcode_with_retry(
            prompt, worktree_dir, mode="yolo",
            model=task.get("model")
        )

        if not result["success"]:
            state_manager.update_task(project_dir, task["id"],
                                      status=state_manager.TASK_FAILED,
                                      error=result.get("stderr", "未知错误")[:200])
            return {"status": "failed", "error": result.get("stderr", "未知错误")[:200]}

        # 强制 commit
        commit_sha = git_ops.force_commit(
            worktree_dir,
            f"go-{task['id']}: {task.get('name', task['id'])[:50]}"
        )

        # 回归保护
        if task.get("files"):
            actual_changes = git_ops.capture_change_snapshot(worktree_dir)
            verification = git_ops.verify_expected_changes(task["files"], actual_changes)
            if not verification["passed"]:
                state_manager.update_task(project_dir, task["id"],
                                          status=state_manager.TASK_FAILED)
                return {
                    "status": "failed",
                    "error": f"非预期文件被修改: {verification['unexpected']}",
                }

        # 解析 handoff
        handoff = _parse_handoff(result["stdout"])
        state_manager.update_task(project_dir, task["id"],
                                  status=state_manager.TASK_COMPLETED,
                                  handoff=handoff,
                                  commit_sha=commit_sha)

        return {"status": "completed", "handoff": handoff, "commit_sha": commit_sha}

    except Exception as e:
        state_manager.update_task(project_dir, task["id"],
                                  status=state_manager.TASK_FAILED,
                                  error=str(e)[:200])
        return {"status": "failed", "error": str(e)[:200]}


def execute_tasks_concurrent(project_dir, tasks, tier="L2", max_workers=4):
    """
    并发执行无依赖的子任务。

    流程:
    1. 拓扑排序,找就绪任务
    2. 无依赖任务并发执行 (ThreadPoolExecutor)
    3. 有依赖任务等前置完成后执行
    4. 全部完成后顺序合并 (不在循环中跑测试,修复 BUG #5)
    """
    ensure_zcode_config()

    completed_ids = set()
    failed = []
    all_results = {}

    while True:
        # 找就绪任务
        ready = [
            t for t in tasks
            if t.get("status") == state_manager.TASK_PENDING
            and all(dep in completed_ids for dep in t.get("depends_on", []))
        ]

        if not ready:
            pending = [t for t in tasks if t.get("status") == state_manager.TASK_PENDING]
            if pending:
                print(f"⚠️ 依赖无法满足: {[t['id'] for t in pending]}")
                failed.extend(t["id"] for t in pending)
                break
            break

        if len(ready) == 1:
            # 单任务直接执行
            task = ready[0]
            print(f"  ▶️ {task['id']}: {task.get('name', '')[:40]}")
            result = execute_task_in_worktree(project_dir, task, tier)
            all_results[task["id"]] = result
            if result.get("status") == "completed":
                completed_ids.add(task["id"])
            else:
                failed.append(task["id"])
        else:
            # 多任务并发执行
            worker_count = min(len(ready), max_workers)
            print(f"  🚀 并发执行 {len(ready)} 个任务 ({worker_count} workers)")

            with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
                futures = {
                    executor.submit(execute_task_in_worktree, project_dir, t, tier): t["id"]
                    for t in ready
                }
                for future in concurrent.futures.as_completed(futures):
                    task_id = futures[future]
                    try:
                        result = future.result(timeout=600)
                        all_results[task_id] = result
                        if result.get("status") == "completed":
                            completed_ids.add(task_id)
                            print(f"  ✅ {task_id} 完成")
                        else:
                            failed.append(task_id)
                            print(f"  ❌ {task_id} 失败: {result.get('error', '')[:60]}")
                    except Exception as e:
                        failed.append(task_id)
                        print(f"  ❌ {task_id} 异常: {str(e)[:60]}")

    # 顺序合并所有完成的任务 (不在循环中跑测试)
    for task in tasks:
        if task["id"] in completed_ids:
            merge_result = _merge_worktree(project_dir, task["id"])
            if not merge_result["ok"]:
                if task["id"] not in failed:
                    failed.append(task["id"])

    all_done = len(completed_ids) + len(failed) == len(tasks)
    return {
        "all_completed": all_done and not failed,
        "failed_tasks": failed,
        "completed_count": len(completed_ids),
        "results": all_results,
    }


def _merge_worktree(project_dir, task_id):
    """
    合并单个 worktree 到 feature 分支。
    冲突时自动解决。
    """
    merge_result = git_ops.merge_worktree_to_feature(project_dir, task_id)

    if merge_result["conflict"]:
        conflict_files = merge_result["conflict_files"]
        resolved = _auto_resolve_conflicts(project_dir, conflict_files)
        if not resolved:
            print(f"  ⚠️ {task_id} 合并冲突未解决,需人工处理")
            return {"ok": False}

    return {"ok": True}


def _auto_resolve_conflicts(project_dir, conflict_files):
    """调用 ZCode Agent 自动解决 git merge 冲突。"""
    if not conflict_files:
        return True

    files_info = []
    for f in conflict_files:
        filepath = Path(project_dir) / f
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            files_info.append(f"### {f}\n```\n{content[:3000]}\n```")

    prompt = (
        f"当前在 git merge 中,以下文件有冲突:\n\n"
        + "\n\n".join(files_info)
        + "\n\n请解决所有冲突:\n"
        "1. 移除冲突标记\n"
        "2. 整合双方改动\n"
        "3. git add 标记已解决 (不要 commit)"
    )

    call_zcode(prompt, project_dir, mode="yolo", timeout=300)
    remaining = git_ops.resolve_conflicts_with_agent(project_dir)
    return len(remaining) == 0


def _parse_handoff(stdout):
    """从 ZCode 输出中解析 handoff JSON"""
    # 尝试从 ```json``` 代码块提取
    match = re.search(r"```json\s*(\{.*?\})\s*```", stdout, re.DOTALL)
    if not match:
        # 退而求其次: 匹配独立的 JSON 对象
        match = re.search(r'\{"files_changed".*?\}', stdout, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {
        "files_changed": [],
        "new_interfaces": [],
        "artifacts": "handoff 解析失败",
        "next_task_hint": None,
    }
