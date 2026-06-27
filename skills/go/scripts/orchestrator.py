"""
编排层主调度器 v3.1 — Feature Branch + Worktree 并发

流程:
  0. 🔴 硬约束: 禁止保护分支上有未提交改动
  1. 创建 feature 分支 (保护 main/master/test)
  2. ZCode 智能拆分 → 真并发的子任务 DAG
  3. Worktree 并发执行 (无依赖并行 + 有依赖串行)
  4. 顺序合并回 feature 分支 (冲突自动解决)
  5. 安全闸: 跑测试
  6. 交付: 可合并到 main
"""
import os
import sys
import json
import time
import re
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import complexity_evaluator
import state_manager
import git_ops
import zcode_runner


def orchestrate(feature, project_dir, acceptance_criteria=None, explicit_flag=None):
    """
    编排层主入口 v3.1。

    Args:
        feature: 功能描述
        project_dir: 项目根目录
        acceptance_criteria: 验收条件列表
        explicit_flag: 'fast'/'full'/None
    """
    project_dir = Path(project_dir)
    print(f"\n{'='*60}")
    print(f"🧠 /go {feature}")
    print(f"{'='*60}")

    # Step ⓪: 断点续跑检测
    if state_manager.state_exists(project_dir):
        return _resume_orchestration(project_dir)

    # Step ⓪.5: 🔴 硬约束 — 保护分支检查
    git_ops.validate_not_protected(project_dir)

    # Step ①: L0 复杂度评估
    eval_result = complexity_evaluator.evaluate_complexity(feature, explicit_flag)
    tier = eval_result["tier"]
    print(f"📊 复杂度: {tier} ({eval_result['reason']})")

    # Step ①.5: 创建 feature 分支(保护 main/master/test)
    feature_slug = _slugify(feature)
    current_before = git_ops.get_current_branch(project_dir)
    branch = git_ops.create_feature_branch(project_dir, feature_slug)
    print(f"🌿 Feature 分支: {branch} (从 {current_before} 切出)")

    # Step ②: 状态初始化
    orch_id = f"go/{feature_slug}-{datetime.now().strftime('%m%d%H%M')}"
    state_manager.create_state(project_dir, orch_id, feature, tier, acceptance_criteria)
    
    # 记录分支信息(断点恢复用)
    state_manager.write_state(project_dir, {
        **state_manager.read_state(project_dir),
        "feature_branch": branch,
        "base_branch": current_before,
    })
    state_manager.set_status(project_dir, state_manager.STATUS_IN_PROGRESS)

    # Step ③: ZCode 智能拆分
    tasks = _split_tasks_with_zcode(feature, project_dir, tier)
    state_manager.add_tasks(project_dir, tasks)
    
    # 统计并发潜力
    no_dep = sum(1 for t in tasks if not t.get("depends_on"))
    print(f"📋 拆分为 {len(tasks)} 个子任务, {no_dep} 个可并发")

    # Step ④⑤: Worktree 并发执行
    result = zcode_runner.execute_tasks_concurrent(project_dir, tasks, tier)

    if result["all_completed"]:
        # Step ⑦: 安全闸 — 跑测试
        print(f"\n🧪 安全闸: 运行测试...")
        tests_ok = git_ops.run_tests(project_dir)
        if tests_ok:
            print(f"✅ 测试通过")
            state_manager.set_status(project_dir, state_manager.STATUS_COMPLETED)
            print(f"\n🎉 完成! Feature 分支 `{branch}` 已就绪,可合并到 main:")
            print(f"   git checkout main && git merge {branch}")
            state_manager.remove_state(project_dir)
            return {"status": "completed", "branch": branch, "tasks": len(tasks)}
        else:
            print(f"❌ 测试失败! Feature 分支保留,请人工检查")
            state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
            return {"status": "test_failed", "branch": branch}
    else:
        state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
        return {"status": "tasks_failed", "failed": result.get("failed_tasks", [])}


