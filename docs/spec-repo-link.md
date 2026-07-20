# 设计文档外部仓库

> **重要变更** (2026-07-02): LoopEngine 的设计文档（spec / plan / ADR）已从主仓剥离，独立仓库管理。
> **2026-07-20**: 主仓安装入口已改为 `install.py`；specs 同步不再作为 install 默认步骤（可手动 clone）。

## 外部仓库

| 项 | 值 |
|---|---|
| 仓库名 | `loop_engineering_specs` |
| URL | `https://github.com/tsfdsong/loop_engineering_specs` |
| 用途 | 存放所有 design docs（spec / plan / ADR） |
| 同步机制 | 手动 `git clone` 到本地（可选） |

## 本地缓存路径

- **克隆目标**: `~/.loopengine/specs/`
- **结构**：
  ```
  ~/.loopengine/specs/
    ├── README.md
    ├── specs/
    │   └── YYYY-MM-DD-<topic>-design.md
    └── plans/
        └── YYYY-MM-DD-<topic>-implementation.md
  ```

## 可选同步

```bash
mkdir -p ~/.loopengine
git clone https://github.com/tsfdsong/loop_engineering_specs ~/.loopengine/specs
# 更新：cd ~/.loopengine/specs && git pull
```

若 clone 失败：不影响 `python3 install.py install` 主流程。

## 引用约定

主仓代码 / 文档引用 spec 时使用 `spec §X.Y` 章节编号（不依赖文件路径），
例如：
- `golden-traces/*.json` 字段 `acceptance_criteria_ref: "spec §15.3"`
- `tests/*.py` 中 spec 章节断言

## 故障排查

| 症状 | 解决 |
|---|---|
| `~/.loopengine/specs/` 为空 | 手动 `git clone`（见上） |
| spec 内容过时 | `cd ~/.loopengine/specs && git pull` |
| 找不到外部仓 | 检查 `gh repo view tsfdsong/loop_engineering_specs` 是否存在 |
| 测试 `test_spec_decision_8_*` skip | 设 `LOOPENGINE_REQUIRE_SPECS=1` 强制要求 spec |

## 迁移历史

- **2026-07-02**: 从 `docs/superpowers/` (主仓 gitignored) 迁出到独立仓库
- 见 `docs/SPEC-EXTERNALIZATION-PLAN.md` 完整 plan（迁移完成后会删除）
