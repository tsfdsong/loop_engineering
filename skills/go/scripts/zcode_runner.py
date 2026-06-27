"""
ZCode CLI 调用模块(调度执行核心)

负责通过 zcode.cjs --prompt 非交互调用 ZCode 执行子任务。
含降级兜底触发(检测 429/quota → 切 DeepSeek)。
"""
import os
import re
import subprocess
import sys
from pathlib import Path

# 将 scripts 目录加入路径以导入同模块
sys.path.insert(0, str(Path(__file__).parent))
import git_ops
import state_manager


# ZCode CLI 路径(实测路径)
ZCODE_CLI_PATH = os.path.expandvars(
    r"%LOCALAPPDATA%\Programs\ZCode\resources\glm\zcode.cjs"
)

# 降级触发错误模式(匹配 stderr/stdout)
DEGRADATION_TRIGGERS = [
    "429",
    "quota_exceeded",
    "insufficient_quota",
    "model_overloaded",
    "rate_limit",
]

# 权限模式(按执行级别)
TIER_MODES = {
    "L1": "yolo",   # 直通档,全自动
    "L2": "yolo",   # 标准档
    "L3": "yolo",   # 完整档
}


def build_prompt(task, skill_content=None, handoff_summaries=None):
    """
    构造子任务的 prompt(含技能注入 + 上下文交接)。

    Args:
        task: 子任务 dict(id/name/assigned_tool)
        skill_content: 注入的 skill-hub 技能内容(机制②)
        handoff_summaries: 前置任务的 handoff 摘要列表(机制⑥)
    """
    parts = [f"# 子任务 {task['id']}: {task['name']}", ""]

    # 注入技能内容(机制②)
    if skill_content:
        parts.append("## 专家技能指引")
        parts.append("请遵循以下技能的最佳实践:")
        parts.append("")
        parts.append(skill_content)
        parts.append("")

    # 注入前置任务的上下文交接(机制⑥)
    if handoff_summaries:
        parts.append("## 前置任务产出(上下文交接)")
        parts.append("以下是已完成的前置任务摘要,供你参考:")
        parts.append("")
        for hs in handoff_summaries:
            parts.append(f"【{hs['task_id']}】已完成")
            parts.append(f"- 修改文件: {', '.join(hs.get('files_changed', []))}")
            if hs.get("new_interfaces"):
                parts.append("- 新增接口:")
                for iface in hs["new_interfaces"]:
                    parts.append(f"  • {iface.get('type','?')}: {iface.get('name','?')}")
            if hs.get("next_task_hint"):
                parts.append(f"- 提示: {hs['next_task_hint']}")
            parts.append("")

    parts.append("## 你的任务")
    parts.append("请完成上述子任务。完成后输出结构化交接摘要(handoff):")
    parts.append("```json")
    parts.append('{"files_changed": [...], "new_interfaces": [...], "artifacts": "...", "next_task_hint": "..."}')
    parts.append("```")

    return "\n".join(parts)


def call_zcode(prompt, project_dir, mode="yolo", timeout=600):
    """
    调用 ZCode CLI 非交互执行。

    Returns:
        dict: {success, stdout, stderr, returncode, degraded, trigger}
    """
    cmd = [
        "node",
        ZCODE_CLI_PATH,
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

        # 检测是否需要降级
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
        return {
            "success": False,
            "stdout": "",
            "stderr": f"超时({timeout}s)",
            "returncode": -1,
            "degraded": False,
            "trigger": "timeout",
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"ZCode CLI 不存在: {ZCODE_CLI_PATH}",
            "returncode": -1,
            "degraded": False,
            "trigger": "cli_missing",
        }


def _detect_degradation(output):
    """检测输出中是否包含降级触发关键词"""
    output_lower = output.lower()
    for trigger in DEGRADATION_TRIGGERS:
        if trigger.lower() in output_lower:
            return trigger
    return None


def execute_task(project_dir, task, tier="L2", skill_content=None):
    """
    执行单个子任务(完整流程含原子性保障)。

    流程:
    1. 记录 git_head_before(原子性回滚用)
    2. 构造 prompt(技能注入 + 上下文交接)
    3. 更新状态为 in_progress
    4. 调用 ZCode CLI
    5. 检测降级 → 触发 DeepSeek 兜底
    6. 完成 → 更新状态 + handoff 摘要
    """
    # 1. 记录任务开始前的 git HEAD(原子性保障)
    head_before = git_ops.get_head(project_dir)
    state_manager.update_task(project_dir, task["id"],
                              status=state_manager.TASK_IN_PROGRESS,
                              git_head_before=head_before)

    # 2. 收集前置任务的 handoff 摘要(机制⑥)
    handoff_summaries = []
    for dep_id in task.get("depends_on", []):
        dep_task = state_manager.get_task(project_dir, dep_id)
        if dep_task.get("handoff"):
            hs = dep_task["handoff"]
            hs["task_id"] = dep_id
            handoff_summaries.append(hs)

    # 3. 构造 prompt
    prompt = build_prompt(task, skill_content, handoff_summaries)

    # 4. 调用 ZCode CLI
    mode = TIER_MODES.get(tier, "yolo")
    result = call_zcode(prompt, project_dir, mode=mode)

    # 5. 降级检测
    if result["degraded"]:
        # 触发 DeepSeek 兜底(机制④,详见 degradation_manager)
        # 先回滚到任务开始前(保证干净状态)
        git_ops.reset_to(project_dir, head_before)
        # 标记降级(透明化标记)
        state_manager.update_task(project_dir, task["id"],
                                  degraded=True,
                                  degraded_reason=result["trigger"],
                                  original_model="glm-5.2")
        # 降级执行由 degradation_manager 接管
        return {
            "status": "degraded",
            "trigger": result["trigger"],
            "task_id": task["id"],
            "head_before": head_before,
        }

    # 6. 任务完成
    if result["success"]:
        head_after = git_ops.get_head(project_dir)
        # 解析 handoff 摘要(从 stdout 提取 JSON)
        handoff = _parse_handoff(result["stdout"])
        state_manager.update_task(project_dir, task["id"],
                                  status=state_manager.TASK_COMPLETED,
                                  git_commit_after=head_after,
                                  handoff=handoff,
                                  actual_model="glm-5.2")
        return {"status": "completed", "task_id": task["id"], "handoff": handoff}
    else:
        # 失败: 回滚到任务开始前
        git_ops.reset_to(project_dir, head_before)
        state_manager.update_task(project_dir, task["id"],
                                  status=state_manager.TASK_FAILED)
        return {"status": "failed", "task_id": task["id"], "error": result["stderr"]}


def _parse_handoff(stdout):
    """从 ZCode 输出中解析 handoff 摘要 JSON"""
    # 匹配 ```json ... ``` 代码块
    match = re.search(r"```json\s*(\{.*?\})\s*```", stdout, re.DOTALL)
    if not match:
        # 退而求其次: 匹配独立的 JSON 对象
        match = re.search(r'\{"files_changed".*?\}', stdout, re.DOTALL)
    if match:
        import json
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # 解析失败: 返回基础结构
    return {
        "files_changed": [],
        "new_interfaces": [],
        "artifacts": "handoff 解析失败,请人工检查 git diff",
        "next_task_hint": None,
    }
