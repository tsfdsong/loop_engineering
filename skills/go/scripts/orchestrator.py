"""
编排层主调度器 v4.0 — 线程安全 + 断点恢复 + JSON --json 模式

修复:
  - BUG #4: JSON 解析脆弱 → 用 --json 模式 + 多策略解析
  - BUG #7: 断点续跑没有恢复分支 → 检查 feature_branch 存在性
"""
import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import complexity_evaluator
import state_manager
import git_ops
import zcode_runner
import task_scheduler


def orchestrate(feature, project_dir, acceptance_criteria=None, explicit_flag=None):
    """
    编排层主入口 v4.0。
    """
    project_dir = Path(project_dir)
    print(f"\n{'='*60}")
    print(f"🧠 /go {feature}")
    print(f"{'='*60}")

    # Step ⓪: 断点续跑检测
    if state_manager.state_exists(project_dir):
        return _resume_orchestration(project_dir)

    # Step ⓪.5: 硬约束 — 保护分支检查
    git_ops.validate_not_protected(project_dir)

    # Step ①: L0 复杂度评估
    eval_result = complexity_evaluator.evaluate_complexity(feature, explicit_flag)
    tier = eval_result["tier"]
    print(f"📊 复杂度: {tier} ({eval_result['reason']})")

    # Step ①.5: 创建 feature 分支
    feature_slug = _slugify(feature)
    current_before = git_ops.get_current_branch(project_dir)
    branch = git_ops.create_feature_branch(project_dir, feature_slug)
    print(f"🌿 Feature 分支: {branch} (从 {current_before} 切出)")

    # Step ②: 状态初始化
    orch_id = f"go/{feature_slug}-{datetime.now().strftime('%m%d%H%M')}"
    state_manager.create_state(project_dir, orch_id, feature, tier, acceptance_criteria)

    # 记录分支信息 (用 atomic_update, 修复 BUG #3)
    def _set_branches(s):
        s["feature_branch"] = branch
        s["base_branch"] = current_before
    state_manager.atomic_update(project_dir, _set_branches)
    state_manager.set_status(project_dir, state_manager.STATUS_IN_PROGRESS)

    # Step ③: ZCode 智能拆分
    tasks = _split_tasks_with_zcode(feature, project_dir, tier)
    state_manager.add_tasks(project_dir, tasks)

    no_dep = sum(1 for t in tasks if not t.get("depends_on"))
    print(f"📋 拆分为 {len(tasks)} 个子任务, {no_dep} 个可并发")

    # Step ④⑤: Worktree 并发执行 (Worker Contract v5)
    runtime_profile = task_scheduler.detect_runtime_profile()
    print(f"🔧 Runtime profile: {runtime_profile}")
    result = task_scheduler.execute_tasks_concurrent(
        project_dir, tasks, tier, runtime_profile=runtime_profile,
    )

    if result["all_completed"]:
        # Step ⑦.5: G10 系统审查 (每个特性分支 1 次)
        print(f"\n🔍 G10 系统审查...")
        review_result = _run_system_review(project_dir)
        if review_result["severity"] == "error":
            print(f"❌ 系统审查发现 ERROR 级问题,暂停交付")
            state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
            return {"status": "review_failed", "branch": branch, "review": review_result}
        print(f"✅ 系统审查通过 (severity={review_result['severity']})")

        # Step ⑦: 安全闸 — 跑测试 (一次性, 修复 BUG #5)
        print(f"\n🧪 安全闸: 运行测试...")
        tests_ok = git_ops.run_tests(project_dir)
        if tests_ok:
            print(f"✅ 测试通过")
            state_manager.set_status(project_dir, state_manager.STATUS_COMPLETED)
            print(f"\n🎉 完成! Feature 分支 `{branch}` 已就绪:")
            print(f"   git checkout {current_before} && git merge {branch}")
            state_manager.remove_state(project_dir)
            return {"status": "completed", "branch": branch, "tasks": len(tasks)}
        else:
            print(f"❌ 测试失败! Feature 分支保留")
            state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
            return {"status": "test_failed", "branch": branch}
    else:
        state_manager.set_status(project_dir, state_manager.STATUS_FAILED)
        return {"status": "tasks_failed", "failed": result.get("failed_tasks", [])}


def _split_tasks_with_zcode(feature, project_dir, tier):
    """
    Step ③: 让 ZCode 分析需求,拆分为可并发的子任务。
    """
    if tier == "L1":
        rt = task_scheduler.assigned_runtime_for_task(profile=task_scheduler.detect_runtime_profile())
        return [{
            "id": "T1", "name": feature,
            "assigned_runtime": rt,
            "depends_on": [],
            "prompt": feature, "skills": [], "files": [],
            "status": state_manager.TASK_PENDING,
        }]

    split_prompt = _build_split_prompt(feature, project_dir, tier)

    result = zcode_runner.call_zcode(split_prompt, project_dir, mode="yolo", timeout=120)
    tasks = _parse_tasks_json(result.get("stdout", ""))

    if not tasks:
        print(f"  ⚠️ ZCode 拆分失败,使用回退拆分")
        return _fallback_split(feature, tier)

    profile = task_scheduler.detect_runtime_profile()
    for task in tasks:
        task.setdefault("assigned_runtime", task_scheduler.assigned_runtime_for_task(task, profile))
        task.setdefault("status", state_manager.TASK_PENDING)
        task.setdefault("skills", [])
        task.setdefault("files", [])

    return tasks


