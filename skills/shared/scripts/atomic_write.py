"""原子写工具（v6.1 共享）

为 go 和 loop 的状态文件提供原子写能力。
完整规范：skills/shared/references/atomic-write-spec.md
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(
    path: str,
    data: dict,
    fsync: bool = True,
    ensure_ascii: bool = False,
    indent: int = 2,
) -> None:
    """原子写 JSON 到指定路径。

    使用 tempfile + os.replace 实现 POSIX 原子替换：
    1. 写到同目录的临时文件（.tmp_*.json）
    2. 写入完成 + fsync 刷盘
    3. os.replace 原子替换目标文件

    Args:
        path: 目标文件路径
        data: 要写入的 dict 数据
        fsync: 是否调用 fsync 强制刷盘（默认 True，更安全）
        ensure_ascii: 是否转义非 ASCII 字符（默认 False，保留中文）
        indent: JSON 缩进空格数（默认 2）

    Raises:
        OSError: 磁盘满 / 权限错
        TypeError: data 不可序列化
        ValueError: JSON 序列化失败

    Example:
        >>> from shared.scripts.atomic_write import atomic_write_json
        >>> atomic_write_json(".orchestrate-state.json", {"status": "in_progress"})
    """
    target_path = Path(path).resolve()
    target_dir = target_path.parent

    # 确保父目录存在
    target_dir.mkdir(parents=True, exist_ok=True)

    # 创建同目录的临时文件（保证 os.replace 原子性）
    fd, tmp_path = tempfile.mkstemp(
        prefix=".tmp_",
        suffix=".json",
        dir=str(target_dir),
    )
    tmp_path = Path(tmp_path)

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
            f.flush()
            if fsync:
                os.fsync(f.fileno())  # 强制刷盘
    except Exception:
        # 写入失败，清理临时文件
        try:
            tmp_path.unlink()
        except OSError:
            pass
        raise

    # 原子替换（POSIX 保证）
    os.replace(str(tmp_path), str(target_path))


def atomic_read_json(path: str) -> dict:
    """读取 JSON 文件。

    Args:
        path: 文件路径

    Returns:
        dict: 解析后的数据

    Raises:
        FileNotFoundError: 文件不存在
        json.JSONDecodeError: JSON 解析失败
    """
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def safe_load_state(path: str, default: dict | None = None) -> dict:
    """安全加载状态文件，失败时返回默认值。

    Args:
        path: 文件路径
        default: 文件不存在或损坏时的默认值

    Returns:
        dict: 状态数据或 default
    """
    if not os.path.exists(path):
        return default if default is not None else {}

    try:
        return atomic_read_json(path)
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


if __name__ == "__main__":
    # 简单测试
    import datetime

    test_path = "/tmp/_test_atomic_write.json"
    test_data = {
        "id": "test-001",
        "status": "in_progress",
        "owner": {
            "pid": os.getpid(),
            "session_id": "test",
            "heartbeat": datetime.datetime.now().isoformat(),
            "started_at": datetime.datetime.now().isoformat(),
        },
    }

    atomic_write_json(test_path, test_data)
    loaded = atomic_read_json(test_path)
    assert loaded == test_data, "原子写后读取不匹配"
    os.unlink(test_path)
    print("✅ atomic_write_json 测试通过")