def _split_tasks_with_zcode(feature, project_dir, tier):
    """
    Step ③: 让 ZCode Agent 分析功能需求,拆分成真正可并发的子任务。

    每个子任务包含:
    - 清晰的文件/模块边界 → 并发安全的保证
    - 依赖关系 → 拓扑排序
    - 推荐技能 → 领域最佳实践
    - 验收条件 → 可验证性
    """
    if tier == "L1":
        # L1 不需要拆分
        return [{
            "id": "T1", "name": feature,
            "assigned_tool": "zcode", "depends_on": [],
            "prompt": feature, "skills": [],
            "status": state_manager.TASK_PENDING,
        }]

    # L2/L3: ZCode 智能拆分
    split_prompt = f"""分析以下功能需求,拆分成可并发的编码子任务:

功能: "{feature}"

项目目录: {project_dir}

输出 JSON 格式(只输出 JSON,不要其他文字):
```json
{{"tasks": [
  {{
    "id": "T1",
    "name": "子任务名称(中文,10字内)",
    "prompt": "具体的执行指令(含验收条件)",
    "depends_on": [],
    "skills": ["需要的技能名"],
    "files": ["预期操作的文件路径"]
  }}
]}}
```

拆分规则:
1. 识别可并发执行的子任务(操作不同文件) → depends_on 为空
2. 标注有依赖关系的子任务 → depends_on 列出前置任务 ID
3. 每个子任务的 files 边界不能重叠(保证并发安全)
4. 每个子任务推荐需要的技能(skill-hub 中的技能名)
5. {"L2 级别拆分 2-3 个子任务" if tier == "L2" else "L3 级别拆分 3-5 个子任务,粒度更细"}"""

    # 调用 ZCode 做拆分
    result = zcode_runner.call_zcode(split_prompt, project_dir, mode="yolo", timeout=120)
    
    tasks = _parse_tasks_json(result.get("stdout", ""))
    
    if not tasks:
        # 回退: L2/L3 骨架拆分
        return _fallback_split(feature, tier)
    
    # 标准化
    for task in tasks:
        task.setdefault("assigned_tool", "zcode")
        task.setdefault("status", state_manager.TASK_PENDING)
        task.setdefault("skills", [])
        task.setdefault("files", [])
    
    return tasks


def _parse_tasks_json(stdout):
    """从 ZCode 输出中解析任务列表 JSON"""
    match = re.search(r'"tasks"\s*:\s*\[.*?\]', stdout, re.DOTALL)
    if not match:
        match = re.search(r'\{[^{]*"tasks"\s*:\s*\[.*?\]\s*\}', stdout, re.DOTALL)
    if match:
        try:
            data = json.loads("{" + match.group(0))
            return data.get("tasks", [])
        except json.JSONDecodeError:
            pass
    return []


def _fallback_split(feature, tier):
    """当 ZCode 拆分失败时的骨架回退"""
    count = 2 if tier == "L2" else 3
    return [{
        "id": f"T{i+1}",
        "name": f"子任务 {i+1}",
        "assigned_tool": "zcode",
        "depends_on": [] if i == 0 else [f"T{i}"],
        "prompt": f"子任务 {i+1}: {feature}",
        "skills": [],
        "files": [],
        "status": state_manager.TASK_PENDING,
    } for i in range(count)]


def _resume_orchestration(project_dir):
    """断点续跑"""
    state = state_manager.read_state(project_dir)
    tier = state["tier"]
    print(f"▶️ 续跑: {state['feature']}")

    tasks = state["tasks"]
    result = zcode_runner.execute_tasks_concurrent(project_dir, tasks, tier)

    if result["all_completed"]:
        tests_ok = git_ops.run_tests(project_dir)
        if tests_ok:
            state_manager.set_status(project_dir, state_manager.STATUS_COMPLETED)
            state_manager.remove_state(project_dir)
            return {"status": "completed"}

    return {"status": "failed"}


def _slugify(text):
    """生成分支友好的 slug"""
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-").lower()
    return text[:30] if text else "task"


if __name__ == "__main__":
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
