# 断点恢复机制(机制③ · 核心痛点解决)

> 解决"网络断联/token耗尽/模型切换导致迭代中断无法恢复"——编排层最核心的保障。

---

## 三重保障

### A. 检查点(每步持久化)

**原则**: 每次状态变更立即写盘,中断也不丢进度。

```
子任务开始 → 状态标记 in_progress + 记录 git_head_before
    ↓ 立即写盘
子任务执行中 → 每个关键节点更新状态
    ↓ 立即写盘
子任务完成 → 状态标记 completed + 写 handoff 摘要 + git_commit_after
    ↓ 立即写盘
```

**原子写入**(防写一半中断损坏):
```python
import json, tempfile, os
def write_state(state, path):
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path))
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # 原子操作(Windows用os.replace)
```

---

### B. 自动恢复(重启即续跑)

编排层启动第一件事(Step⓪):

```
1. 检查 .orchestrate-state.json 是否存在
   ├─ 不存在 → 全新开始(Step①)
   └─ 存在 → 读取状态
        ↓
2. 一致性校验:
   a. git HEAD vs tasks[进行中].git_head_before
      不一致 → 提示"断点后有外部改动,重新确认范围"
   b. updated_at 距今 >24h
      → 提示"搁置较久,复盘验收条件是否仍有效"
   c. owner.heartbeat 判定并发
      <5min → "他会在跑",提示[接管/另起/取消]
      ≥5min → "前会话僵死",自动接管
        ↓
3. 定位断点:
   - status=in_progress 的任务 → 重点检查
   - status=completed 的任务 → 跳过(已验证产物)
        ↓
4. 验证已完成任务的产物:
   git log --oneline git_head_before..git_commit_after
   确认 commit 存在且代码完整
        ↓
5. 从断点继续:
   - 进行中的任务 → git reset 到 git_head_before → 重新执行(原子性)
   - 待执行的任务 → 按拓扑序继续调度
```

---

### C. 错误分类 + 自动重试

不同中断原因用不同恢复策略,**不一刀切**:

| 中断原因 | 检测方式 | 恢复策略 | 是否打断用户 |
|---------|---------|---------|:---:|
| **网络断联** | API 超时/连接错误/ETIMEDOUT | 指数退避重试(3次: 1s→2s→4s)→续跑 | ❌ 不打断 |
| **token 耗尽** | 429/quota_exceeded/insufficient_quota | 自动降级 DeepSeek → 续跑 | ❌ 不打断 |
| **模型切换** | model_not_found/model_overloaded | 切备选模型(GLM-5.2→GLM-4.7)→续跑 | ❌ 不打断 |
| **进程崩溃** | 状态标记 in_progress 但 heartbeat 过期(≥5min) | git reset 到 git_head_before → 重新执行 | ❌ 不打断 |
| **用户手动中断** | Ctrl+C / 会话关闭 | 保存状态 → 下次启动询问是否续跑 | ✅ 下次询问 |
| **DeepSeek 也限流** | DeepSeek 返回 429 | 暂停 + 人工介入(保存状态,等待配额恢复) | ✅ 必须告知 |

---

## 原子性保障(防半成品代码)

**核心问题**: 任务执行到一半中断,文件可能写了一半,产生"半成品"代码。

**解决**: 每个 in_progress 任务记录 `git_head_before`(任务开始前的 HEAD)。

```
恢复时:
  发现任务 status=in_progress 且无 git_commit_after
    ↓
  git reset --hard git_head_before  # 回滚到任务开始前
    ↓
  重新执行该任务(从干净状态开始)
```

**保证**: 不会有半成品代码残留,每次重试都从干净的 git 状态开始。

---

## 与 loop 断点续跑的区别

| 维度 | loop Step⓪ | 编排层 Step⓪ |
|------|-----------|-------------|
| 范围 | 单任务内(轮次级) | **跨子任务(任务树级)** |
| 状态 | .loop-state(单文件) | .orchestrate-state(任务树) |
| 原子性 | 每轮 commit | 每子任务 git_head_before 回滚 |
| 错误分类 | 无(统一续跑) | **6类错误分类重试** |

**为什么编排层需要更强的恢复**: loop 是单会话,中断概率低;编排层跨多工具/多模型/长时间运行,中断概率高,必须有强恢复。

---

## 🔗 v6.1 共享引用

> **v6.1 增强**：本文件中的三步骤断点恢复协议（一致性校验 → 搁置时长 → 状态定位）已抽取到 `shared/references/breakpoint-recovery-base.md`，与 loop 技能共享。

| 共享 spec | 替换原文件中的内容 | 详见 |
|----------|----------------|------|
| `shared/references/breakpoint-recovery-base.md` | 三步骤协议 | 一致性校验（git HEAD / 分支 / worktree）+ 搁置时长阈值（1h/24h）+ 状态定位规则 |
| `shared/references/atomic-write-spec.md` | 6 类错误分类中的"状态文件损坏"类 | tempfile + os.replace 原子写保证 |
| `shared/references/state-protocol-base.md` | 5 状态机定义 | planning → in_progress → completed/failed/paused |

**本文件保留的编排层特有内容**：
- 任务树级范围（vs loop 的轮次级）
- 6 类错误分类重试策略
- git_head_before 原子性回滚机制
- 跨子任务并发检测

**向后兼容**：本文件原有内容**全部保留**，共享 spec 是**增量引用**而非修改。
