"""
ZCode CLI 调用模块(调度执行核心 · v3.0 支持 Worktree 并发)

负责通过 zcode.cjs --prompt 非交互调用 ZCode 执行子任务。
支持 worktree 隔离的并发编码模式。
含降级兜底触发(检测 429/quota → 切 DeepSeek)。
"""
import os
import re
import subprocess
import sys
import concurrent.futures
from pathlib import Path

# 将 scripts 目录加入路径以导入同模块
sys.path.insert(0, str(Path(__file__).parent))
import git_ops
import state_manager


# ZCode CLI 路径(实测路径 · 2026-06-27 验证通过)
ZCODE_CLI_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\ZCode\resources\glm\zcode.cjs"
)

# ZCode model 配置(从 ~/.zcode/v2/config.json 提取)
ZCODE_MODEL_MAIN = "4f14f683-2d01-4ee4-802f-51bdfc87cc5b/deepseek-v4-pro-260425"
ZCODE_PROVIDERS = {
    "4f14f683-2d01-4ee4-802f-51bdfc87cc5b": {
        "name": "Doubao",
        "kind": "openai-compatible",
        "options": {
            "apiKey": "38cd8e26-36b5-4a96-86a5-d1bd9cbbb695",
            "baseURL": "https://ark.cn-beijing.volces.com/api/v3"
        }
    },
    "e5037316-f958-4231-aa9e-8c7e3d8f2029": {
        "name": "DeepSeek",
        "kind": "openai-compatible",
        "options": {
            "apiKey": "sk-f9ee6ee73ae345c39c0c989c5fa81b53",
            "baseURL": "https://api.deepseek.com"
        }
    }
}

# 降级触发错误模式(匹配 stderr/stdout)
DEGRADATION_TRIGGERS = [
    "429", "quota_exceeded", "insufficient_quota",
    "model_overloaded", "rate_limit",
]


def ensure_zcode_config():
    """确保 ZCode config.json 包含正确的 model 和 provider 配置"""
    import json
    config_dir = Path.home() / ".zcode" / "cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"

    config = {
        "model": {"main": ZCODE_MODEL_MAIN},
        "provider": ZCODE_PROVIDERS,
    }

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                existing = json.load(f)
            if existing.get("model", {}).get("main") == ZCODE_MODEL_MAIN:
                return
        except (json.JSONDecodeError, OSError):
            pass

    with open(config_path, "w") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def build_prompt(task, project_dir, handoff_summaries=None):
    """
    构造子任务的 prompt(含 per-task 技能注入 + 上下文交接 + 文件边界约束)。

    Args:
        task: 子任务 dict(id/name/skills/files/prompt)
        project_dir: 项目根目录
        handoff_summaries: 前置任务的 handoff 摘要列表(机制⑥)
    """
    parts = [
        f"# 子任务 {task['id']}: {task['name']}",
        "",
        f"## ⚠️ 工作目录: `{project_dir}`",
        f"所有操作必须在此目录下进行。",
        "",
    ]

    # 文件边界约束(并发安全)
    task_files = task.get("files", [])
    if task_files:
        parts.append("## ⚠️ 文件操作边界(并发安全)")
        parts.append(f"你只能操作以下文件: {', '.join(task_files)}")
        parts.append("禁止修改其他文件,其他 Agent 正在并行操作不同的文件。")
        parts.append("")

    # 注入 per-task 技能
    task_skills = task.get("skills", [])
    if task_skills:
        parts.append("## 推荐加载的技能")
        for skill_name in task_skills:
            parts.append(f"- 加载技能: **{skill_name}**")
        parts.append("")

    # 注入前置任务的上下文交接(机制⑥)
    if handoff_summaries:
        parts.append("## 前置任务产出(上下文交接)")
        for hs in handoff_summaries:
            parts.append(f"【{hs['task_id']}】已完成")
            parts.append(f"- 修改文件: {', '.join(hs.get('files_changed', []))}")
            if hs.get("new_interfaces"):
                for iface in hs["new_interfaces"]:
                    parts.append(f"  • {iface.get('type','?')}: {iface.get('name','?')}")
            if hs.get("next_task_hint"):
                parts.append(f"- 提示: {hs['next_task_hint']}")
            parts.append("")

    parts.append("## 你的任务")
    parts.append(task.get("prompt", task.get("name", "")))
    parts.append("")
    parts.append("完成后请 git add + git commit，并输出结构化交接摘要(handoff JSON):")
    parts.append("```json")
    parts.append('{"files_changed": [...], "new_interfaces": [...], "artifacts": "..."}')
    parts.append("```")

    return "\n".join(parts)


