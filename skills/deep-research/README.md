# deep-research（深度调研） — 4 阶段本地化调研闭环

> 📌 **30 秒理解**：数据不出本地、成本为 0 的调研技能。集各家方案之长。

---

## 何时使用

✅ **用这个技能**：
- 调研 / 对比 / 选型 / 综述 / 市场分析 / 竞品分析 / 技术文献综述
- 内部代码库调研 / 决策依据整理 / "我需要了解 X"
- 任何需要**带引用的报告**的调研任务

❌ **不要用**（用其他技能）：
| 任务 | 改用 |
|------|------|
| 创意/方案/架构探索 | `brainstorming` |
| 实施计划/任务拆分 | `writing-plans` |
| 架构/系统审查 | `system-review` |
| 文档协同撰写 | `doc-coauthoring` |
| 编码 | `loop` 或 `go` |

---

## 快速上手（3 步）

### 1. 启动

```
/deep-research（深度调研） 调研 <题目>
```

或自然语言（skill-hub 自动调度）：
```
调研一下 FastAPI 框架的依赖注入机制
对比 A vs B 哪个更适合我的场景
```

### 2. 4 阶段流程

```
Plan（计划）→ Search（搜索）→ Reason（推理）→ Report（报告）
   ↑                                            ↓
   └────────── Reader Testing（独立反馈环）────────┘
```

| 阶段 | 做什么 | 产出 |
|------|--------|------|
| **Plan** | 拆解调研题目为 2-5 个子问题 | `00-plan.md` |
| **Search** | 用 WebFetch / WebSearch / jcodemunch 找资料 | `10-search.md` |
| **Reason** | WDM 决策矩阵 + Munger 反向 5 问 | `20-reason-wdm.md` + `20-reason-munger.md` |
| **Report** | 撰写带引用的最终报告 | `30-report.md` |
| **Reader Testing** | 模拟"无上下文读者"提问 + 回答 | `90-reader-test.md` |

### 3. 文件结构

所有产出存在项目根目录的 `.workflow/<slug>/` 下：

```
<项目根目录>/.workflow/<slug>/
├── 00-plan.md
├── 10-search.md
├── 20-reason-wdm.md
├── 20-reason-munger.md
├── 30-report.md
├── 90-reader-test.md
├── 95-supplemental-findings.md  (可选)
├── 99-final-state.json
└── INDEX.md
```

跨会话恢复：`继续 .workflow/<slug>/`

---

## 核心方法论

- **WDM 决策矩阵**（Reason 阶段）—— 列出 ≥ 3 个方案、加权标准、1-5 评分、加权总分
- **Munger 反向自检**（Reason 阶段）—— 5 问反向：失败模式 / 偏见 / 忽略 / 反对者 / 1 年后
- **Reader Testing**（独立反馈环）—— 模拟"无上下文读者"列出 3-5 个问题
- **动态来源分级**（Search 阶段）—— T1 一手 / T2 二手 / T3 低质 / Reject 拒收

详细提示词模板见 `prompts/` 目录。

---

## 与其他技能的关系

| 维度 | deep-research（深度调研） | brainstorming | writing-plans | to-prd |
|------|-------------------|---------------|---------------|--------|
| 目标产出 | 带引用的调研报告 | 设计文档 (spec) | 实施计划 (plan) | PRD |
| 数据流向 | 本地 | 本地 | 本地 | 本地 |
| 成本 | 0 | 0 | 0 | 0 |
| 适合场景 | 调研/对比/综述 | 创意/方案 | 计划/拆分 | 文档合成 |

**典型串联**：
- `deep-research（深度调研）`（调研）→ `to-prd`（合成 PRD）→ `writing-plans`（实施计划）→ `loop` / `go`（执行）

---

## 关键优势

1. **数据不出本地** —— 所有 WebFetch 通过你的 MCP，不调用外部 LLM API
2. **方法论严谨** —— WDM + Munger + Reader Testing 三重质量门
3. **跨会话恢复** —— checkpoint 机制 + `99-final-state.json`
4. **可观测** —— 每个阶段有完成判据
5. **集合各家之长** —— 学了 doc-coauthoring、recursive-research、Gemini Deep Research、Claude Research 的优点

---

## 限制

- ❌ 不做"市场/用户/竞品"信息搜集（需要外部数据源）
- ❌ 不替代 brainstorming（创意发散）
- ❌ 不替代 writing-plans（实施计划）
- ❌ 不保证学术严谨（动态分级 + Munger 是工程级保障）
- ⚠️ Reader Testing 是 system-reminder 模拟（自问自答，可信度有限）

---

## 相关文件

- [`SKILL.md`](SKILL.md) — 技能定义 / 定位 / 边界
- [`workflow.md`](workflow.md) — 详细操作手册（10 个章节）
- [`prompts/`](prompts/) — 4 个核心提示词模板
  - [`source-tagging.md`](prompts/source-tagging.md) — 动态来源分级
  - [`wdm-matrix.md`](prompts/wdm-matrix.md) — WDM 决策矩阵
  - [`munger-inversion.md`](prompts/munger-inversion.md) — Munger 反向 5 问
  - [`reader-testing.md`](prompts/reader-testing.md) — Reader Testing 模拟
- [`CONFLICT-STRATEGY.md`](CONFLICT-STRATEGY.md) — 与 brainstorming 冲突时的调优策略

---

## 真实试跑参考

`.workflow/loopengine-skillhub-scheduling/` —— 完整跑通 skill-hub 调度算法调研（90% 完成度，4 空白已补 3）。

---

**版本**：1.0.1 · **创建**：2026-06-29
