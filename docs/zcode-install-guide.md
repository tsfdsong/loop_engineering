# ZCode 桌面版 LoopEngine 安装指南

> 适用版本：ZCode 桌面版 v3.1.8+
> 最后更新：2026-06-28
> 当前 LoopEngine 版本：**v1.0.1**（新增 MCP 红线规则 + 一键更新脚本）
> 基于实测验证的安装流程

---

## 一、安装原理

ZCode 桌面版的插件面板从**内置包目录**加载插件，而非 CLI 插件目录。完整注册链路：

```
内置包目录（glm/packages/loopengine-plugin/）
  → CLI 缓存（cache/zcode-plugins-official/loopengine/1.0.0/）
    → marketplace 注册（marketplace.json）
      → config 启用（config.json）
        → data 目录（data/loopengine@zcode-plugins-official）
          → 插件面板可见 ✅
```

**关键教训**：缓存路径必须与 marketplace 的 `cachePath` 一致，且 marketplace 必须是 `zcode-plugins-official`（桌面版只识别此市场）。

---

## 🔴 MCP 红线规则（v1.0.1 核心更新）

> **这是 v1.0.1 最重要的更新。安装/更新后，AI 代理在所有会话中将强制执行此规则。**

### 规则内容

| 规则 | 内容 |
|------|------|
| **适用范围** | 修改代码、调研代码、解释代码、分析架构、查找定义/引用——**只要目的是"理解代码"** |
| **标准流程** | `get_repo_map`（定位项目全景）→ `get_file_outline`（理解文件结构）→ `search_symbols`（找关联符号）→ `Read`（仅精确读取目标行） |
| **唯一例外** | MCP 工具全部不可用（报错/超时）、文件小于 50 行、已通过 MCP 定位需精确读取某几行 |
| **违规判定** | 连续 3 次以上直接 Read 全文件而未使用任何 MCP 工具 → 红线违规 |
| **自查机制** | 每次会话结束后自查：MCP 工具调用次数应 ≥ Read 调用次数 |

### 规则生效层级

| 层级 | 文件 | 生效范围 |
|------|------|---------|
| 全局 | `~/.zcode/AGENTS.md` | 所有 ZCode 会话 |
| 项目 | `loop_engineering/AGENTS.md` | 本项目工作区 |
| 调度 | `skill-hub/SKILL.md` | 所有加载了 skill-hub 的会话 |
| 编排 | `go/SKILL.md` | `/go` 命令执行时 |
| 执行 | `loop/SKILL.md` | `/loop` 命令执行时 |

### 可用 MCP 工具速查

| 工具 | 用途 | Token 节省 |
|------|------|:--:|
| `mcp__jcodemunch__get_repo_map` | 项目结构全景图（符号级） | ~80% |
| `mcp__jcodemunch__get_file_outline` | 文件符号大纲（函数/类/变量列表） | ~85% |
| `mcp__jcodemunch__search_symbols` | 语义搜索符号（按名称/签名/摘要） | ~90% |
| `mcp__jcodemunch__get_file_tree` | 目录树（可选含文件摘要） | ~95% |
| `mcp__jcodemunch__find_references` | 查找符号的所有引用位置 | ~85% |
| `mcp__jcodemunch__get_blast_radius` | 修改影响面分析 | ~90% |

---

## 二、安装步骤

### 步骤 1：克隆到内置包目录

```powershell
# PowerShell（管理员）
git clone https://github.com/tsfdsong/loop_engineering.git "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
```

验证：
```powershell
ls "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\skills\" | Measure-Object | Select-Object -ExpandProperty Count
# 应输出: 53
```

### 步骤 2：复制到 CLI 缓存

```powershell
$src = "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
$dst = "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0"
mkdir -p $dst
xcopy "$src\*" "$dst\" /E /I /Y
```

验证：
```powershell
ls "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0\skills\" | Measure-Object | Select-Object -ExpandProperty Count
# 应输出: 53
```

### 步骤 3：创建 data 目录

```powershell
mkdir "$env:USERPROFILE\.zcode\cli\plugins\data\loopengine@zcode-plugins-official"
```

