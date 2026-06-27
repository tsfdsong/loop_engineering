"""
Git 操作模块(机制③ · 原子性保障)

负责 git HEAD 记录、回滚、变化检测(Cursor 半自动协作完成信号)。
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


def commit_exists(cwd, sha):
    """检查某个 commit 是否存在(验证已完成任务的产物)"""
    try:
        run_git(cwd, "cat-file", "-t", sha)
        return True
    except RuntimeError:
        return False


def reset_to(cwd, sha, hard=True):
    """
    回滚到指定 commit(原子性保障 · 机制③C 进程崩溃恢复)。

    in_progress 任务中断后,reset 到 git_head_before 再重新执行,
    保证无半成品代码残留。
    """
    flag = "--hard" if hard else "--soft"
    return run_git(cwd, "reset", flag, sha)


def get_changed_files(cwd, from_sha, to_sha="HEAD"):
    """获取两个 commit 之间的改动文件列表(Cursor 完成信号检测 · 机制⑤)"""
    output = run_git(cwd, "diff", "--name-only", from_sha, to_sha)
    return [f for f in output.splitlines() if f]


def get_new_commits(cwd, from_sha):
    """
    检测是否有新 commit(Cursor 半自动协作完成信号)。

    返回 from_sha 之后的新 commit 列表,空列表表示用户尚未 commit。
    """
    output = run_git(cwd, "log", "--oneline", f"{from_sha}..HEAD")
    if not output:
        return []
    return [line.split()[0] for line in output.splitlines()]


def get_diff_stat(cwd, from_sha, to_sha="HEAD"):
    """获取改动统计(生成 handoff 摘要用)"""
    return run_git(cwd, "diff", "--stat", from_sha, to_sha)


def has_uncommitted_changes(cwd):
    """检查是否有未提交的改动"""
    output = run_git(cwd, "status", "--porcelain")
    return bool(output.strip())


def get_commit_message(cwd, sha):
    """获取某 commit 的 message"""
    return run_git(cwd, "log", "-1", "--format=%s", sha)
