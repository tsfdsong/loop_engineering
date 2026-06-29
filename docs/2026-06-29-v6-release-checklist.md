# Skill-Hub v6.0 Alpha 灰度发布检查清单

> 生成时间：2026-06-29
> 分支：feature/skill-hub-v6
> 状态：✅ 实施完成，等待发布决策

## 发布前（必须全部 ✅）

- [x] 4 个 references 文件完整（composite-task-types / complexity-evaluator / orchestrator-protocol / trace-format）
- [x] 3 个测试脚本通过（composite-recognition / orchestrator-execution / failure-defenses）
- [x] v5.4 SKILL.md 备份存在（skills/skill-hub/SKILL.md.v5.4.backup）—— 保留作为防护
- [x] ~~迁移指南完成（docs/migration-guide-v5-to-v6.md）~~（v6.1.1 已删除 — 历史归档）
- [x] README.md 更新（添加 v6.0 章节）
- [x] 设计 + 计划文档完整
- [x] v5.4 黄金轨迹录制（tests/golden-traces/v54-baseline.json）—— 保留作为兼容性保护

## 测试结果汇总

| 测试类型 | 通过标准 | 实际结果 | 状态 |
|---------|--------|---------|:---:|
| 复合任务识别 | ≥ 80% 准确率 | 96.7% (24/25 正 + 5/5 负) | ✅ |
| 编排执行 | ≥ 95% 完成 + token ≤ 2x | 100% 完成 + 7700 tokens | ✅ |
| 失败防御 | 100% 触发停止 | 5/5 场景 | ✅ |

## 发布中

- [ ] git tag v6.0-alpha
- [ ] 更新 AGENTS.md 引用（如需要）
- [ ] 在 skill-hub/SKILL.md frontmatter 标记 `v6_orchestrator: opt-in`（已完成）
- [ ] 推送分支到远程
- [ ] 创建 GitHub PR（feature/skill-hub-v6 → main）

## 发布后（持续验证 1-2 周）

- [ ] 收集 alpha 用户反馈
- [ ] 监控 4 类测试报告（tests/reports/*.json）
- [ ] 监控 trace 日志异常
- [ ] Phase 2 决策：
  - 复合识别准确率持续 ≥ 80% → 推进 v6.0-beta
  - 准确率 < 80% 或用户反馈负向 → 回滚到 v5.4

## 回滚预案

```bash
# 一键回滚 Orchestrator
export LOOPENGINE_ORCHESTRATOR=off

# 完全回滚到 v5.4（如需）
cd skills/skill-hub && cp SKILL.md.v5.4.backup SKILL.md
git add skills/skill-hub/SKILL.md && git commit -m "revert: 回滚 skill-hub 到 v5.4"
```

## 已知限制

- 复合任务识别仅支持 5 类预设
- Orchestrator trace 暂仅本地存储
- 5 类之外的复合任务需 Phase 2 扩展
