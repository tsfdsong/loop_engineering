"""
编排层主调度器

串联所有模块: L0评估 → 状态初始化 → 任务拆分 → 技能注入 →
拓扑调度执行(ZCode/Cursor) → 降级兜底 → 上下文交接 → 全局回归。
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import complexity_evaluator
import state_manager
import git_ops
import zcode_runner
import cursor_collaboration


def orchestrate(feature, project_dir, acceptance_criteria=None, explicit_flag=None):
    """
    编排层主入口。

    Args:
        feature: 功能描述
        project_dir: 项目根目录
        acceptance_criteria: 验收条件列表
        explicit_flag: 'fast'/'full'/None

    Returns:
        dict: 编排结果
    """
    project_dir = Path(project_dir)
    print(f"🧠 /orchestrate 启动: {feature}")

    # Step ⓪: 断点续跑检测
    if state_manager.state_exists(project_dir):
        result = _handle_breakpoint(project_dir)
        if result["action"] == "resume":
            return _resume_orchestration(project_dir)
        elif result["action"] == "abort":
            return {"status": "aborted", "reason": "用户选择放弃"}

    # Step ①: L0 复杂度评估(纯规则,零token)
    eval_result = complexity_evaluator.evaluate_complexity(feature, explicit_flag)
    tier = eval_result["tier"]
    print(f"📊 L0 评估: {tier} ({eval_result['reason']})")

    # Step ②: 状态初始化
    orchestrate_id = f"orch/{_slugify(feature)}-{datetime.now().strftime('%m%d')}"
    criteria = acceptance_criteria or []
    state = state_manager.create_state(
        project_dir, orchestrate_id, feature, tier, criteria
    )
    state_manager.set_status(project_dir, state_manager.STATUS_IN_PROGRESS)

    # 🔒 硬闸门(实际执行时由 SKILL.md 流程拦截,这里模拟确认)
    print(f"\n🔒 硬闸门确认")
    print(f"   评估级别: {tier}")
    print(f"   验收条件: {len(criteria)} 条")
    for i, c in enumerate(criteria, 1):
        print(f"   [{i}] {c}")
    # 注: 实际由 ZCode 会话的 SKILL.md 流程处理用户确认

    # Step ③: 任务拆分(简化版,实际由 SKILL.md 指导拆分)
    tasks = _split_tasks(feature, tier)
    state_manager.add_tasks(project_dir, tasks)

    # Step ④⑤: 调度执行
    result = _execute_tasks(project_dir, tier)

    if result["all_completed"]:
        # Step ⑦: 全局集成回归
        regression_ok = _global_regression(project_dir)
        if regression_ok:
            # Step ⑧: 交付
            state_manager.set_status(project_dir, state_manager.STATUS_COMPLETED)
            print(f"\n✅ 编排完成: {feature}")
            state_manager.remove_state(project_dir)
            return {"status": "completed", "feature": feature}
        else:
            state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
            return {"status": "regression_failed"}
    else:
        state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
        return {"status": "tasks_failed", "failed": result.get("failed_tasks", [])}


def _handle_breakpoint(project_dir):
    """Step⓪: 断点续跑检测"""
    state = state_manager.read_state(project_dir)
    updated = state.get("updated_at", "")
    completed = sum(1 for t in state["tasks"] if t["status"] == "completed")
    total = len(state["tasks"])
    print(f"\n📌 检测到未完成的编排任务: {state['feature']}")
    print(f"   进度: {completed}/{total} 子任务完成")
    print(f"   最后更新: {updated}")
    # 注: 实际由 SKILL.md 流程询问用户
    return {"action": "resume"}


def _resume_orchestration(project_dir):
    """断点续跑: 从断点继续"""
    state = state_manager.read_state(project_dir)
    tier = state["tier"]
    print(f"▶️ 续跑: {state['feature']}")
    return _execute_tasks(project_dir, tier)


def _split_tasks(feature, tier):
    """Step③: 任务拆分(简化版)"""
    if tier == "L1":
        # L1 不拆,单任务
        return [{
            "id": "T1",
            "name": feature,
            "assigned_tool": "zcode",
            "depends_on": [],
            "status": state_manager.TASK_PENDING,
            "skill_injected": None,
            "git_head_before": None,
            "git_commit_after": None,
            "handoff": None,
            "degraded": False,
            "degraded_reason": None,
            "original_model": None,
            "actual_model": None,
        }]

    # L2/L3: 实际拆分由 SKILL.md 指导(这里给骨架)
    # 注: 真实场景由 ZCode 会话中的 writing-plans 完成
    return [{
        "id": f"T{i+1}",
        "name": f"子任务{i+1}(待SKILL.md细化)",
        "assigned_tool": "zcode",
        "depends_on": [] if i == 0 else [f"T{i}"],
        "status": state_manager.TASK_PENDING,
        "skill_injected": None,
        "git_head_before": None,
        "git_commit_after": None,
        "handoff": None,
        "degraded": False,
        "degraded_reason": None,
        "original_model": None,
        "actual_model": None,
    } for i in range(1 if tier == "L2" else 3)]


def _execute_tasks(project_dir, tier):
    """Step⑤: 按拓扑序调度执行"""
    state = state_manager.read_state(project_dir)
    failed = []

    while True:
        ready = state_manager.get_ready_tasks(project_dir)
        if not ready:
            break

        for task in ready:
            print(f"\n▶️ 执行 {task['id']}: {task['name']}")

            # 检查前置 handoff(机制⑥)
            handoff_summaries = []
            for dep_id in task.get("depends_on", []):
                dep = state_manager.get_task(project_dir, dep_id)
                if dep.get("handoff"):
                    hs = dep["handoff"]
                    hs["task_id"] = dep_id
                    handoff_summaries.append(hs)

            tool = task.get("assigned_tool", "zcode")

            if tool == "cursor":
                # Cursor 半自动协作(机制⑤)
                result = cursor_collaboration.dispatch_cursor_task(project_dir, task)
            elif tool == "trae":
                # Trae 半自动(简化: 标记跳过,待用户手动)
                state_manager.update_task(project_dir, task["id"],
                                          status=state_manager.TASK_SKIPPED)
                print(f"⏭️ Trae 任务 {task['id']} 标记为手动审查")
                continue
            else:
                # ZCode CLI 自动执行(含降级兜底)
                prompt = zcode_runner.build_prompt(task, None, handoff_summaries)
                result = zcode_runner.execute_task(project_dir, task, tier)

                # 降级处理
                if result.get("status") == "degraded":
                    print(f"⚠️ 任务 {task['id']} 触发降级({result['trigger']}),切 DeepSeek")
                    from degradation_manager import execute_with_degradation
                    deg_result = execute_with_degradation(
                        project_dir, task, prompt,
                        mode=zcode_runner.TIER_MODES.get(tier, "yolo")
                    )
                    if deg_result["status"] == "completed":
                        head_after = git_ops.get_head(project_dir)
                        handoff = zcode_runner._parse_handoff(deg_result["stdout"])
                        state_manager.update_task(project_dir, task["id"],
                                                  status=state_manager.TASK_COMPLETED,
                                                  git_commit_after=head_after,
                                                  handoff=handoff,
                                                  actual_model="deepseek-chat")
                        result = {"status": "completed"}
                    else:
                        result = {"status": "failed"}

            if result.get("status") == "failed":
                failed.append(task["id"])
                print(f"❌ 任务 {task['id']} 失败: {result.get('error', '未知')}")

    state = state_manager.read_state(project_dir)
    all_done = all(t["status"] in (state_manager.TASK_COMPLETED, state_manager.TASK_SKIPPED)
                   for t in state["tasks"])
    return {"all_completed": all_done, "failed_tasks": failed}


def _global_regression(project_dir):
    """Step⑦: 全局集成回归(复用 loop 门禁)"""
    print("\n🌐 全局集成回归...")
    # 注: 实际由 SKILL.md 调用 loop 的门禁矩阵 G1-G8 + F1-F5
    # 这里检查是否有测试可跑
    project_dir = Path(project_dir)
    if (project_dir / "pytest.ini").exists() or (project_dir / "pyproject.toml").exists():
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-q"],
            cwd=str(project_dir), capture_output=True, text=True, encoding="utf-8"
        )
        if result.returncode == 0:
            print("✅ 全量测试通过")
            return True
        else:
            print(f"❌ 全量测试失败:\n{result.stdout[-500:]}")
            return False
    print("ℹ️ 未找到测试配置,跳过测试回归")
    return True


def _slugify(text):
    """生成 URL 友好的 slug"""
    import re
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return text[:20] if text else "task"


if __name__ == "__main__":
    # 命令行入口
    if len(sys.argv) < 2:
        print("用法: python orchestrator.py <功能描述> [项目目录] [--fast|--full]")
        sys.exit(1)

    feature = sys.argv[1]
    project = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else os.getcwd()
    flag = None
    if "--fast" in sys.argv:
        flag = "fast"
    elif "--full" in sys.argv:
        flag = "full"

    result = orchestrate(feature, project, explicit_flag=flag)
    print(f"\n📋 结果: {result}")
