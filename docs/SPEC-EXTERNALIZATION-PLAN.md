# Plan: spec/plan 完全外部化（LoopEngine v2.1）

> **状态**: 用户已批准（`/orch 4` + 选项 D "完全外部化"）
> **日期**: 2026-07-02
> **关联 issue**: system-review 2026-07-02 🟢 #11 (spec 入库策略)

---

## 1. 目标

将 design docs（specs / plans / 后续 ADRs）从主仓 `loop_engineering` 剥离，
独立仓库 `loop_engineering_specs` 管理。解决 `.gitignore` L12 决策不传承问题。

---

## 2. 默认决策（用户跳过 sub-decision，采用合理默认值）

| # | 子决策 | 默认值 | 理由 |
|---|---|---|---|
| 1 | 外部仓库名 | `loop_engineering_specs` | 与主仓名家族一致；`specs` 复数表明多文档 |
| 2 | 本地缓存路径 | `~/.loopengine/specs/` | 与技能目录平级；用户级不污染项目 |
| 3 | 测试 fallback | skip with warning | CI 不崩溃；用户可在 CI 强校验时打开 |
| 4 | install.sh 默认行为 | 默认 clone + `--skip-specs` flag | 保持最佳体验；可显式跳过 |

---

## 3. 影响范围

### 3.1 新建文件（主仓，tracked）

| 文件 | 内容 |
|---|---|
| `docs/spec-repo-link.md` | 外部仓库 URL + 克隆路径 + 同步说明 + 故障排查 |
| `docs/SPEC-EXTERNALIZATION-PLAN.md` | 本文件（迁移完后删除） |

### 3.2 修改文件（主仓）

| 文件 | 修改 |
|---|---|
| `.gitignore` | 删除 `docs/superpowers/` 行（不再 local） |
| `AGENTS.md` | 顶部加 1 段说明外部仓库 |
| `README.md` | "设计文档" section 加外部仓库链接 |
| `install.sh` | 加 `install_specs()` 函数 + `--skip-specs` / `--with-specs` / `--specs-source <path>` flags |
| `tests/test_orch_golden_traces.py` | spec 引用改读 `~/.loopengine/specs/` + fallback |

### 3.3 外部仓库（用户手动创建 + push）

```
loop_engineering_specs/
├── README.md
├── specs/
│   ├── 2026-06-30-summary-redline-design.md
│   ├── 2026-07-01-mcp-redesign.md
│   ├── 2026-07-02-orch-v2-c-lite-design.md
│   └── 2026-07-02-web-test-orchestration.md
└── plans/
    └── 2026-07-02-orch-v2-implementation.md
```

> **AI 无法直接创建 GitHub 仓库**。本地会准备初始文件 `loop_engineering_specs_init/` 目录，待用户 push。

### 3.4 不动文件

- `skills/orch/references/golden-traces/*.json` 的 `acceptance_criteria_ref` 仍引用 `spec §X.Y`（章节编号稳定，不依赖路径）

### 3.5 迁移 / 删除

- `docs/superpowers/specs/*.md` → 复制到外部 `specs/`
- `docs/superpowers/plans/*.md` → 复制到外部 `plans/`
- 主仓 `docs/superpowers/` 目录：**保留 7 天作为本地缓存**（gitignored），便于 cross-reference；7 天后由用户手动删除

---

## 4. 执行步骤

### Step 1：本地创建外部仓库初始文件
- 路径：`/tmp/loop_engineering_specs_init/`
- 复制现有 `docs/superpowers/specs/*.md` 与 `plans/*.md`
- 加外部仓 README.md（说明用途 + 同步机制）

### Step 2：主仓调整
- 改 `.gitignore`：删除 `docs/superpowers/` 行
- 改 `AGENTS.md`：加 1 段"设计文档外部化"
- 改 `README.md`：加"设计文档" section
- 新建 `docs/spec-repo-link.md`

### Step 3：install.sh 改造
- 加 `install_specs()` 函数（git clone `loop_engineering_specs` → `~/.loopengine/specs/`）
- 加 3 个 flag：`--skip-specs` / `--with-specs` / `--specs-source <path>`
- 默认行为：尝试 clone，失败则警告但不阻塞

### Step 4：测试调整
- `test_spec_decision_8_acknowledges_parallel_investigation_exception`
  - 优先读 `~/.loopengine/specs/specs/2026-07-02-orch-v2-c-lite-design.md`
  - 备选读 `docs/superpowers/specs/...md`（本地缓存）
  - 两者都无 → skip with warning
- 加 `LOOPENGINE_REQUIRE_SPECS=1` 环境变量控制 fallback 行为

### Step 5：验证
- `python -m unittest tests.test_orch_golden_traces tests.test_orch_v2_assets` → 28/28 通过
- `bash install.sh --help` → 正确显示新 flag
- `bash install.sh --dry-run --with-specs` → 显示 clone 步骤
- `bash install.sh --dry-run --skip-specs` → 不显示 clone 步骤

### Step 6：清理
- 删除主仓 `docs/SPEC-EXTERNALIZATION-PLAN.md`（已迁移到外部）
- 保留 `docs/superpowers/` 作 7 天缓存（gitignored）

---

## 5. 风险与缓解

| 风险 | 缓解 |
|---|---|
| 外部仓库未创建 | install.sh 默认 clone 失败 → 警告但不阻塞；主仓 + 测试可独立运行 |
| 跨仓引用断裂 | tests 加 fallback（先外后内再 skip） |
| clone 网络失败 | install.sh 显示清晰错误 + 提示手动 `git clone` |
| 用户无 GH 账号 | 提供 `--specs-local <path>` flag 指向本地路径 |
| spec/plan 同步漂移 | 在 `docs/spec-repo-link.md` 标注同步机制（manual PR 流程） |

---

## 6. 不做项

- ❌ 不自动 sync spec 内容（manual PR 流程，由 spec 作者 push）
- ❌ 不改 docs/ 之外的其他目录
- ❌ 不重命名现有 spec/plan 文件（保留日期前缀，便于追溯）
- ❌ 不引入 sub-module（submodule 太重，普通 git clone 更轻）

---

## 7. 验收标准

1. ✅ `~/.loopengine/specs/` 含全部 5 个 spec + 1 个 plan
2. ✅ 主仓 `docs/superpowers/` 在 `.gitignore` 已删除
3. ✅ install.sh 默认 clone 外部仓库
4. ✅ 28/28 测试通过
5. ✅ 用户手动 push 外部仓库后，全新 install 流程端到端可用

---

## 8. 下一步

用户手动创建外部仓库（GitHub UI 或 `gh repo create`）后：
1. 推送 `loop_engineering_specs_init/` 内容
2. 删除主仓 `docs/superpowers/`（7 天缓存期后）
3. 在主仓 README 加 `loop_engineering_specs` badge