# docs/legacy/ — 旧版本兼容代码（仅做迁移参考）

> **本目录代码已被新版本替代，请勿在新部署中使用。**

## 文件

| 文件 | 替代方案 | 删除原因 |
|------|---------|---------|
| `zcode-mcp-ensure.v1.0.2.sh` | `install.sh` Step 4 (`write_zcode_desktop_config`) | 与 install.sh Step 4 重复 ~70 行；install.sh 已自包含 MCP 探测 + 写 ~/.zcode/cli/config.json + 兼容性处理 |

## 历史

- **v1.0.2 (2026-06-30)**：因 ZCode 桌面版 MCP "重启丢失"问题，临时引入 zcode-mcp-ensure.sh 作为"自愈脚本"
- **v1.1.0 (2026-07-01)**：install.sh Step 4 已吸收自愈逻辑；delete zcode-mcp-ensure.sh，合并 ~70 行重复代码

## 升级指引

如果你之前用 v1.0.2 + zcode-mcp-ensure.sh，升级到 v1.1.0：

```bash
# 1. 跑新 install.sh（Step 4 自动覆盖 ~/.zcode/cli/config.json）
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash

# 2. 删除旧自愈脚本（可选）
rm -f ~/.local/bin/zcode-mcp-ensure.sh
```

## 相关 commit

- `5739f94` fix(install): CRITICAL+IMPORTANT 修复 7 项（2026-06-30）
- `90e192a` feat(install): v1.1.0 全面同步 + plugin 模板+overlay（2026-07-01）