### 步骤 4：注册 marketplace

编辑 `%USERPROFILE%\.zcode\cli\plugins\marketplaces\zcode-plugins-official\marketplace.json`，在 `plugins` 数组中添加：

```json
{
  "cachePath": "C:\\Users\\<你的用户名>\\.zcode\\cli\\plugins\\cache\\zcode-plugins-official\\loopengine\\1.0.0",
  "name": "loopengine",
  "source": "filesystem",
  "version": "1.0.0"
}
```

> ⚠️ `cachePath` 必须是**绝对路径**，且反斜杠需要双写（`\\`）。

完整文件示例（含 7 个插件）：

```json
{
  "name": "zcode-plugins-official",
  "plugins": [
    { "cachePath": "...", "name": "android-emulator", "source": "filesystem", "version": "0.1.0" },
    { "cachePath": "...", "name": "document-skills", "source": "filesystem", "version": "0.1.0" },
    { "cachePath": "...", "name": "ios-simulator", "source": "filesystem", "version": "0.1.0" },
    { "cachePath": "...", "name": "loopengine", "source": "filesystem", "version": "1.0.1" },
    { "cachePath": "...", "name": "restore-legacy-sessions", "source": "filesystem", "version": "0.1.0" },
    { "cachePath": "...", "name": "skill-creator", "source": "filesystem", "version": "0.1.0" },
    { "cachePath": "...", "name": "superpowers", "source": "filesystem", "version": "5.1.0" }
  ],
  "version": 1
}
```

### 步骤 5：启用插件

编辑 `%USERPROFILE%\.zcode\cli\config.json`，在 `plugins.enabledPlugins` 中添加：

```json
"loopengine@zcode-plugins-official": true
```

完整示例：

```json
{
  "plugins": {
    "enabledPlugins": {
      "superpowers@zcode-plugins-official": true,
      "loopengine@zcode-plugins-official": true
    }
  }
}
```

### 步骤 6：重启 ZCode

完全退出 ZCode 桌面版（系统托盘也要退出），重新启动。

---

## 三、验证安装

### 3.1 插件面板

打开 ZCode → 设置 → 插件管理，应看到：

> **loopengine** v1.0.1 — LoopEngine 循环工程全家桶

### 3.2 功能验证

在 ZCode 会话中输入：

```
/loop 验证安装，确认插件可用
```

或直接使用 skill-hub：

```
帮我分析一下这个项目的架构
```

如果 skill-hub 自动调度到合适的技能，说明安装成功。

### 3.3 注册链路检查

```powershell
# 检查 5 个关键位置
$checks = @(
    "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\.zcode-plugin\plugin.json",
    "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0\.zcode-plugin\plugin.json",
    "$env:USERPROFILE\.zcode\cli\plugins\data\loopengine@zcode-plugins-official"
)
foreach ($c in $checks) {
    if (Test-Path $c) { Write-Host "✅ $c" -ForegroundColor Green }
    else { Write-Host "❌ $c" -ForegroundColor Red }
}
```

---

## 四、故障排查

### 4.1 插件面板不显示

| 症状 | 排查 |
|------|------|
| 重启后插件面板无 loopengine | 检查 marketplace.json 的 `cachePath` 是否正确（绝对路径 + 双反斜杠） |
| | 检查 config.json 是否启用 `loopengine@zcode-plugins-official` |
| | 检查缓存目录是否存在于 `cache/zcode-plugins-official/loopengine/1.0.0/` |
| | 检查 data 目录是否已创建 |

### 4.2 技能无法加载

| 症状 | 排查 |
|------|------|
| skill-hub 不工作 | 检查缓存目录中 `skills/` 是否包含 53 个技能目录 |
| | 检查 `.zcode-plugin/plugin.json` 中 `"skills": "skills"` 字段是否存在 |

### 4.3 常见错误

**错误 1：缓存路径在 `loopengine-local` 下**
```
症状：marketplace 注册了 zcode-plugins-official，但缓存在 loopengine-local
修复：复制缓存到 cache/zcode-plugins-official/loopengine/1.0.0/
```

