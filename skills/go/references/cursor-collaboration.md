# Cursor 半自动协作(机制⑤)

> v1 因 Cursor CLI 版本限制(本地 3.9.8 不支持 `-p`/`--model`),前端任务采用半自动协作。
> v2(升级 Cursor CLI 后)解锁全自动 CLI 编排。

---

## 为什么需要 Cursor

ZCode 不擅长前端 UI 交互任务。Cursor 的 auto 模型 + Sonnet/GPT-5 在前端页面、UI 组件、交互调优上更强。

---

## v1 半自动协作流程

**决策**: A方案(git 变化检测完成信号)。

```
编排层 Step⑤ 遇到前端任务(路由匹配 tool=cursor)
    │
    ▼
1. 暂停编排,记录当前 git HEAD
   git rev-parse HEAD > 记录到 tasks[T_n].git_head_before
    │
    ▼
2. 提示用户切到 Cursor:
   "子任务 T3(前端积分页面)需要在 Cursor 中完成。
    已为你定位到相关文件:[文件列表]
    请在 Cursor 完成开发并 git commit。
    编排层将自动检测 commit 并继续后续任务。"
    │
    ▼
3. 轮询检测 git 变化(每 30 秒检查一次)
   git log --oneline {git_head_before}..HEAD
    │
    ├─ 无新 commit → 继续等待
    │
    └─ 检测到新 commit → 认为任务完成
        ↓
4. 验证产物:
   - git diff {git_head_before}..HEAD 检查改动范围
   - 确认涉及预期文件
        ↓
5. 生成 handoff 摘要(由编排层根据 git diff 生成):
   {files_changed, new_interfaces:[type:component], ...}
        ↓
6. 更新状态文件 tasks[T_n].status = completed
        ↓
7. 继续后续任务
```

---

## 为什么用 git commit 作完成信号

| 方案 | 可靠性 | 问题 |
|------|:---:|------|
| **git commit**(选用) | 🟢 高 | git 是唯一可靠真相;用户只需正常 commit(开发习惯) |
| 文件轮询 | 🟡 中 | 致命缺陷:Cursor 自动改文件产生中间态,轮询会误判"完成了"其实是改一半 |
| 手动确认 | 🟢 最高 | 但太打断,违背编排层"减少人工干预"初衷 |

**git commit 介于两者之间**: 不打断执行流,又能避免误判半成品。

---

## 完成后的处理

编排层检测到 Cursor 任务完成(git commit)后:

1. **生成 handoff 摘要**: 编排层根据 `git diff` 自动生成(因为 Cursor 不会自己输出 handoff)
   ```python
   # 伪代码
   files = git_diff_name_only(head_before, head_after)
   components = extract_components(files)  # 扫描 .tsx/.vue 文件提取组件名
   handoff = {
     "files_changed": files,
     "new_interfaces": [{"type": "component", "name": c} for c in components],
     "artifacts": f"前端页面已完成,改动{len(files)}个文件",
     "git_commit": head_after
   }
   ```

2. **不跑前端验证**: v1 阶段,Cursor 写完代码后**前端验证协议(agent-browser)由编排层调用 ZCode 执行**(缺口5,v2明确归属)。v1 暂时信任 Cursor 产出,在全局集成回归(Step⑦)统一验证。

---

## v2 演进(待 Cursor 升级)

升级 Cursor CLI 支持 `-p`/`--model` 后,解锁全自动:

```bash
# v2: 全自动 CLI 编排(无需用户手动切 Cursor)
cursor agent -p "实现前端积分页面" --model claude-sonnet-4-20250514
```

此时 Cursor 任务与 ZCode 任务一样全自动执行,不再需要 git 检测半自动协作。
