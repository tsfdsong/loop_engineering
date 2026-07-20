# 冲突场景调优策略（deep-research vs brainstorming）

> 📌 **本文件用途**：当用户输入同时包含 brainstorming 和 deep-research 触发词时，给 go 和 AI 提供调优策略。
> 📅 **生成时间**：2026-06-29（基于 BM25 + LLM 模拟路由测试结果）

---

## 1. 三类典型冲突场景

| 类型 | 用户输入举例 | 单技能路由 | 实际意图 |
|------|------------|----------|---------|
| **调研 → 设计** | "调研 FastAPI 后设计方案" | 错（只去 deep-research）| **应该串联**：deep-research → brainstorming |
| **设计 → 调研** | "设计一个功能，先调研市场" | 错（只去 brainstorming）| **应该串联**：brainstorming → deep-research |
| **二选一明确** | "我想做个新功能" vs "我想调研 X" | 二选一 | 当前 OK |

**关键洞察 [H]**：当用户输入包含**连串意图**（"调研 X + 设计 Y"），单技能路由是**错的**。应该是**复合任务编排**。

---

## 2. 调优策略（3 步）

### Step 1：检测"复合意图"

如果用户输入命中以下特征之一，标记为"复合"：
- ✅ "调研/选型/对比... 然后/接着/之后 设计/方案/计划"
- ✅ "做/设计/创建 X，先/然后 调研/了解"
- ✅ "我想 X（X 是抽象任务）+ 怎么/如何做 X"（隐含两步）

### Step 2：判断"顺序"

按"先数据后设计"的原则：
| 第 1 关键词 | 第 2 关键词 | 顺序 |
|-----------|-----------|------|
| 调研/对比/选型 | 设计/方案/计划 | **先 deep-research → 后 brainstorming** |
| 设计/方案/创建 | 调研/了解/对比 | **先 brainstorming → 后 deep-research** |
| 同类（都调研或都设计） | — | 单技能路由 |

### Step 3：接力棒格式

deep-research → brainstorming 接力时，把 30-report.md 的关键发现作为 brainstorming 的输入：

```yaml
# 接力棒 YAML
user_input: "调研 FastAPI 后设计方案"
handoff:
  from_skill: deep-research
  to_skill: brainstorming
  artifacts:
    - file: ".workflow/<slug>/30-report.md"
      role: "用户提供的事实基础"
  notes: "deep-research 已完成调研，brainstorming 基于此设计方案"
```

brainstorming → deep-research 接力时，把 spec.md 作为 deep-research 的输入：

```yaml
user_input: "设计功能 X，先调研市场"
handoff:
  from_skill: brainstorming
  to_skill: deep-research
  artifacts:
    - file: "docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md"
      role: "brainstorming 已确定的设计方向，需要 deep-research 补充外部数据"
  notes: "brainstorming 已确定 spec，deep-research 需补充调研"
```

---

## 3. 已知限制

| 限制 | 严重度 | 缓解 |
|------|------|------|
| **go 默认不自动触发复合编排** | 🟡 中 | 显式用 `/go`（family-first）触发多技能编排 |
| **description 无法精确抢"做 X"中文短语** | 🟡 中 | A1 用例 BM25 score = 0 是已知问题 |
| **接力棒机制无自动化** | 🟡 中 | 用户需手动 "继续 .workflow/<slug>/" 触发下一阶段 |
| **冲突场景 C1/C2/C3 全部被 BM25 路由到 deep-research** | 🟠 较高 | description 中文"调研"权重高于英文"design" |

---

## 4. 实战示例

### 示例 1：调研 + 设计（C1 类冲突）

**用户输入**："基于调研报告做技术选型方案设计"

**当前路由**（description 调优后）：deep-research

**理想路由**：
1. **Skill 1**：deep-research（产出基于报告的事实分析）
2. **Skill 2**：brainstorming（基于事实做技术选型方案）
3. **Skill 3**（可选）：writing-plans（写实施计划）

**手动串联方式**：
```
# Step 1
你说：调研 ZCode 调度算法
（AI 加载 deep-research，跑完 4 阶段，产出 .workflow/zcode-scheduling/30-report.md）

# Step 2
你说：继续 .workflow/zcode-scheduling/，基于报告做技术选型方案设计
（AI 加载 brainstorming，跑完 9 步流程，产出 spec）
```

### 示例 2：设计 + 调研（C3 类冲突）

**用户输入**："我想做个新功能，先调研一下 FastAPI 和 Django"

**当前路由**（description 调优后）：deep-research

**理想路由**：
1. **Skill 1**：brainstorming（先确定"做什么功能"）
2. **Skill 2**：deep-research（基于功能调研技术栈对比）
3. **Skill 3**：writing-plans

**手动串联方式**：
```
# Step 1
你说：我想做个用户通知功能
（AI 加载 brainstorming，问澄清问题 + 出 2-3 方案）

# Step 2
你说：调研 FastAPI 和 Django 哪个更适合这个通知功能
（AI 加载 deep-research，对比技术栈）

# Step 3
你说：基于对比结果，写实施计划
（AI 加载 writing-plans）
```

---

## 5. go 现状与未来扩展

**当前状态（v2.0）**：go Step 0 承担 family-first 意图识别。自然语言优先，显式入口为 `/go`：

- 自动识别场景家族：review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test
- 在 family 内抽取 actions，按 rule-first 组装串行/并行 DAG
- handoff schema 自动把前一阶段结构化产出喂给后一阶段（见 `skills/go/references/handoff-schema.json`）

> 设计哲学：go Step 0 只做"意图→执行图"规划，不替代 go 后续 worktree 并发 / loop 的执行细节。

---

## 6. 下一步

**测试**：在 ZCode 端跑 C1/C2/C3 实测，看 go 实际怎么路由。如果实测仍全部 → deep-research，那意味着 go 用的是 BM25-like 关键词匹配（确认了我的怀疑）。如果实测给出"复合任务提示"，那意味着 go 已有 LLM 路由层（更智能）。

**记录**：实测结果填到 `96-scheduling-accuracy-test.md` 的 C 类表。

---

**作者**：MiniMax-M3（基于自动测试结果）
**生成时间**：2026-06-29
**版本**：v1.0
