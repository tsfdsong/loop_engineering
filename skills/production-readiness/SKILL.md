---
name: production-readiness
description: "Use when preparing for production deployment, doing pre-launch audits, designing stability patterns (circuit breaker, retry, timeout), or planning release strategy (blue-green, canary). Triggers on 上线, 生产, 部署, 断路器, 金丝雀, production. Do NOT use for: CI setup (use github-actions-templates), or local dev (use testing)."
metadata:
  version: "2.1"
  type: skill
  sources:
    - community (production-code-audit)
    - ciembor/agent-rules-books (release-it)
  merged_from:
    - production-code-audit
    - release-it
  merge_date: "2026-06-29"
  merge_date_v2_1: "2026-06-30"  # v6.4 强化 3 阶段上线流程
  merge_reason: |
    v6.2 合并 → 2 源并排（审计 + 稳定）；v6.4 重组为 3 阶段上线流程（审计 → 稳定 → 发布），
    真正从"上线工作流"角度融合而非简单堆叠。
  workflow:
    - stage_1: audit (上线前全代码库审计)
    - stage_2: stability (应用稳定性模式)
    - stage_3: release (蓝绿/金丝雀发布)
---

# Production Readiness 超级技能

## 核心定位：3 阶段上线工作流

```
┌────────────────────────────────────────────────────────┐
│ Stage 1: 审计 (Audit) — 上线前全代码库审计             │
│   6 维度（代码质量 / 架构 / 性能 / 安全 / 可观测 / 维护）│
│   ↓ 修复 Critical + Important                          │
│ Stage 2: 稳定 (Stability) — 应用稳定性模式            │
│   反模式识别（集成点/连锁反应/级联）→ 模式（超时/断路器）│
│   ↓ 故障演练通过                                        │
│ Stage 3: 发布 (Release) — 渐进式发布                  │
│   容量测试 + 蓝绿/金丝雀/滚动 → 监控 + 告警            │
│   ↓ 监控稳定                                            │
│  ✅ 上线完成                                             │
└────────────────────────────────────────────────────────┘
```

**何时该用 production-readiness**：
- 上线前的全流程准备
- 重大变更后（架构升级 / 库升级）
- 定期生产健康检查（季度）
- 故障后的系统性加固

**何时不该用**：
- ❌ 紧急 hotfix（应 systematic-debugging）
- ❌ 纯代码层审查（应 code-reviewer）
- ❌ 项目级审查（应 system-review）

---

## Stage 1 · 审计（Audit · production-code-audit）

> 目标：全代码库 6 维度审计，找出 Critical / Important / Minor 三级问题

### 6 维度审计清单

| 维度 | 检查项 | 通过标准 |
|------|-------|---------|
| **代码质量** | 命名、注释、复杂度、重复 | 圈复杂度 ≤ 10，重复率 < 5% |
| **架构** | 分层、依赖、耦合度 | 依赖方向单向，无循环 |
| **性能** | 瓶颈、N+1、内存 | 无明显热点 |
| **安全** | 注入、密钥、权限 | OWASP Top 10 全防 |
| **可观测性** | 日志、指标、追踪 | 关键路径全覆盖 |
| **可维护性** | 测试覆盖、文档 | 覆盖率 ≥ 80%，文档同步 |

### 审计执行步骤

```
1. 范围确认：核心模块 / 全量代码 / 关键路径
2. 工具扫描：linter / SAST / 依赖审计
3. 人工 review：架构 + 业务规则
4. 报告分级：
   - [CRITICAL] 影响线上 / 阻塞上线
   - [IMPORTANT] 应在上线前修复
   - [MINOR] 后续迭代处理
5. 修复跟踪：每条 CRITICAL/IMPORTANT 有 owner + ETA
6. 重新审计：所有 CRITICAL/IMPORTANT 修复后再过一遍
```

### 审计报告模板

