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

# 获取 state_manager 的全局锁 (复用, 不重复创建)
_config_write_lock = state_manager._global_locks_guard


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

    多线程安全: 用全局锁串行化对 config.json 的写操作,
    避免并发任务间互相覆盖 model 设置。

    Args:
        preferred_provider: 指定优先 provider ID (来自 task.model)
    """
    with _config_write_lock:
        config_dir = Path.home() / ".zcode" / "cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.json"

        providers = _load_providers()
        model_main = _load_model_main(preferred_provider)

        # ZCode 要求 provider.enabled === true (不是 falsy)
        # v2/config.json 中很多 provider 缺 enabled 字段, 这里补上
        if preferred_provider and preferred_provider in providers:
            providers = dict(providers)
            providers[preferred_provider] = dict(providers[preferred_provider])
            providers[preferred_provider]["enabled"] = True

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

        # ZCode 严格检查 config.json: JSON.parse 不接受多行 (Extra data 错误)
        # 必须用紧凑单行格式
        with open(config_path, "w") as f:
            json.dump(config, f, ensure_ascii=False, separators=(",", ":"))


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

    # per-task model 指令 (经实测: /model 必须直接跟参数, 用 ";" 分隔后续指令)
    task_model = task.get("model")
    if task_model:
        parts.append("## 模型要求")
        parts.append(f"**首先执行**: `/model {task_model}`")
        parts.append("**然后**执行下面的任务。")
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

    go_runtime_context = _get_go_runtime_context(worktree_dir, task)
    if go_runtime_context:
        parts.append("## go 编排运行时真源")
        parts.append("以下 go family/DAG 资产是真实运行路径要消费的规则与契约，请按它们实现，不要只改文档:")
        parts.append("```")
        parts.append(go_runtime_context)
        parts.append("```")
        parts.append("")

    # 注入 repomix 代码结构 (Python 层调用 CLI, 节省 token)
    repo_structure = _get_repomix_structure(worktree_dir, task.get("files", []))
    if repo_structure:
        parts.append("## 项目代码结构 (repomix 打包)")
        parts.append("以下是与本任务相关的代码文件内容，可直接参考，无需重复读取:")
        parts.append("```")
        parts.append(repo_structure)
        parts.append("```")
        parts.append("")

    parts.append("## 你的任务")
    parts.append(task.get("prompt", task.get("name", "")))
    parts.append("")
    parts.append("完成后请 git add + commit。")

    return "\n".join(parts)


def _get_go_runtime_context(worktree_dir, task):
    """
    当任务明显在实现 go 编排 / family 路由本身时，注入 go references 真源摘要。
    """
    task_files = task.get("files", [])
    task_text = " ".join(
        str(x) for x in [task.get("name", ""), task.get("prompt", "")]
    ).lower()
    touches_go = any("skills/go/" in f or "hooks/" in f for f in task_files)
    mentions_go = any(
        token in task_text
        for token in ["go", "family", "orch", "orchestrator", "编排"]
    )
    if not (touches_go or mentions_go):
        return None

    worktree_dir = Path(worktree_dir)
    refs = [
        worktree_dir / "skills/go/SKILL.md",
        worktree_dir / "skills/go/references/intent-schema.json",
        worktree_dir / "skills/go/references/capability-registry.yaml",
        worktree_dir / "skills/go/references/dag-rules.yaml",
        worktree_dir / "skills/go/references/executor-contracts/direct-skill.json",
        worktree_dir / "skills/go/references/executor-contracts/loop.json",
        worktree_dir / "skills/go/references/executor-contracts/go.json",
    ]
    chunks = []
    for path in refs:
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8").strip()
        except OSError:
            continue
        if len(content) > 1600:
            content = content[:1600] + "\n... (截断)"
        chunks.append(f"### {path.relative_to(worktree_dir)} ###\n{content}")
    if not chunks:
        return None
    return "\n\n".join(chunks)


def _get_repomix_structure(worktree_dir, task_files):
    """
    调用 repomix CLI 打包代码结构。
    
    Returns:
        str: repomix 输出 (截断到 8000 字符), 失败返回 None
    """
    try:
        worktree_dir = Path(worktree_dir)
        # Windows 上 repomix 是 .cmd 文件, 需要用 shell=True 或直接调 .cmd
        repomix_cmd = os.path.expandvars(r"%APPDATA%\npm\repomix.cmd")
        if not os.path.exists(repomix_cmd):
            import shutil
            found = shutil.which("repomix.cmd") or shutil.which("repomix")
            if found:
                repomix_cmd = found
            else:
                return None
        
        cmd = [repomix_cmd, "--stdout", "--quiet"]
        
        if task_files:
            existing_files = [f for f in task_files if (worktree_dir / f).exists()]
            if not existing_files:
                return None
            cmd.extend(["--include", ",".join(existing_files)])
        
        cmd.append(str(worktree_dir.resolve()))
        
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, encoding="utf-8",
            timeout=30, cwd=str(worktree_dir),
            shell=False,
        )
        
        if result.returncode == 0 and result.stdout:
            output = result.stdout.strip()
            if len(output) > 8000:
                output = output[:8000] + "\n... (截断)"
            return output
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    
    return None


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
# 并发 Worktree 执行 (v5.0 → task_scheduler + Worker Contract)
# ═══════════════════════════════════════════════════════════

def execute_packet_in_worktree(*args, **kwargs):
    from task_scheduler import execute_packet_in_worktree as _fn
    return _fn(*args, **kwargs)


def execute_task_in_worktree(*args, **kwargs):
    from task_scheduler import execute_task_in_worktree as _fn
    return _fn(*args, **kwargs)


def execute_tasks_concurrent(*args, **kwargs):
    from task_scheduler import execute_tasks_concurrent as _fn
    return _fn(*args, **kwargs)


def detect_runtime_profile():
    from task_scheduler import detect_runtime_profile as _fn
    return _fn()


def assigned_runtime_for_task(*args, **kwargs):
    from task_scheduler import assigned_runtime_for_task as _fn
    return _fn(*args, **kwargs)


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
