"""
Cursor 半自动协作模块(机制⑤)

v1 因 Cursor CLI 限制,前端任务采用半自动:
暂停 → 提示用户切 Cursor → 检测 git commit → 续跑。
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import git_ops
import state_manager


# 轮询间隔(秒)
POLL_INTERVAL = 30
# 最大等待时间(秒,默认 30 分钟)
MAX_WAIT = 30 * 60


def dispatch_cursor_task(project_dir, task):
    """
    派发 Cursor 半自动任务。

    流程:
    1. 记录 git HEAD
    2. 更新状态为 in_progress
    3. 提示用户切 Cursor 完成并 commit
    4. 轮询检测 git commit(完成信号)
    5. 检测到 commit → 生成 handoff → 标记完成

    Returns:
        dict: {status, handoff}
    """
    # 1. 记录任务开始前的 git HEAD
    head_before = git_ops.get_head(project_dir)
    state_manager.update_task(project_dir, task["id"],
                              status=state_manager.TASK_IN_PROGRESS,
                              git_head_before=head_before)

    # 2. 提示用户
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  🟢 Cursor 半自动协作任务                                ║
╠══════════════════════════════════════════════════════════╣
║  子任务 {task['id']}: {task['name']}
║                                                          ║
║  请在 Cursor 中完成此任务:                               ║
║  1. 打开 Cursor                                          ║
║  2. 完成前端开发                                         ║
║  3. git commit 提交                                      ║
║                                                          ║
║  编排层将自动检测 commit 并继续后续任务。                ║
╚══════════════════════════════════════════════════════════╝
""")

    # 3. 轮询检测 git commit
    waited = 0
    while waited < MAX_WAIT:
        new_commits = git_ops.get_new_commits(project_dir, head_before)
        if new_commits:
            # 检测到 commit,任务完成
            head_after = new_commits[-1]
            print(f"✅ 检测到 Cursor 任务完成(commit: {head_after[:7]})")

            # 4. 生成 handoff 摘要(编排层根据 git diff 生成,Cursor 不输出 handoff)
            handoff = _generate_handoff_from_git(project_dir, head_before, head_after, task)

            # 5. 更新状态
            state_manager.update_task(project_dir, task["id"],
                                      status=state_manager.TASK_COMPLETED,
                                      git_commit_after=head_after,
                                      handoff=handoff,
                                      actual_model="cursor-sonnet")
            return {"status": "completed", "handoff": handoff}

        # 等待
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
        state_manager.update_heartbeat(project_dir)
        remaining = MAX_WAIT - waited
        if waited % (POLL_INTERVAL * 4) == 0:
            print(f"⏳ 等待 Cursor commit... (剩余 {remaining // 60} 分钟)")

    # 超时
    state_manager.update_task(project_dir, task["id"],
                              status=state_manager.TASK_FAILED)
    return {"status": "timeout", "error": f"等待 Cursor commit 超时({MAX_WAIT // 60}分钟)"}


def _generate_handoff_from_git(project_dir, head_before, head_after, task):
    """
    根据 git diff 生成 handoff 摘要(Cursor 不会自己输出 handoff)。

    扫描前端文件提取组件名。
    """
    changed = git_ops.get_changed_files(project_dir, head_before, head_after)

    # 提取前端组件名(.tsx/.vue/.jsx 文件)
    components = []
    for f in changed:
        if f.endswith((".tsx", ".jsx", ".vue")):
            # 文件名作为组件名(简化处理)
            import os
            components.append(os.path.basename(f).split(".")[0])

    return {
        "files_changed": changed,
        "new_interfaces": [
            {"type": "component", "name": c} for c in components
        ],
        "artifacts": f"前端任务已完成,改动 {len(changed)} 个文件",
        "git_commit": head_after,
        "next_task_hint": f"前端组件已就绪: {', '.join(components) if components else '见改动文件'}",
    }


def check_cursor_completion(project_dir, task_id):
    """
    非阻塞式检查 Cursor 任务是否完成(供编排层轮询调用)。

    不同于 dispatch_cursor_task 的内部轮询,这个是单次检查。
    """
    task = state_manager.get_task(project_dir, task_id)
    if task["status"] != state_manager.TASK_IN_PROGRESS:
        return {"status": task["status"]}

    head_before = task.get("git_head_before")
    if not head_before:
        return {"status": "error", "error": "无 git_head_before 记录"}

    new_commits = git_ops.get_new_commits(project_dir, head_before)
    if new_commits:
        return {"status": "completed", "commit": new_commits[-1]}
    return {"status": "waiting"}