```markdown
# Production Audit Report

**项目:** [name]
**日期:** [date]
**范围:** [全量/核心模块/关键路径]
**审计者:** production-readiness 技能

## 严重程度分布
- CRITICAL: [N] 条
- IMPORTANT: [N] 条
- MINOR: [N] 条

## CRITICAL（必须修复才能上线）
- [ ] [模块/文件:行号] 问题描述 → 修复方案
- ...

## IMPORTANT（应在上线前修复）
- [ ] [模块/文件:行号] 问题描述 → 修复方案
- ...

## MINOR（后续迭代）
- [模块/文件:行号] 问题描述
- ...

## 总结
[1-2 句话 + 优先级建议]
```

### 完整审计模式（548 行）

- 通过 `~/.agents/skills/agent-rules-books/production-code-audit/` 规则文件查阅
- v6.4 变更：原 production-code-audit 完整内容（references 形式）已合并入 SKILL.md 的 Stage 1 章节

---

## Stage 2 · 稳定（Stability · Release It! · Michael Nygard）

> 目标：识别稳定性反模式，应用稳定性模式，故障演练验证

### 2.1 稳定性反模式（必须避免）

| 反模式 | 描述 | 后果 |
|-------|------|------|
| **集成点** | 跨网络/跨进程的脆弱边界 | 单点失败 |
| **连锁反应** | 一个故障扩散全系统 | 雪崩 |
| **级联故障** | 超时未设置 → 资源耗尽 | 服务全挂 |
| **慢响应** | 拖死线程池 | 整个服务慢 |
| **无界队列** | 队列无限增长 | 内存溢出 |
| **无限重试** | 失败时持续重试 | 雪崩 |

### 2.2 稳定性模式（必须采用）

| 模式 | 实现 | 解决什么 |
|------|------|---------|
| **超时** | 所有外部调用必须设超时 | 级联故障 |
| **断路器** | 失败率超阈值时短路 | 连锁反应 |
| **隔舱** | 限制故障爆炸半径 | 雪崩 |
| **稳态处理** | 避免资源累积 | 内存/连接泄漏 |
| **快速失败** | 不要无限重试 | 资源耗尽 |
| **限流** | 限制入站流量 | 过载 |
| **降级** | 依赖不可用时返回部分结果 | 用户体验 |
| **幂等** | 重复调用安全 | 重试安全 |

### 2.3 故障演练

| 演练类型 | 工具 | 验证什么 |
|---------|------|---------|
| **单节点宕机** | 手动 kill | 副本接管 / 服务发现 |
| **网络分区** | toxiproxy / chaos-mesh | 断路器生效 |
| **慢响应注入** | toxiproxy 延迟 | 超时触发 |
| **依赖故障** | 第三方 API mock 失败 | 降级生效 |
| **流量激增** | 压测工具 | 限流生效 |

### 2.4 断路器实现（Python）

```python
from datetime import datetime, timedelta
from enum import Enum

class State(str, Enum):
    CLOSED = "closed"        # 正常
    OPEN = "open"            # 短路
    HALF_OPEN = "half_open"  # 试探

class CircuitBreaker:
    def __init__(self, failure_threshold=5, reset_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.state = State.CLOSED
        self.opened_at = None

    def call(self, func, *args, **kwargs):
        if self.state == State.OPEN:
            if datetime.now() - self.opened_at > timedelta(seconds=self.reset_timeout):
                self.state = State.HALF_OPEN
            else:
                raise CircuitOpenError("Circuit is open")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise

    def on_success(self):
        self.failure_count = 0
        self.state = State.CLOSED

    def on_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = State.OPEN
            self.opened_at = datetime.now()
```

### 2.5 稳定性模式详细（915 行 · Nygard）

通过 `~/.agents/skills/agent-rules-books/release-it/release-it.mini.md` 查阅

---

## Stage 3 · 发布（Release · 渐进式发布策略）

> 目标：用最小爆炸半径的发布模式，配合监控快速发现问题

### 3.1 3 大发布模式

| 模式 | 适用 | 风险 | 回滚速度 |
|------|------|:---:|:---:|
| **蓝绿部署** | 大版本切换、数据库兼容 | 中（瞬时切换） | 立即（切流量） |
| **金丝雀发布** | 高频迭代、A/B 测试 | 低（小比例） | 立即（停止放量） |
| **滚动发布** | 常规迭代、K8s 集群 | 中（逐步替换） | 等待新版本替换完 |

