# docs/legacy/ — 旧版本兼容代码（仅做迁移参考）

> **本目录代码已被新版本替代，请勿在新部署中使用。**
> v1.2.0 起，目录中所有脚本已删除（v1.1.0 移入 + v1.2.0 删除）；本 README 仅作为历史迁移参考。

## 历史脚本（已删除）

| 脚本 | 替代方案 | 删除版本 |
|------|---------|---------|
| `zcode-mcp-ensure.v1.0.2.sh` | `install.sh` Step 4 (`write_zcode_desktop_config`) | v1.2.0（v1.1.0 已移入本目录作为 deprecation marker）|
| `update.sh` | `install.sh` 智能模式（含 Step 0 自动判断 + `--dry-run` / `--force` 参数）| v1.2.0（已合并到 install.sh）|

## 升级指引

### 从 v1.0.2 升级到 v1.2.0

```bash
# 1. 重跑 install.sh（智能模式自动处理）
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash

# 2. 删除旧 zcode-mcp-ensure 自愈脚本（可选）
rm -f ~/.local/bin/zcode-mcp-ensure.sh
```

### 从 v1.1.0 升级到 v1.2.0

```bash
# 重跑 install.sh 即可（智能模式自动判断）
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

## 相关 commit

- `5739f94` fix(install): CRITICAL+IMPORTANT 修复 7 项（2026-06-30）
- `90e192a` feat(install): v1.1.0 全面同步 + plugin 模板+overlay（2026-07-01）
- `6ae5f0c` feat(install): v1.2.0 一体化（首次安装 + 版本更新合一，update.sh 合并）
- `77e740a` docs(release): v1.2.0 详细 release notes
