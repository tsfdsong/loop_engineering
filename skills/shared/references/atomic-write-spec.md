# 原子写规范（v6.1 共享 spec）

> **来源**：从 `skills/go/references/state-protocol.md` 第 99-108 行 +
> `skills/go/references/breakpoint-recovery.md` 第 23-30 行抽取。
> **抽取原因**：同一段 Python 伪代码出现 2 次，抽取后消除重复并提供可复用实现。

## 目的

防止状态文件写到一半因进程崩溃、断电、磁盘满等原因损坏。
POSIX 原子性保证：要么完整写入成功，要么完全没改动（不可能写到一半）。

## 算法（tempfile + os.replace）

```python
import os
import tempfile
import json

def atomic_write_json(path: str, data: dict, fsync: bool = True) -> None:
    """
    原子写 JSON 到指定路径。
    
    Args:
        path: 目标文件路径
        data: 要写入的 dict 数据
        fsync: 是否调用 fsync 强制刷盘（默认 True，更安全）
    
    Raises:
        OSError: 磁盘满 / 权限错 / 父目录不存在
    """
    target_dir = os.path.dirname(os.path.abspath(path))
    os.makedirs(target_dir, exist_ok=True)
    
    # 1. 写到同目录的临时文件
    fd, tmp_path = tempfile.mkstemp(
        prefix=".tmp_",
        suffix=".json",
        dir=target_dir,  # 同目录确保 os.replace 是原子操作
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            if fsync:
                os.fsync(f.fileno())  # 强制刷盘
    except Exception:
        # 写入失败，清理临时文件
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    
    # 2. 原子替换（POSIX 保证）
    os.replace(tmp_path, path)
```

## 为什么是 tempfile + os.replace？

| 方式 | 原子性 | 跨平台 | 性能 |
|------|:------:|:------:|:----:|
| 直接 `open(path, 'w')` | ❌ 中断会损坏 | ✅ | 🟢 最快 |
| **`tempfile + os.replace`** | ✅ **POSIX 原子** | ✅（Windows 也支持） | 🟡 略慢（多一次 rename） |
| 数据库事务 | ✅ | 🟡 需 SQLite | 🔴 重 |

`tempfile + os.replace` 是最简单且满足 POSIX 原子性的方案。

## 异常处理

| 异常 | 触发条件 | 处理 |
|------|---------|------|
| `OSError(28)` | 磁盘满 | 不重试，抛给上层；用户清理磁盘后重试 |
| `OSError(13)` | 权限错 | 不重试，提示用户检查权限 |
| `OSError(2)` | 父目录不存在 | 自动 `os.makedirs(parents=True)` |
| `KeyboardInterrupt` | 用户中断 | 清理 tmp_path 后抛出 |
| `json.JSONDecodeError` | 序列化失败 | 清理 tmp_path 后抛出（理论上不会发生，data 已是 dict） |

## 关键约束

1. **临时文件必须与目标文件同目录**——否则 `os.replace` 退化为"复制+删除"，失去原子性
2. **必须先 `os.fsync`**——否则断电后可能丢失（操作系统缓冲未刷盘）
3. **写入失败必须清理 tmp_path**——避免遗留垃圾文件
4. **不要使用 `shutil.move`**——跨设备会失败，应始终用 `os.replace`

## 双轨制应用

| 状态文件 | 写入入口 | 调用方式 |
|---------|---------|---------|
| `.orchestrate-state.json`（go） | `scripts/state_manager.py` | `from shared.scripts.atomic_write import atomic_write_json` |
| `.loop-state-<slug>.json`（loop） | 内部写入函数（待抽取） | 同上 |

## Python 函数

完整实现见 `scripts/atomic_write.py`。

## 兼容性

- ✅ 与 go/loop 既有内联实现**字节级一致**（行为完全相同）
- ✅ 既有 .orchestrate-state.json / .loop-state-*.json 100% 兼容
