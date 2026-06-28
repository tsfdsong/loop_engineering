# ZCode 桌面版 LoopEngine 安装指南

> 适用版本：ZCode 桌面版 v3.1.8+
> 最后更新：2026-06-28
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

## 二、安装步骤

### 步骤 1：克隆到内置包目录

```powershell
# PowerShell（管理员）
git clone https://github.com/tsfdsong/loop_engineering.git "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
```

验证：
```powershell
ls "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\skills\" | Measure-Object | Select-Object -ExpandProperty Count
# 应输出: 55
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
# 应输出: 55
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
    { "cachePath": "...", "name": "loopengine", "source": "filesystem", "version": "1.0.0" },
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

> **loopengine** v1.0.0 — LoopEngine 循环工程全家桶

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
| skill-hub 不工作 | 检查缓存目录中 `skills/` 是否包含 55 个技能目录 |
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
| 技能数 | 14 | 55 |
| hooks | ✅ SessionStart | ❌（非必须） |
| 更新方式 | 随 ZCode 升级 | 手动 git pull |

---

## 七、更新

```powershell
cd "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"
git pull

# 同步到缓存
xcopy "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\*" "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0\" /E /I /Y

# 重启 ZCode
```