def _build_split_prompt(feature, project_dir, tier):
    parts = [
        "分析以下功能需求,拆分成可并发的编码子任务:",
        "",
        f'功能: "{feature}"',
        f"项目目录: {project_dir}",
        "",
    ]

    go_context = _load_go_planning_context(feature, project_dir)
    if go_context:
        parts.extend([
            "以下 go family/DAG 运行时真源会约束拆分方式。若任务与 go 编排有关，必须优先依据这些 family/rules/contracts 来拆分，不要凭空发明流程:",
            "```",
            go_context,
            "```",
            "",
        ])

    parts.extend([
        "只输出 JSON,不要其他文字:",
        '{"tasks": [',
        '  {"id": "T1", "name": "名称", "prompt": "执行指令", "depends_on": [], "skills": [], "files": ["路径"]}',
        "]}",
        "",
        "规则:",
        "1. 操作不同文件的子任务 depends_on 为空 (可并发)",
        "2. 有依赖关系的标注 depends_on",
        "3. files 边界不重叠",
        "4. L2 拆 2-3 个, L3 拆 3-5 个",
    ])
    return "\n".join(parts)


def _load_go_planning_context(feature, project_dir):
    """
    仅在目标明显涉及 go 编排 / family 路由时，把 go references 真源摘要带入拆分 prompt。
    """
    feature_lower = feature.lower()
    if not any(token in feature_lower for token in ["go", "family", "orch", "orchestrat", "编排", "调度"]):
        return None

    project_dir = Path(project_dir)
    refs = [
        project_dir / "skills/go/references/intent-schema.json",
        project_dir / "skills/go/references/capability-registry.yaml",
        project_dir / "skills/go/references/dag-rules.yaml",
        project_dir / "skills/go/references/executor-contracts/direct-skill.json",
        project_dir / "skills/go/references/executor-contracts/loop.json",
        project_dir / "skills/go/references/executor-contracts/go.json",
    ]

    chunks = []
    for path in refs:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if len(content) > 1200:
            content = content[:1200] + "\n... (截断)"
        rel = path.relative_to(project_dir).as_posix()
        chunks.append(f"### {rel} ###\n{content}")

    if not chunks:
        return None
    return "\n\n".join(chunks)


def _parse_tasks_json(stdout):
    """
    从 ZCode 输出中解析任务列表 JSON。
    修复 BUG #4: 多策略解析。
    """
    if not stdout:
        return []

    # 策略 1: 从 ```json``` 代码块提取
    block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', stdout, re.DOTALL)
    if block_match:
        try:
            data = json.loads(block_match.group(1))
            if "tasks" in data:
                return data["tasks"]
        except json.JSONDecodeError:
            pass

    # 策略 2: 直接找 {"tasks": [...]} 结构
    try:
        # 找最外层的 JSON 对象
        start = stdout.find('{"tasks"')
        if start >= 0:
            # 从 start 开始找匹配的 }
            depth = 0
            for i in range(start, len(stdout)):
                if stdout[i] == '{':
                    depth += 1
                elif stdout[i] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = stdout[start:i+1]
                        data = json.loads(candidate)
                        return data.get("tasks", [])
    except (json.JSONDecodeError, ValueError):
        pass

    # 策略 3: 正则 (最后手段)
    match = re.search(r'"tasks"\s*:\s*\[([\s\S]*?)\]', stdout)
    if match:
        try:
            tasks_arr = json.loads("[" + match.group(1) + "]")
            return tasks_arr
        except json.JSONDecodeError:
            pass

    return []


def _fallback_split(feature, tier):
    """ZCode 拆分失败时的骨架回退"""
    count = 2 if tier == "L2" else 3
    profile = task_scheduler.detect_runtime_profile()
    return [{
        "id": f"T{i+1}",
        "name": f"子任务 {i+1}",
        "assigned_runtime": task_scheduler.assigned_runtime_for_task(profile=profile),
        "depends_on": [] if i == 0 else [f"T{i}"],
        "prompt": f"子任务 {i+1}: {feature}",
        "skills": [], "files": [],
        "status": state_manager.TASK_PENDING,
    } for i in range(count)]


