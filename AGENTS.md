# LoopEngine — 循环工程全家桶

## 🔴 MCP 红线规则（本项目最高优先级 · 不可违反）

> **任何需要理解代码结构的操作，必须先用 MCP 工具，禁止直接 Read 全文件。**
> 此规则适用于本项目（loop_engineering）的所有开发、调研、分析工作。

### MCP 三件套（节省 80% token）

LoopEngine 依赖三个 MCP 工具实现 token 优化：

| 工具 | 类型 | 核心能力 | Token 节省 |
|------|------|---------|:---:|
| **jCodeMunch-MCP** | Python | AST 符号级代码检索 | **95%** |
| **Repomix** | Node.js | 代码库打包 + 结构压缩 | **70%** |
| **Headroom-ai** | Python | 上下文压缩层 | **60-95%** |

详细安装配置见 `docs/mcp-setup-guide.md`。

### 典型场景对比

| 场景 | ZCode 自带工具（Glob+Grep+Read） | MCP 三件套 | 节省 |
|------|----------------------|--------|:---:|
| 阅读单个函数（300 行） | ~800 token | ~40 token | **95%** |
| 理解项目架构 | ~1,200,000 token | ~370,000 token | **69%** |
| 长会话（50 轮） | ~40,000 token | ~12,000 token | **70%** |
| pytest 输出（200 行） | ~1,200 token | ~200 token | **83%** |
| **典型场景平均** | — | — | **~80%** |

### 适用范围
- 修改代码、调研代码、解释代码、分析架构
- 查找函数/类/变量定义、查找引用位置
- 了解项目结构、浏览目录、理解文件内容
- **只要目的是"理解代码"，就必须 MCP 优先**

### 标准流程
```
get_repo_map → get_file_outline → search_symbols → Read（仅精确行）
```

### MCP 工具速查

| MCP 工具 | 用途 | Token 节省 |
|------|------|:--:|
| `mcp__jcodemunch__get_repo_map` | 项目结构全景图 | ~80% |
| `mcp__jcodemunch__get_file_outline` | 文件符号大纲 | ~85% |
| `mcp__jcodemunch__search_symbols` | 语义搜索符号 | ~90% |
| `mcp__jcodemunch__get_file_tree` | 目录树浏览 | ~95% |
| `mcp__jcodemunch__find_references` | 查找引用位置 | ~85% |
| `mcp__jcodemunch__get_blast_radius` | 修改影响面分析 | ~90% |
| `mcp__repomix__pack_codebase` | 打包代码库 | ~70% |
| `mcp__headroom__headroom_compress` | 压缩大段内容 | ~95% |

### 唯一例外
- MCP 工具全部不可用（报错/超时）
- 文件小于 50 行
- 已通过 MCP 定位，需要精确读取某几行

### 违规判定
- 连续 3 次以上直接 Read 全文件而未使用任何 MCP 工具 → 红线违规
- 每次会话结束后自查：MCP 工具调用次数应 ≥ Read 调用次数

### PATH 修复指引（如 MCP 命令找不到）

如果 `jcodemunch-mcp` 或 `headroom` 命令找不到，是因为 pip 安装到了 Scripts 目录但未加入 PATH：

- **Windows**: 把 `C:\Users\<user>\AppData\Roaming\Python\Python<ver>\Scripts\` 加入系统 PATH
- **Linux/macOS**: `export PATH="$HOME/.local/bin:$PATH"`（写入 ~/.bashrc / ~/.zshrc）

或修改项目根 `.mcp.json` 用绝对路径（详见 `docs/mcp-setup-guide.md` 第四章）。

---

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 55 个技能的开发引擎全家桶。

**Below is the full content of your 'loopengine:skill-hub' skill —— 你的技能调度中心。收到任何任务后，先通过 skill-hub 自动匹配最合适的技能。**

skill-hub 会在收到任务时自动分析意图，从 55 个技能中调度最精准的一个。涵盖：编码、架构、重构、测试、调试、API、安全、数据库、CI/CD、规划执行、产品管理、循环工程等全领域。

## 安装方式

### 一键安装
```bash
curl -fsSL https://raw.githubusercontent.com/tsfdsong/loopengine/main/install.sh | bash
```

### 各平台原生命令
- **ZCode**: `zcode plugin install tsfdsong/loopengine`
- **ZCode 桌面版**: 见下方「ZCode 桌面版手动安装」章节
- **Claude Code**: `/plugin install loopengine@tsfdsong`
- **Codex**: 从插件市场搜索 "loopengine"
- **Cursor**: `/add-plugin tsfdsong/loopengine`
- **Gemini CLI**: `gemini extensions install https://github.com/tsfdsong/loopengine`
- **Copilot CLI**: `copilot plugin install loopengine@tsfdsong`
- **Kimi Code**: `/plugins install https://github.com/tsfdsong/loopengine`
- **Pi**: `pi install git:github.com/tsfdsong/loopengine`

### ZCode 桌面版手动安装

ZCode 桌面版 v3.1.8+ 的插件面板从内置包目录加载插件。安装步骤：

```powershell
# 1. 克隆项目到内置包目录
git clone https://github.com/tsfdsong/loop_engineering.git "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin"

# 2. 复制到 CLI 缓存（与 marketplace 路径一致）
mkdir -p "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0"
xcopy "$env:LOCALAPPDATA\Programs\ZCode\resources\glm\packages\loopengine-plugin\*" "$env:USERPROFILE\.zcode\cli\plugins\cache\zcode-plugins-official\loopengine\1.0.0\" /E /I /Y

# 3. 创建 data 目录
mkdir "$env:USERPROFILE\.zcode\cli\plugins\data\loopengine@zcode-plugins-official"

# 4. 在 marketplace.json 中注册插件（编辑 %USERPROFILE%\.zcode\cli\plugins\marketplaces\zcode-plugins-official\marketplace.json，添加 loopengine 条目）

# 5. 在 config.json 中启用插件（编辑 %USERPROFILE%\.zcode\cli\config.json，在 enabledPlugins 中添加 "loopengine@zcode-plugins-official": true）

# 6. 重启 ZCode 桌面版
```

**注册链路完整性检查清单**：
- [ ] 内置包目录 `glm/packages/loopengine-plugin/` 存在且含 55 个技能
- [ ] CLI 缓存 `cache/zcode-plugins-official/loopengine/1.0.0/` 存在
- [ ] marketplace.json 注册了 loopengine（`zcode-plugins-official` 市场）
- [ ] config.json 启用了 `loopengine@zcode-plugins-official`
- [ ] data 目录 `loopengine@zcode-plugins-official` 已创建

详见 `docs/zcode-install-guide.md`。