def call_zcode(prompt, project_dir, mode="yolo", timeout=600):
    """
    调用 ZCode CLI 非交互执行。

    Returns:
        dict: {success, stdout, stderr, returncode, degraded, trigger}
    """
    ensure_zcode_config()

    cmd = [
        "node", ZCODE_CLI_PATH,
        "--prompt", prompt,
        "--cwd", str(project_dir),
        "--mode", mode,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir),
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
            "trigger": degraded,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": f"超时({timeout}s)", "returncode": -1}


def _detect_degradation(output):
    """检测输出中是否包含降级触发关键词"""
    output_lower = output.lower()
    for trigger in DEGRADATION_TRIGGERS:
        if trigger.lower() in output_lower:
            return trigger
    return None


# ═══════════════════════════════════════════════════════════
# 并发 Worktree 执行(方案C · 混合模式)
# ═══════════════════════════════════════════════════════════

def execute_task_in_worktree(project_dir, task, tier="L2"):
    """
    在隔离的 git worktree 中执行单个子任务。
    
    流程:
    1. 创建 worktree (基于 feature 分支)
    2. 在 worktree 中调用 ZCode
    3. 降级: ZCode 失败 → ZCode CLI 直连 → DeepSeek API
    4. 强制 commit + 回归保护
    5. 返回结果(合并由上层统一处理)
    """
    # 准备工作
    ensure_zcode_config()
    prompt = build_prompt(task, str(project_dir))
    head_before = git_ops.get_head(project_dir)
    
    state_manager.update_task(project_dir, task["id"],
                              status=state_manager.TASK_IN_PROGRESS,
                              git_head_before=head_before)
    
    # 创建 worktree
    try:
        worktree_dir = git_ops.create_worktree(project_dir, task["id"])
    except RuntimeError as e:
        return {"status": "failed", "error": f"创建 worktree 失败: {e}"}
    
    try:
        # Layer 1: ZCode + loop --auto (首选)
        result = call_zcode(prompt, worktree_dir, mode="yolo")
        
        degraded = False
        if not result["success"]:
            # 检测是否需要降级
            if result.get("degraded") or _is_quota_error(result.get("stderr", "")):
                degraded = True
                # Layer 2: ZCode CLI 直连(无 loop 门禁)
                result = call_zcode(prompt, worktree_dir, mode="yolo")
            
            if not result["success"]:
                # Layer 3: DeepSeek 兜底
                degraded = True
                from degradation_manager import execute_with_degradation
                deg_result = execute_with_degradation(
                    worktree_dir, task, prompt, mode="yolo"
                )
                if deg_result["status"] == "completed":
                    # DeepSeek 成功了
                    state_manager.update_task(project_dir, task["id"],
                                              status=state_manager.TASK_COMPLETED,
                                              degraded=True,
                                              degraded_reason="quota_exhausted",
                                              actual_model="deepseek-chat")
                    return {"status": "completed", "degraded": True}
                else:
                    result = {"success": False, "stderr": "所有降级层均已失败"}
        
        if not result["success"]:
            git_ops.reset_to(project_dir, head_before)
            state_manager.update_task(project_dir, task["id"],
                                      status=state_manager.TASK_FAILED)
            return {"status": "failed", "error": result.get("stderr", "未知错误")}
        
        # 🔴 强制 commit(解决 loop 不自动 commit 的 BUG)
        commit_sha = git_ops.force_commit(
            worktree_dir,
            f"go-{task['id']}: {task['name'][:50]}"
        )
        
        # 🔴 回归保护: 验证非预期文件变更
        if task.get("files"):
            actual_changes = git_ops.capture_change_snapshot(worktree_dir)
            verification = git_ops.verify_expected_changes(task["files"], actual_changes)
            if not verification["passed"]:
                state_manager.update_task(project_dir, task["id"],
                    status=state_manager.TASK_FAILED)
                return {
                    "status": "failed",
                    "error": f"非预期文件被修改: {verification['unexpected']}",
                    "regression_violation": True,
                }
        
        handoff = _parse_handoff(result["stdout"])
        state_manager.update_task(project_dir, task["id"],
                                  status=state_manager.TASK_COMPLETED,
                                  handoff=handoff,
                                  actual_model="deepseek-v4-pro",
                                  degraded=degraded,
                                  commit_sha=commit_sha)
        
        return {"status": "completed", "handoff": handoff, "degraded": degraded}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _is_quota_error(stderr):
    """检测是否为配额耗尽错误"""
    keywords = ["429", "quota_exceeded", "insufficient_quota", "rate_limit"]
    return any(kw in stderr.lower() for kw in keywords)


