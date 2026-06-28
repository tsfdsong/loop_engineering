"""
Git 操作模块(机制③ · 原子性保障 + Worktree 隔离)

负责 git HEAD 记录、回滚、变化检测、worktree 创建/合并/清理。
"""
import subprocess
from pathlib import Path


def run_git(cwd, *args):
    """执行 git 命令,返回 stdout(去除首尾空白)"""
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 失败: {result.stderr}")
    return result.stdout.strip()


def get_head(cwd):
    """获取当前 git HEAD commit SHA"""
    return run_git(cwd, "rev-parse", "HEAD")


def get_current_branch(cwd):
    """获取当前分支名"""
    return run_git(cwd, "rev-parse", "--abbrev-ref", "HEAD")


def commit_exists(cwd, sha):
    """检查某个 commit 是否存在"""
    try:
        run_git(cwd, "cat-file", "-t", sha)
        return True
    except RuntimeError:
        return False


def reset_to(cwd, sha, hard=True):
    """
    回滚到指定 commit(原子性保障 · 机制③C 进程崩溃恢复)。
    """
    flag = "--hard" if hard else "--soft"
    return run_git(cwd, "reset", flag, sha)


def get_changed_files(cwd, from_sha, to_sha="HEAD"):
    """获取两个 commit 之间的改动文件列表"""
    output = run_git(cwd, "diff", "--name-only", from_sha, to_sha)
    return [f for f in output.splitlines() if f]


def get_new_commits(cwd, from_sha):
    """检测是否有新 commit"""
    output = run_git(cwd, "log", "--oneline", f"{from_sha}..HEAD")
    if not output:
        return []
    return [line.split()[0] for line in output.splitlines()]


def get_diff_stat(cwd, from_sha, to_sha="HEAD"):
    """获取改动统计"""
    return run_git(cwd, "diff", "--stat", from_sha, to_sha)


def has_uncommitted_changes(cwd):
    """检查是否有未提交的改动"""
    output = run_git(cwd, "status", "--porcelain")
    return bool(output.strip())


def get_commit_message(cwd, sha):
    """获取某 commit 的 message"""
    return run_git(cwd, "log", "-1", "--format=%s", sha)


# ═══════════════════════════════════════════════════════════
# 硬约束: 分支保护
# ═══════════════════════════════════════════════════════════

PROTECTED_BRANCHES = frozenset({
    "main", "master", "test", "testing",
    "release", "production", "staging",
})

GO_BRANCH_PREFIX = "go-"


def is_go_worktree(project_dir):
    """检测当前是否已处于 go 编排层的 worktree 中"""
    try:
        branch = get_current_branch(project_dir)
        return branch.startswith(GO_BRANCH_PREFIX)
    except RuntimeError:
        return False


def validate_not_protected(project_dir):
    """
    🔴 硬约束: 禁止在保护分支上有未提交改动时执行 /go。
    
    Raises:
        RuntimeError: 在保护分支上且有未提交改动
    """
    current = get_current_branch(project_dir)
    if current in PROTECTED_BRANCHES:
        if has_uncommitted_changes(project_dir):
            raise RuntimeError(
                f"当前在保护分支 '{current}' 上且有未提交改动。\n"
                f"请先 commit 或 stash 后再执行 /go。"
            )


# ═══════════════════════════════════════════════════════════
# Worktree 操作(并发编码隔离 · 机制⑦)
# ═══════════════════════════════════════════════════════════

WORKTREE_BASE_DIR = ".go/worktrees"


def create_worktree(project_dir, task_id):
    """
    为子任务创建隔离的 git worktree。
    
    在 .go/worktrees/<task_id>/ 创建独立工作目录,
    基于当前 feature 分支创建新分支 go-<task_id>。
    
    Args:
        project_dir: 项目根目录(已在 feature 分支上)
        task_id: 子任务 ID(如 T1, T2)
    
    Returns:
        Path: worktree 目录路径
    """
    project_dir = Path(project_dir)
    worktree_dir = project_dir / WORKTREE_BASE_DIR / task_id
    branch_name = f"go-{task_id.lower()}"
    
    # 创建 worktree
    run_git(
        project_dir, "worktree", "add",
        str(worktree_dir),
        "-b", branch_name,
    )
    
    return worktree_dir


def commit_worktree(worktree_dir, message):
    """已废弃 — 请使用 force_commit() 替代。保留仅为向后兼容。"""
    return force_commit(worktree_dir, message)