**错误 2：marketplace.json 中 loopengine 条目丢失**
```
症状：重启后 marketplace.json 被还原
原因：ZCode 可能在启动时重写 marketplace.json
修复：重启后再次添加，或在 ZCode 关闭时编辑
```

**错误 3：config.json 被还原**
```
症状：enabledPlugins 中 loopengine 条目消失
原因：ZCode 可能在关闭时保存了旧状态
修复：关闭 ZCode → 编辑 config.json → 启动 ZCode
```

---

## 五、卸载

```powershell
# 1. 删除内置包
rm -r "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"

# 2. 删除缓存
rm -r "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine"

# 3. 删除 data 目录
rm -r "$env:USERPROFILE\.zcode\cli\plugins\data\loopengine@zcode-plugins-official"

# 4. 编辑 marketplace.json，移除 loopengine 条目
# 5. 编辑 config.json，移除 "loopengine@zcode-plugins-official": true
# 6. 重启 ZCode
```

---

## 六、与 Superpowers 的对比

| 维度 | superpowers | loopengine |
|------|:--:|:--:|
| 安装方式 | ZCode 安装程序预打包 | 手动 git clone |
| 内置包目录 | `glm/packages/superpowers-plugin/` | `glm/packages/loopengine-plugin/` |
| 缓存路径 | `cache/zcode-plugins-official/superpowers/5.1.0/` | `cache/zcode-plugins-official/loopengine/1.0.0/` |
| marketplace | `zcode-plugins-official` | `zcode-plugins-official` |
| 技能数 | 14 | 50 |
| hooks | ✅ SessionStart | ✅ SessionStart（注入 skill-hub） |
| MCP 红线 | ❌ 无 | ✅ 全局强制执行 |
| 更新方式 | 随 ZCode 升级 | `update.sh` 一键更新 / 手动 git pull |

---

## 七、更新

### 7.1 一键更新（推荐）

```bash
# 方式 1：在线更新
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/update.sh | bash

# 方式 2：install.sh --update
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash -s -- --update
```

### 7.2 手动更新

```powershell
cd "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
git pull

# 同步到缓存
xcopy "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\*" "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0\" /E /I /Y

# 重启 ZCode
```

### 7.3 更新内容说明

每次更新可能包含以下类型的变更：

| 变更类型 | 说明 | 是否需要重启 ZCode |
|------|------|:--:|
| 技能内容更新 | SKILL.md 修改（如 MCP 红线规则） | ✅ 是（SessionStart hook 在启动时加载） |
| 新增技能 | skills/ 下新增目录 | ✅ 是 |
| 脚本更新 | go/scripts/*.py 修改 | ✅ 是（/go 执行时重新加载） |
| 文档更新 | docs/*.md 修改 | ❌ 否 |

**v1.0.1 更新内容**：
- 🔴 **新增 MCP 红线规则**：任何理解代码的操作必须先用 MCP 工具，省 ~90% token
- 📝 适用范围从"修改代码前"扩展为"所有理解代码的操作"
- ⚡ 标准流程：`get_repo_map` → `get_file_outline` → `search_symbols` → `Read`（仅精确行）
- 🚨 违规判定：连续 3 次直接 Read 全文件未用 MCP = 红线事故
- 🆕 新增 `update.sh` 一键更新脚本

### 7.4 验证更新是否生效

```
源仓库 (GitHub)  ← 红线规则在此定义
  ↓ git pull
内置包目录 (glm/packages/loopengine-plugin/)
  ↓ xcopy 同步
CLI 缓存 (cache/zcode-plugins-official/loopengine/1.0.0/)
  ↓ SessionStart hook 注入
AI 会话生效 ✅
```

**关键**：更新后必须**重启 ZCode 桌面版**，因为 SessionStart hook 在启动时加载技能内容到内存。

### 7.4 验证更新是否生效

打开新的 ZCode 会话，发送：
```
告诉我 MCP 红线规则是什么
```

如果 AI 代理能准确回答红线规则的内容（适用范围、标准流程、违规判定），说明更新已生效。

### 7.5 更新链路说明