def execute_tasks_concurrent(project_dir, tasks, tier="L2"):
    """
    并发执行无依赖的子任务(Worktree 隔离模式)。
    
    在 feature 分支上创建 worktree,并发执行无依赖的子任务。
    执行完成后顺序合并回 feature 分支。
    
    Args:
        project_dir: 项目根目录(已在 feature 分支)
        tasks: 所有子任务列表
        tier: 执行级别
    """
    ensure_zcode_config()
    
    completed_ids = set()
    failed = []
    all_results = {}
    
    while True:
        # 找就绪任务(依赖全部完成)
        ready = [
            t for t in tasks
            if t.get("status") == state_manager.TASK_PENDING
            and all(dep in completed_ids for dep in t.get("depends_on", []))
        ]
        
        if not ready:
            pending = [t for t in tasks if t.get("status") == state_manager.TASK_PENDING]
            if pending:
                raise RuntimeError(f"依赖无法满足: {[t['id'] for t in pending]}")
            break
        
        if len(ready) == 1:
            # 单任务,直接执行
            task = ready[0]
            result = execute_task_in_worktree(project_dir, task, tier)
            all_results[task["id"]] = result
            
            if result.get("status") == "completed":
                completed_ids.add(task["id"])
                # 立即合并
                _merge_and_verify(project_dir, task["id"])
            else:
                failed.append(task["id"])
        else:
            # 多任务并发执行
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(ready)) as executor:
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
                        else:
                            failed.append(task_id)
                    except Exception as e:
                        failed.append(task_id)
            
            # 顺序合并(避免交叉冲突)
            for task in ready:
                if task["id"] in completed_ids:
                    merge_result = _merge_and_verify(project_dir, task["id"])
                    if not merge_result["ok"]:
                        failed.append(task["id"])
    
    all_done = len(completed_ids) + len(failed) == len(tasks)
    return {
        "all_completed": all_done and not failed,
        "failed_tasks": failed,
        "completed_count": len(completed_ids),
        "results": all_results,
    }


def _merge_and_verify(project_dir, task_id):
    """
    合并单个 worktree 到 feature 分支 + 安全闸门。
    
    返回: {"ok": bool, "auto_resolved": bool}
    """
    merge_result = git_ops.merge_worktree_to_feature(project_dir, task_id)
    
    if merge_result["conflict"]:
        # 尝试让 Agent 自动解决冲突
        conflict_files = merge_result["conflict_files"]
        resolved = _auto_resolve_conflicts(project_dir, conflict_files)
        if not resolved:
            return {"ok": False, "auto_resolved": False}
    
    # 安全闸: 跑测试
    tests_ok = git_ops.run_tests(project_dir)
    if not tests_ok:
        return {"ok": False, "auto_resolved": bool(merge_result["conflict"])}
    
    return {"ok": True, "auto_resolved": merge_result["conflict"]}


def _auto_resolve_conflicts(project_dir, conflict_files):
    """
    调用 ZCode Agent 自动解决 git merge 冲突。
    
    将冲突文件内容和冲突标记传给 Agent,让它整合双方改动。
    """
    if not conflict_files:
        return True
    
    files_info = []
    for f in conflict_files:
        filepath = Path(project_dir) / f
        if filepath.exists():
            content = filepath.read_text(encoding="utf-8", errors="ignore")
            files_info.append(f"### {f}\n```\n{content[:3000]}\n```")
    
    prompt = (
        f"当前在 git merge 中,以下文件有冲突(含 <<<<<<< HEAD 和 >>>>>>> 冲突标记):\n\n"
        + "\n\n".join(files_info)
        + "\n\n请解决所有冲突。要求:\n"
        "1. 移除所有冲突标记 (<<<<<<<, =======, >>>>>>>)\n"
        "2. 整合双方的改动,保留双方的意图\n"
        "3. 如果双方的改动无法兼容,优先保留 HEAD 的改动,在注释中标注 task-B 的改动\n"
        "4. 完成后执行 git add 标记冲突已解决(不要 commit)"
    )
    
    result = call_zcode(prompt, project_dir, mode="yolo", timeout=300)
    
    # 检查是否还有冲突
    remaining = git_ops.resolve_conflicts_with_agent(project_dir)
    return len(remaining) == 0


def _parse_handoff(stdout):
    """从 ZCode 输出中解析 handoff 摘要 JSON"""
    match = re.search(r"```json\s*(\{.*?\})\s*```", stdout, re.DOTALL)
    if not match:
        match = re.search(r'\{"files_changed".*?\}', stdout, re.DOTALL)
    if match:
        import json
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