def _resume_orchestration(project_dir):
    """
    断点续跑。
    修复 BUG #7: 检查 feature_branch 是否存在。
    """
    state = state_manager.read_state(project_dir)
    tier = state["tier"]
    feature = state["feature"]
    print(f"▶️ 续跑: {feature}")

    # 检查 feature 分支是否存在
    feature_branch = state.get("feature_branch", "")
    if feature_branch:
        try:
            git_ops.run_git(project_dir, "rev-parse", "--verify", feature_branch)
            # 切换到 feature 分支
            git_ops.run_git(project_dir, "checkout", feature_branch)
            print(f"   已切换到 {feature_branch}")
        except RuntimeError:
            print(f"   ⚠️ Feature 分支 {feature_branch} 不存在!")
            state_manager.remove_state(project_dir)
            return {"status": "failed", "error": "feature 分支已被删除"}

    tasks = state["tasks"]
    runtime_profile = task_scheduler.detect_runtime_profile()
    result = task_scheduler.execute_tasks_concurrent(
        project_dir, tasks, tier, runtime_profile=runtime_profile,
    )

    if result["all_completed"]:
        tests_ok = git_ops.run_tests(project_dir)
        if tests_ok:
            state_manager.set_status(project_dir, state_manager.STATUS_COMPLETED)
            state_manager.remove_state(project_dir)
            return {"status": "completed"}

    return {"status": "failed"}


def _run_system_review(project_dir):
    """
    Step ⑦.5: G10 系统审查。

    按变更范围自动判断深度:
    - < 3 文件且未跨模块 → 仅 Step 1 自洽性
    - ≥ 3 文件或跨模块 → Step 1 + 2
    - 跨架构级 → 全三步

    调用 ZCode 加载 system-review 技能执行。判定 severity 用结构化 JSON 协议
    （system-review agent 输出 verdict.json），不再用字符串匹配 emoji/英文
    （消除 v6.x "改个 emoji 即漏判" 的脆性 — 红线 9 R3.1 根因级）。
    """
    import json
    import tempfile
    from pathlib import Path

    # 获取变更范围
    try:
        base_branch = "main"
        state = state_manager.read_state(project_dir)
        if state.get("base_branch"):
            base_branch = state["base_branch"]

        changed_files = git_ops.get_changed_files(project_dir, base_branch)
        file_count = len(changed_files)

        # 判断跨模块
        dirs = set()
        for f in changed_files:
            parts = f.split("/")
            if len(parts) > 1:
                dirs.add(parts[0])
        cross_module = len(dirs) > 1
    except Exception:
        changed_files = []
        file_count = 0
        cross_module = False

    # 确定深度
    if file_count < 3 and not cross_module:
        depth = "仅自洽性检查"
        review_prompt = "加载 system-review 技能，用快速模式审查当前项目的变更，仅执行 Step 1（横向自洽性检查）。"
    elif file_count >= 10 or cross_module:
        depth = "完整三步审查"
        review_prompt = "加载 system-review 技能，用完整模式审查当前项目的所有变更，执行全部三步（自洽性+架构深度+持续改进）。"
    else:
        depth = "自洽性+架构"
        review_prompt = "加载 system-review 技能，审查当前项目的变更，执行 Step 1（自洽性）+ Step 2（架构深度）。"

    print(f"   深度: {depth} (变更 {file_count} 文件, 跨模块={cross_module})")

    # 协议化判定：让 system-review 输出 verdict.json（结构化），而不是匹配字符串
    verdict_path = Path(tempfile.gettempdir()) / f"system-review-verdict-{os.getpid()}.json"
    review_prompt += (
        f"\n\n【强制协议】审查结束后必须将结果写入 JSON 文件 {verdict_path}（UTF-8）。"
        "schema: {\"severity\": \"error\"|\"warning\"|\"pass\", \"findings_count\": int, "
        "\"dimensions_covered\": [\"self_consistency\", \"architecture\", \"improvement\"]}。"
        "未写文件或 schema 校验失败 → 降级到 legacy 字符串匹配（兼容老 agent）。"
    )

    result = zcode_runner.call_zcode(review_prompt, project_dir, mode="yolo", timeout=300)

    # 优先读 verdict.json（结构化），失败再降级到字符串匹配（兼容老 agent）
    output = result.get("stdout", "") + result.get("stderr", "")
    severity = None
    findings_count = 0
    dimensions_covered = []
    verdict_missing = False
    try:
        if verdict_path.exists():
            with open(verdict_path, "r", encoding="utf-8") as f:
                verdict = json.load(f)
            severity = verdict.get("severity")
            findings_count = int(verdict.get("findings_count", 0))
            dimensions_covered = list(verdict.get("dimensions_covered", []))
            # 协议级 schema 校验
            if severity not in ("error", "warning", "pass"):
                raise ValueError(f"invalid severity: {severity}")
            # 清理临时文件
            verdict_path.unlink(missing_ok=True)
    except (json.JSONDecodeError, ValueError, OSError) as e:
        verdict_missing = True
        print(f"   ⚠️ verdict.json 协议失败（{e}），降级到字符串匹配（红线 9 R3.1 警示）")

    if severity is None:
        # 降级路径（仅在协议失败时使用）
        if "CRITICAL" in output or "ERROR" in output.upper():
            severity = "error"
        elif "WARNING" in output.upper() or "⚠️" in output:
            severity = "warning"
        else:
            severity = "pass"

    return {
        "severity": severity,
        "depth": depth,
        "file_count": file_count,
        "cross_module": cross_module,
        "findings_count": findings_count,
        "dimensions_covered": dimensions_covered,
        "verdict_protocol": "verdict.json" if not verdict_missing else "legacy_string_match",
        "output": output[-500:] if output else "",
    }


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
