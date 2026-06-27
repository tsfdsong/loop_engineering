---
name: skill-publisher
description: 将本地技能发布到平台。当用户说"发布技能/上传技能/把技能发到平台"时使用。支持指定目录或 .zip 压缩包直接发布，内置格式校验与中文错误提示。可选查重和扫描本地已装技能。
metadata:
  kind: tool
  category: productivity
---

# skill-publisher

把本地技能发布到平台的元技能。

## 何时使用

- 用户说"发布技能"、"上传技能"、"把 xxx 发布到平台"
- 用户说"把这个目录发布上去"、"把这个 zip 发到平台"
- 用户说"扫描本地技能"（低频，用于发现已安装的技能）

## 脚本

所有脚本在 `scripts/` 目录下，用 `python` 运行。脚本依赖 `pyyaml`。

### publish.py — 发布技能（核心）

```bash
# 发布一个目录
python scripts/publish.py ~/my-project/my-skill

# 发布一个 zip 压缩包
python scripts/publish.py ~/Downloads/my-skill.zip

# 指定版本号和分类
python scripts/publish.py ~/my-skill --version 2.0.0 --category devops
```

参数：

- `path` — 技能目录路径或 `.zip` 压缩包（必填）
- `--slug` — slug（默认从 SKILL.md 的 name 读取）
- `--version` — 版本号（默认 1.0.0）
- `--category` — 分类（默认 general）
- `--kind` — 类型 tool/agent/framework（默认 tool）

zip 模式下：脚本会校验包内包含 SKILL.md 且格式正确，通过后直接上传该 zip，不重新打包。目录模式下：自动打包为 zip 后上传。

### search.py — 查重（可选）

```bash
python scripts/search.py "技能名"
```

发布前可选查重，避免 slug 冲突。

### scan.py — 扫描本地已装技能（低频）

```bash
python scripts/scan.py                    # 扫描 ~/.agents/skills 等默认目录
python scripts/scan.py --dir ~/my-skills  # 额外扫描自定义路径
```

输出 JSON 数组，每个技能包含 path/name/description/file_count/valid/errors。

### config.py — Token 配置

| 命令 | 说明 |
|---|---|
| `python scripts/config.py --check` | 检查是否已配置 Token（退出码 0=已配） |
| `python scripts/config.py set --token <token> --url <平台地址>` | 保存 Token 和平台地址 |
| `python scripts/config.py show` | 查看当前配置 |
| `python scripts/config.py clear` | 清除 Token |

### 退出码约定

- 0 = 成功
- 1 = 校验/业务失败（可修复后重试）
- 2 = 认证失败（需重新配置 Token）

## 首次使用引导

当用户首次说"发布技能"时，按以下顺序操作：

1. 运行 `python scripts/config.py --check`
2. 若返回码为 1（未配置），向用户展示引导：

```
📋 首次使用，需要配置 API Token（仅一次）：

1. 浏览器打开 https://test-yimiaihub.yimidida.com/yimiaihub/dashboard/settings
   登录后进入「账号设置」

2. 页面拉到「API Token 管理」→ 点击「生成新 Token」

3. 复制 token，在此对话中告诉我
   格式：aih_xxxxxxxxxxxxxxxx

4. 同时告诉我平台地址：
   https://test-yimiaihub.yimidida.com/yimiaihub

🔹 Token 将安全保存在本地 ~/.ai-hub/credentials
```

3. 用户提供 token 和平台地址后，运行：
   ```
   python scripts/config.py set --token <token> --url <平台地址>
   ```
4. 继续执行发布操作

## 推荐工作流

1. `publish.py <路径或zip>` — 发布（核心场景）
2. `search.py <name>` — 可选：发布前查重
3. `scan.py` — 可选：发现本地已装技能

## 错误处理

脚本输出的中文错误均来自平台校验，包含具体的字段和原因，可直接展示给用户。如有"认证失败"提示，引导用户重新生成 Token。