### 3.2 模式选择决策

```
需要瞬时切换 / 大版本？
├─ 是 → 蓝绿部署（资源消耗 2x）
└─ 否 → 能否承受小比例风险？
    ├─ 是 → 金丝雀（推荐：监控 + 渐进放量）
    └─ 否 → 滚动发布（K8s 默认）
```

### 3.3 金丝雀发布流程

```
1. 部署新版本（占比 5%）
2. 监控 30 分钟（错误率 / 延迟 / 业务指标）
3. 验证通过 → 放量到 25% → 监控 30 分钟
4. 验证通过 → 放量到 50% → 监控 30 分钟
5. 验证通过 → 放量到 100%
6. 旧版本标记废弃
7. 全量后 1 天稳定 → 删除旧版本
```

**回滚触发**：
- 错误率 > baseline 1.5x
- p99 延迟 > baseline 1.3x
- 业务核心指标下降

### 3.4 容量规划

- **容量测试**：在生产规模下验证
- **SLA 定义**：99.9% / 99.99% 量化目标
- **监控告警**：黄金指标（延迟 / 流量 / 错误 / 饱和）
- **负载预测**：基于增长模型预留 50% 容量

### 3.5 黄金指标（Google SRE）

| 指标 | 公式 | 告警阈值 |
|------|------|---------|
| **延迟** | p50 / p95 / p99 响应时间 | p99 > SLO |
| **流量** | QPS / RPS | 突增/突降 50% |
| **错误** | 4xx/5xx 比例 | 5xx > 1% |
| **饱和** | CPU/内存/连接池使用率 | > 80% |

---

## 整合使用流程

### 场景 1 · 上线新服务

```
Step 1 (审计): 6 维度全量审计 → 修复 CRITICAL + IMPORTANT
Step 2 (稳定): 识别反模式 → 应用 5+ 稳定性模式 → 故障演练
Step 3 (发布): 容量测试 → 金丝雀 5% → 监控 → 放量 100%
持续: 监控告警 + 定期重审
```

### 场景 2 · 故障后加固

```
Step 1: 复盘故障（root cause）
Step 2: 加固相关路径（应用缺失的稳定性模式）
Step 3: 加故障注入测试
Step 4: 重跑故障演练
Step 5: 总结 ADR（记录决策 + 理由）
```

### 场景 3 · 框架/库升级

```
Step 1 (审计): 评估兼容性（依赖图 + breaking changes）
Step 2 (稳定): 双写 + 蓝绿切换
Step 3 (发布): 蓝绿部署 + 监控
持续: 旧实现并行 1 周后下掉
```

---

## 与其他技能配合

| 场景 | 配合技能 |
|------|---------|
| 架构级审计 | `system-review`（项目/模块级） |
| 代码层审查 | `code-reviewer`（单 PR / 单文件） |
| 性能优化 | `clean-code`（规范）+ `python-web-development`（异步性能） |
| 测试覆盖 | `testing`（覆盖率 + 故障注入测试） |
| 故障处理 | `systematic-debugging`（故障根因） |

---

## 限制

- **完整审计需大量上下文** — 建议分模块进行
- **容量测试需生产规模环境** — staging 不够
- **故障演练有真实风险** — 应在预发环境
- **完整内容在原书规则文件** — production-code-audit 完整内容通过 agent-rules-books/production-code-audit/ 查阅
- **不替代人工判断** — 审计报告是建议，最终决策需用户

---

## 迁移说明

- v6.2 合并前：production-code-audit + release-it 两个独立技能
- v6.2 合并后：production-readiness 超级技能（2 源并排）
- **v6.4 重组**：从并排 → 3 阶段上线流程（审计 → 稳定 → 发布）
- 内联：release-it 30 行要点（稳定性反模式 / 模式 / 发布模式 / 容量规划）已融入 Stage 2/3
- 内联：production-code-audit 6 维度审计清单已融入 Stage 1 章节
- 保留：release-it 通过 agent-rules-books 规则文件引用
- orch 调度表已同步
