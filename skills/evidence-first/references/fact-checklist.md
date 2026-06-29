# 5 项事实清单（详解）

> 本文档是 `evidence-first` 技能 5 项事实清单的详细说明。
> 任何项目分析、比较、评估前，**必须**先完成本清单。

---

## 清单 1：最近 10 次提交（`git log --oneline -10`）

### 命令
```bash
cd <项目根目录>
git log --oneline -10
```

### 必读信息

| 字段 | 含义 | 用法 |
|------|------|------|
| 提交 hash | 唯一标识 | 用于 `git show <hash>` 查看详情 |
| 提交说明 | 改动摘要 | 了解项目当前方向 |
| 日期（可选 `-pretty=format:"%h %ad %s"`） | 提交时间 | 判断最近活跃度 |

### 示例输出
```
a1b2c3d  fix: 修复 skill-hub 路由
e4f5g6h  docs: 添加 v6.0 设计文档
i7j8k9l  merge: v6.0 复合任务编排
```

### 常见解读

- **最近全是 bug fix** → 项目可能不稳定，谨慎乐观
- **最近全是 docs 更新** → 项目可能在整理期
- **最近有大 merge** → 近期有重大变更
- **3 个月没提交** → 项目可能不活跃

---

## 清单 2：项目自我描述（`README.md` / `AGENTS.md`）

### 必读文件

| 文件 | 用途 | 优先级 |
|------|------|:------:|
| `README.md` | 项目自我介绍 | 🟢 必读 |
| `AGENTS.md` | 给 AI 的指令（如果有） | 🟢 必读 |
| `CONTRIBUTING.md` | 贡献指南 | 🟡 可选 |
| `CHANGELOG.md` | 变更日志 | 🟡 可选 |

### 必抓信息

- 项目名称 + 一句话定位
- 核心功能列表
- 当前版本号
- 适用场景 / 不适用场景
- 项目**自己声明**的"是什么 / 不是什么"

### 重要原则

> **项目自己说的话 > 你的推断**。如果项目 README 说"这是一个工具型项目"，不要推断它是"产品级 SaaS"。

---

## 清单 3：版本声明（`package.json` / `pyproject.toml` / `VERSION`）

### 命令

```bash
# Python 项目
cat pyproject.toml | grep -E "^version|^\[project\]" -A 5
# 或
cat setup.py | grep version

# Node.js 项目
cat package.json | grep version

# 通用
ls VERSION 2>/dev/null && cat VERSION
ls CHANGELOG.md 2>/dev/null && head -20 CHANGELOG.md
```

### 必抓信息

- **当前版本号**（如 6.0 / 6.1 / 1.0.0）
- **版本号语义**（SemVer: major.minor.patch）
- **是否有 base_compat 字段**（向后兼容声明）
- **CHANGELOG 第一行**（最近变更主题）

### 重要原则

> **版本号是项目"自我声明的状态"**。v6.1 ≠ v1.0，v5.4 不一定是"老版本"（可能是基线）。

---

## 清单 4：最近 changelog / 设计文档（`docs/`）

### 必读文件

```bash
ls docs/
# 找出最近的设计文档（按文件名日期）
ls -lt docs/ | head -5
```

### 必抓信息

- **最近的设计决策是什么**
- **未来规划是什么**
- **哪些是已实现 / 未实现 / alpha / 计划中**
- **是否有"决策记录"或"ADR"（Architecture Decision Records）**

### 重要原则

> **设计文档 = 项目的"集体记忆"**。在 v6.0 设计文档里说"v5.4 是基线"，比任何推断都权威。

---

## 清单 5：main 分支活跃度（`git log --since="3 months ago" --oneline | wc -l`）

### 命令

```bash
cd <项目根目录>
git log --since="3 months ago" --oneline | wc -l
```

### 活跃度判断

| 3 个月提交数 | 状态 | 解读 |
|------------|------|------|
| 0 | 🔴 停滞 | 项目可能不活跃或有 fork |
| 1-5 | 🟡 低活跃 | 维护期 |
| 6-20 | 🟢 健康 | 正常开发 |
| 20+ | 🚀 高活跃 | 快速迭代期 |

### 重要原则

> **活跃度不等于成熟度**。3 个月没提交可能是"项目稳定，不需要改"，也可能是"项目已死"——需要结合其他事实判断。

---

## 事实清单使用流程

```
1. 打开终端，cd 到项目根目录
2. 依次跑 5 项命令（或合并跑）
3. 把结果整理成"事实清单"段
4. 标注每条 [F]
5. 进入分析论述
```

### 一键脚本（可选）

```bash
# 一键生成事实清单
cat << 'EOF' > /tmp/fact-check.sh
echo "=== 1. 最近 10 次提交 ==="
git log --oneline -10
echo ""
echo "=== 2. 项目自述（README 前 20 行）==="
head -20 README.md 2>/dev/null || echo "（无 README）"
echo ""
echo "=== 3. 版本声明 ==="
cat pyproject.toml 2>/dev/null | grep -E "version|name" | head -5
cat package.json 2>/dev/null | grep -E "version|name" | head -5
echo ""
echo "=== 4. 最近设计文档 ==="
ls -lt docs/*.md 2>/dev/null | head -3
echo ""
echo "=== 5. 3 个月活跃度 ==="
git log --since="3 months ago" --oneline | wc -l
EOF
bash /tmp/fact-check.sh
```

---

## 反模式（禁止）

| 反模式 | 后果 |
|--------|------|
| 跳过清单直接论述 | 可能基于错误假设 |
| 用"通常""一般"代替事实 | 套用通用经验，掩盖事实不清 |
| 只查 README 不查 git | 看不到项目真实活跃度 |
| 只看代码不看设计文档 | 错过"设计意图"和"未实现功能" |

---

## 自检问题

完成清单后自问：

- [ ] 5 项都查了吗？
- [ ] 每条结果都标注了 [F] 吗？
- [ ] 有没有基于"印象""通常"的推断？（如有，标注 [H]）
- [ ] 事实之间是否矛盾？（如版本号 v6.0 但 CHANGELOG 写 v5.4）
- [ ] 是否需要进一步查证？

**5 项都查完 + 自检通过 = 可以进入论述**。
