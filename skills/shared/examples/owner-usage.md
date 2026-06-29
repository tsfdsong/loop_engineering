# owner 字段使用示例（v6.1）

> 演示如何在 go 和 loop 的状态文件中正确使用 owner 字段。
> 完整规范见 `references/owner-field-spec.md`。

## go 侧使用

### 写入 owner（state_manager.py）

```python
import os
import datetime
from shared.scripts.atomic_write import atomic_write_json

state = {
    "orchestrate_id": "go/order-mgmt-0630",
    "feature": "实现订单管理",
    "status": "in_progress",
    "owner": {
        "pid": os.getpid(),
        "session_id": "sess_abc123",
        "heartbeat": datetime.datetime.now().isoformat(),
        "started_at": datetime.datetime.now().isoformat(),
    },
    "decision_log": [],
    # ... 其他字段
}

atomic_write_json(".orchestrate-state.json", state)
```

### 读取并判定 owner 状态

```python
import json
import datetime
from pathlib import Path

def check_owner_state(state_path: str) -> str:
    """返回 'alive' / 'stale' / 'dead' / 'abandoned'"""
    if not Path(state_path).exists():
        return "no_state"
    
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    
    owner = state.get("owner")
    if not owner:
        return "no_owner"
    
    heartbeat = datetime.datetime.fromisoformat(owner["heartbeat"])
    now = datetime.datetime.now()
    elapsed = (now - heartbeat).total_seconds() / 60  # 分钟
    
    if elapsed < 5:
        return "alive"  # 提示"他会在跑"
    elif elapsed < 30:
        return "stale"  # 自动接管
    elif elapsed < 24 * 60:
        return "dead"   # 自动接管
    else:
        return "abandoned"  # 强制询问用户
```

## loop 侧使用

### 写入 owner（loop 内部）

```python
import os
import datetime
from shared.scripts.atomic_write import atomic_write_json

loop_state = {
    "loop_id": "loop/pagination-0630",
    "feature": "实现分页功能",
    "status": "in_progress",
    "mode": "🤖 auto",
    "auto_mode": True,
    "owner": {
        "pid": os.getpid(),
        "session_id": "sess_def456",
        "heartbeat": datetime.datetime.now().isoformat(),
        "started_at": datetime.datetime.now().isoformat(),
    },
    "decision_log": [],
    "current_step": "Step 2",
    "current_round": 1,
    "total_rounds": 3,
    "task_list": [],
    # ... 其他字段
}

atomic_write_json(".loop-state-loop-pagination-0630.json", loop_state)
```

## 心跳更新（长时间任务）

```python
import datetime
import json
from pathlib import Path

def update_heartbeat(state_path: str) -> None:
    """更新 owner.heartbeat（每 60s 调一次）"""
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    
    state["owner"]["heartbeat"] = datetime.datetime.now().isoformat()
    state["updated_at"] = datetime.datetime.now().isoformat()
    
    atomic_write_json(state_path, state)

# 在长时间循环中
while not done:
    do_work()
    update_heartbeat(".orchestrate-state.json")
    time.sleep(60)  # 每分钟更新一次心跳
```

## 接管死锁 owner

```python
import json
import datetime
from pathlib import Path

def takeover_owner(state_path: str) -> None:
    """自动接管 5+ 分钟未更新的 owner"""
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)
    
    old_owner = state["owner"]
    new_owner = {
        "pid": os.getpid(),
        "session_id": f"sess_takeover_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
        "heartbeat": datetime.datetime.now().isoformat(),
        "started_at": datetime.datetime.now().isoformat(),
    }
    
    # 记录到 decision_log
    state["decision_log"].append({
        "timestamp": datetime.datetime.now().isoformat(),
        "step": "owner.takeover",
        "decision": f"接管 owner (old_pid={old_owner['pid']}, new_pid={new_owner['pid']})",
        "rationale": f"原 owner heartbeat > 5min 未更新",
    })
    
    state["owner"] = new_owner
    state["updated_at"] = datetime.datetime.now().isoformat()
    
    atomic_write_json(state_path, state)
```

## 双轨制验证

两份状态文件的 owner 字段**结构完全一致**：

```python
def validate_owner_field(state: dict) -> bool:
    required = {"pid", "session_id", "heartbeat", "started_at"}
    if "owner" not in state:
        return False
    return required.issubset(set(state["owner"].keys()))
```

详见 `references/owner-field-spec.md`。
