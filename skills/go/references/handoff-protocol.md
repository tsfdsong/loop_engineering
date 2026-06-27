# 上下文交接协议(机制⑥)

> 解决"子任务跨工具/跨模型执行,上下文易丢失"——T1完成后T2不知道T1产出了什么。

---

## 问题场景

```
T1(数据库迁移, ZCode执行) → 完成
    ↓ 切工具
T2(API开发, ZCode执行) → 不知道T1建了什么表!
    ↓ 切工具
T3(前端页面, Cursor执行) → 不知道T2有哪些API!
```

单会话(loop)上下文天然连续,但编排层跨工具/跨模型,上下文会断。

---

## 解决:结构化 handoff 摘要

每个子任务完成时,**必须输出一份机器可读的交接摘要**,写入状态文件 `tasks[].handoff`。

### Handoff Schema

```json
{
  "files_changed": [
    "app/models/points.py",
    "migrations/019_points.sql"
  ],
  "new_interfaces": [
    {
      "type": "table",
      "name": "points",
      "columns": ["user_id", "amount", "reason", "created_at"]
    },
    {
      "type": "function",
      "name": "add_points(user_id, amount, reason)",
      "returns": "void"
    }
  ],
  "artifacts": "数据库迁移已完成,points 表就绪,add_points 函数可用",
  "git_commit": "def5678",
  "next_task_hint": "T2 可基于 points 表和 add_points 函数开发累积/兑换API,表结构见 app/models/points.py"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `files_changed` | string[] | 本任务修改/新增的文件列表 |
| `new_interfaces` | object[] | 新增的接口(表/API/函数/组件),供下个任务引用 |
| `new_interfaces[].type` | enum | `table` / `api` / `function` / `component` |
| `artifacts` | string | 人类可读的产出摘要(一段话) |
| `git_commit` | string | 本任务的 commit SHA |
| `next_task_hint` | string | 给下一个任务的提示(关键信息+引用路径) |

---

## 生成规范

**谁生成**: 完成任务的工具**自己生成**(它最清楚产出了什么)。

**生成时机**: 子任务执行完成、门禁通过后,输出 handoff 摘要。

**编排层的职责**: 只负责**存储**(写入状态文件)和**注入**(下个任务启动时把前序任务的 handoff 注入其 prompt)。

---

## 注入规范

下一个子任务(T(n+1))启动时,编排层把**所有前置任务的 handoff 摘要**注入其 prompt:

```
你正在执行子任务 T2: 积分累积/兑换API

前置任务已完成,以下是它们的产出摘要(供你参考):

【T1: 数据库表设计】已完成
- 修改文件: app/models/points.py, migrations/019_points.sql
- 新增接口:
  • 表 points: 列 [user_id, amount, reason, created_at]
- 提示: T2 可基于 points 表开发累积/兑换API

请基于以上上下文开始你的任务。
```

---

## 核心价值

1. **上下文连续**: T2 知道 T1 产出了什么,不重复造轮子
2. **省 token**: 只传摘要(~500 tokens),不传完整执行日志(~50K tokens)
3. **跨工具无障碍**: Cursor/Trae 都能读懂结构化摘要(JSON)
4. **可追溯**: handoff 存在状态文件,断点恢复时也能看到历史交接

---

## 与 loop 的区别

loop 是单会话,上下文在对话历史里天然连续,不需要交接协议。
编排层跨多工具/多模型,**handoff 摘要是唯一的上下文桥梁**。