def merge_worktree_to_feature(project_dir, task_id):
    """
    将 worktree 分支合并回 feature 分支,并清理 worktree。
    
    流程:
    1. 切换到 feature 分支
    2. git merge go-<task_id>
    3. 如果冲突,返回冲突状态(由上层 Agent 解决)
    4. 清理 worktree 目录和分支
    
    Args:
        project_dir: 项目根目录(feature 分支)
        task_id: 子任务 ID
    
    Returns:
        dict: {merged: bool, conflict: bool, files: list}
    """
    project_dir = Path(project_dir)
    worktree_dir = project_dir / WORKTREE_BASE_DIR / task_id
    branch_name = f"go-{task_id.lower()}"
    
    # 先确保在 feature 分支上
    run_git(project_dir, "checkout", get_current_branch(project_dir))
    
    # 尝试合并
    conflict = False
    try:
        run_git(project_dir, "merge", branch_name, "--no-edit")
    except RuntimeError as e:
        if "CONFLICT" in str(e):
            conflict = True
        else:
            raise
    
    # 清理 worktree
    try:
        run_git(project_dir, "worktree", "remove", str(worktree_dir), "--force")
    except RuntimeError:
        pass
    
    # 清理分支(如果已合并)
    try:
        run_git(project_dir, "branch", "-d", branch_name)
    except RuntimeError:
        # 未合并完成,保留分支
        pass
    
    # 获取冲突文件列表
    conflict_files = []
    if conflict:
        try:
            output = run_git(project_dir, "diff", "--name-only", "--diff-filter=U")
            conflict_files = [f for f in output.splitlines() if f]
        except RuntimeError:
            pass
    
    return {
        "merged": not conflict,
        "conflict": conflict,
        "conflict_files": conflict_files,
    }


def create_feature_branch(project_dir, feature_slug):
    """
    从当前分支创建 feature 分支,保护 main/master 不被污染。
    
    Args:
        project_dir: 项目根目录
        feature_slug: 功能标识(用于分支名)
    
    Returns:
        str: feature 分支名
    """
    project_dir = Path(project_dir)
    branch_name = f"go-{feature_slug}"
    
    run_git(project_dir, "checkout", "-b", branch_name)
    return branch_name


def resolve_conflicts_with_agent(project_dir):
    """
    检查是否有未解决的冲突,如果有,返回冲突文件列表。
    冲突的实际解决由上层调用 ZCode Agent 完成。
    
    Returns:
        list: 冲突文件列表,无冲突返回空列表
    """
    project_dir = Path(project_dir)
    try:
        output = run_git(project_dir, "diff", "--name-only", "--diff-filter=U")
        return [f for f in output.splitlines() if f] if output else []
    except RuntimeError:
        return []


def run_tests(project_dir):
    """
    运行项目测试(安全闸门)。
    
    自动检测测试框架并运行,返回是否通过。
    """
    project_dir = Path(project_dir)
    
    # 检测测试框架
    if (project_dir / "pytest.ini").exists() or (project_dir / "pyproject.toml").exists():
        try:
            subprocess.run(
                ["python", "-m", "pytest", "--tb=short", "-q"],
                cwd=str(project_dir), capture_output=True, text=True,
                encoding="utf-8", timeout=300,
            ).check_returncode()
            return True
        except subprocess.CalledProcessError:
            return False
    elif (project_dir / "package.json").exists():
        try:
            subprocess.run(
                ["npm", "test"],
                cwd=str(project_dir), capture_output=True, text=True,
                encoding="utf-8", timeout=300,
            ).check_returncode()
            return True
        except subprocess.CalledProcessError:
            return False
    
    # 无测试框架,默认通过
    return True


# ═══════════════════════════════════════════════════════════
# 强制 Commit + 回归保护(机制⑧)
# ═══════════════════════════════════════════════════════════

def force_commit(worktree_dir, message):
    """
    🔴 强制 commit: 无论 ZCode Agent 是否执行了 commit,
    执行后一定做 git add -A && git commit。
    
    解决 loop skill 中 "自动 git add + commit" 是文本指令
    而非代码约束的 BUG。
    
    Args:
        worktree_dir: worktree 目录
        message: commit message
    
    Returns:
        str|None: commit SHA,无改动返回 None
    """
    worktree_dir = Path(worktree_dir)
    
    # 检查是否有改动
    output = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(worktree_dir), capture_output=True, text=True
    ).stdout.strip()
    
    if not output:
        return None  # 无改动,不需要 commit
    
    # 强制 add + commit
    run_git(worktree_dir, "add", "-A")
    run_git(worktree_dir, "commit", "-m", message)
    
    return get_head(worktree_dir)


def capture_change_snapshot(cwd):
    """
    捕获当前 git 变更快照(用于回归保护)。
    
    Returns:
        dict: {untracked, modified, deleted, staged}
    """
    output = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(cwd), capture_output=True, text=True
    ).stdout
    
    files = {"untracked": [], "modified": [], "deleted": [], "staged": []}
    for line in output.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        filename = line[3:].strip()
        if "?" in status:
            files["untracked"].append(filename)
        elif "M" in status:
            files["modified"].append(filename)
        elif "D" in status:
            files["deleted"].append(filename)
        if status[0] in "MADR":
            files["staged"].append(filename)
    return files


def verify_expected_changes(expected_files, actual_changed):
    """
    回归保护: 验证实际变更文件是否是预期的。
    
    Args:
        expected_files: 子任务声明的预期文件列表(task.files)
        actual_changed: capture_change_snapshot 返回的 dict
    
    Returns:
        dict: {passed: bool, unexpected: list, missing: list}
    """
    all_actual = set(
        actual_changed.get("modified", []) +
        actual_changed.get("untracked", []) +
        actual_changed.get("deleted", [])
    )
    expected = set(expected_files) if expected_files else set()
    
    unexpected = all_actual - expected
    missing = expected - all_actual if expected_files else []
    
    return {
        "passed": len(unexpected) == 0,
        "unexpected": list(unexpected),
        "missing": list(missing),
    }
