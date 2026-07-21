---
description: 智能 stage + commit（规则过滤 untracked，防漏提交）
allowed-tools: Bash
---

使用本地脚本完成智能提交（**禁止**自行拼 `git add` 文件列表；**禁止**用模型决定 add 哪些文件）。

```bash
python3 scripts/smart_commit.py -m "<message>" [--dry-run] [--push]
```

若当前不在仓库根目录，先 `cd` 到 git 根，或：

```bash
python3 scripts/smart_commit.py --cwd <repo> -m "<message>"
```

## 参数

- `-m` / `--message`：**必填** commit message
- `--dry-run`：只打印 `WILL ADD` / `SKIPPED`，不改仓库
- `--push`：commit 成功后再 `git push`（默认不推）

## 行为

1. `git status --porcelain` 识别 modified / deleted / untracked  
2. 过滤：硬黑名单 + 轻量启发式 + 可选 `.loopengine-commit-ignore`  
3. `git add` 通过列表 → `git commit -m ...`  
4. 打印可审计清单（`WILL ADD` / `SKIPPED` / `COMMIT`）

详规：`docs/2026-07-21-smart-git-commit-design.md`
