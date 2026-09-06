# 端到端示例（v2.0 强化）

> SKILL.md §端到端示例的外迁全文。何时读：需要参照 go 全流程的实际输出形态、交付报告格式或 L1/L3 档差异时。

## 示例 1：跨模块新功能（L3 · go + supervisor + 3 loop 并发）

**用户输入:** `/go 实现订单管理功能 · 验收：创建订单/查询订单/取消订单`

**go 流程（10 步）：**

1. **Step 0 意图识别** → family=design_build（单 family · confidence 0.92 · 自动档）
2. **Step ① L0 评估** → L3（跨模块 + 多接口 · 触发深度拆分 + 真并发）
3. **Step ①.5 6 维项目上下文分析**（落地约束 · ≠产品需求分析）：
   - 维度1 项目身份：全栈 Web（FastAPI + React）· Docker 部署
   - 维度2 技术栈：Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL
   - 维度3 现有模块：users / products / points（无 orders）
   - 维度4 功能匹配：**复用 existing users 表**（FK user_id）+ **新建 orders 模块**
   - 维度5 架构约束：遵循 router→service→model 分层 · 用 Alembic 迁移
   - 维度6 风险方案：方案 A 新建 orders 模块（推荐 · 与现有分层一致）/ 方案 B 扩展 products（未采纳 · 职责混淆）
4. **Step ③ 拆分** → 3 子任务 DAG（每包含 goal + acceptance）：
   - T1: orders schema + Alembic migration（**独立** · 无依赖）
   - T2: orders API CRUD（创建/查询/取消）· **依赖 T1**
   - T3: orders 单元 + 集成测试 · **依赖 T2**
5. **Step ⑤ 并行前沿派发**（ready 写安全节点一次派齐执行器）：
   - 前沿 1：`supervisor` + `loop T1`（T2/T3 依赖未满足 · 不在前沿）
   - T1 完成后前沿 2：`loop T2`
   - T2 完成后前沿 3：`loop T3`
   - （若另有无依赖写安全节点，与 T1 同前沿并行；写集冲突则串行）
6. **supervisor 监控时序**：
   - T+0:30s → T1 done（schema + migration G0-G9 全绿）
   - T+0:31s → T2 启动
   - T+4:20s → T2 G3 test 失败（cancel 接口边界 case）→ **supervisor R1 重启**（重派 T2 到新 worktree）
   - T+7:50s → T2 再次 exhausted → **supervisor R2 降级**（DeepSeek 接手 cancel 接口 · 标 degraded=true）
   - T+9:10s → T2 done（degraded）→ T3 启动
   - T+12:40s → T3 done（测试全绿 · 含 cancel 边界 case）
7. **Step ⑥ merge**：顺序 merge T1 → T2 → T3（T2 含 degraded 标记 · 进交付报告）
8. **Step ⑦ 回归**：pytest 全量（含 users + products + orders）→ 全绿
9. **Step ⑦.5 G10 system-review**：架构一致性 ✅（orders 遵循现有分层 · 未污染 users 模块）· WARNING 1 条（cancel 接口建议加幂等键 · 登记后续）
10. **Step ⑧ 交付**：自动 merge to `feature/orders`（因 T2 degraded=true → **触发 🛑 人工闸门** · 交付报告含完整决策追溯 · 等用户签字 review）

**交付报告关键字段：**
- 质量分层：loop 门禁全绿 2 任务（T1/T3 · 高）· DeepSeek 降级 1 任务（T2 · degraded=true）
- 决策追溯：R1 重启 1 次 + R2 降级 1 次（cancel 接口边界 case 复杂度超预期）
- 验收：创建/查询/取消 3 接口全实现 · 测试覆盖 92%

## 示例 2：L1 单文件修复（直通档 · 不拆分）

**用户输入:** `/go-fast 修复登录页 typo "Sign ni" → "Sign in"`

**go 流程（精简 · L1 直通）：**

1. Step 0 意图识别 → family=debug_fix（confidence 0.98 · 自动）
2. Step ① L0 → L1（`-fast` 强制 · 单文件单行）
3. Step ①.5 → 一句话项目上下文分析（项目=Web · 单字符串替换 · 无架构影响）
4. **委托 loop**（side-effect=single write · 包含 goal+acceptance）→ loop --level=L1
5. loop 跑 G0/G1/G9（3 核心门禁）→ 全绿
6. Step ⑧ 自动 merge（无 degraded · 门禁全绿）

**关键差异（vs 示例 1）**：L1 不拆分、**无并行前沿调度税**、不派 supervisor、不跑 G10（改动 <3 文件）。

## 附：交付报告字段示例（对应 SKILL.md Step ⑧）

```
📊 交付报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌─ 项目上下文分析
│  项目类型: 全栈Web · 技术栈: React+FastAPI
│  已有模块: points/orders/users
│
├─ 推荐方案
│  方案: 扩展现有 API(方案A)
│  理由: 复用 points 表,避免新模块,影响最小
│
├─ 替代方案(未采纳)
│  方案B: 新建独立模块
│  未采纳: 与现有架构不一致,引入额外依赖
│
├─ 执行摘要
│  子任务: 3/3 完成 · 门禁: 全绿
│  降级: 无 · 回归: 通过
│
└─ 质量分层
   loop门禁全绿: 2个任务(高)
   ZCode直通: 0个任务
   DeepSeek降级: 0个任务
```
