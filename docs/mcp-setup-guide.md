# MCP 三件套安装配置与高效使用指南

> 适用版本：LoopEngine 1.0.2+
> 文档日期：2026-06-30
> 配套文档：`docs/token-optimization-guide.md`（底层原理）

---

## 一、TL;DR — 三件套是什么

LoopEngine 依赖 **三个 MCP 工具** 为 AI 提供"省 90% token"的代码探索能力：

| 工具 | 类型 | 安装命令 | 核心能力 | Token 节省 |
|------|------|---------|---------|:---:|
| **jCodeMunch-MCP** | Python | `pip install jcodemunch-mcp` | AST 符号级代码检索 | **95%** |
| **Repomix** | Node.js | `npm install -g repomix` | 代码库打包 + 结构压缩 | **70%** |
| **Headroom-ai** | Python | `pip install headroom-ai` | 上下文压缩层 | **60-95%** |

> **典型场景平均节省 ≈ 80% token**（详见第五章量化数据）

---

## 二、三件套分工

```
你的日常 AI 编程流程
        │
        ├── "帮我看看 kb_service.py 的 create_knowledge_base 函数"
        │       └─→ jCodeMunch  search_symbols → 仅返回该函数的 30 行源码（省 95%）
        │
        ├── "帮我理解整个项目的架构"
        │       └─→ Repomix     --compress     → 仅保留函数/类签名（省 70%）
        │
        └── "对话进行了 30 轮，上下文快满了"
                └─→ Headroom    mcp serve      → 自动压缩历史上下文（省 60-95%）
```

---

## 三、安装步骤

### 3.1 一键安装（推荐）

执行 LoopEngine 安装脚本，会自动检测 + 安装 + 配置 MCP 三件套：

```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
```

脚本会自动：
1. 检测本机已装的 AI 工具并部署 LoopEngine 插件包
2. 合并 MCP 配置到 Cursor / ZCode 等（需本机已装 jcodemunch-mcp / repomix / headroom）
3. 注入 AGENTS 红线块
4. 写入 `~/.loopengine/install-manifest.json`

### 3.2 手动安装

#### Windows（PowerShell / Git Bash）

```powershell
# 1. 安装 repomix（Node.js 包）
npm install -g repomix

# 2. 安装 jcodemunch-mcp（Python 包）
pip install --upgrade jcodemunch-mcp

# 3. 安装 headroom-ai（Python 包）
pip install --upgrade headroom-ai

# 4. 验证三个工具
repomix --version
jcodemunch-mcp --version
headroom --version
```

> **PATH 修复**（仅 Windows 需要）：
> 如果 `jcodemunch-mcp` 和 `headroom` 不在 PATH 中，把以下加入系统 PATH：
> - `C:\Users\<user>\AppData\Roaming\Python\Python314\Scripts\`（pip 默认安装位置）
> - 或 `%LOCALAPPDATA%\Programs\Python\Python314\Scripts\`

#### Linux / macOS

```bash
# 1. 安装 repomix
npm install -g repomix

# 2. 安装 jcodemunch-mcp + headroom-ai
pip3 install --upgrade jcodemunch-mcp headroom-ai

# 3. 把 pip --user bin 加入 PATH（如未自动加入）
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc  # 或 ~/.zshrc
source ~/.bashrc

# 4. 验证
repomix --version
jcodemunch-mcp --version
headroom --version
```

---

## 四、配置 MCP 服务

> **重要更新（2026-06-30）**：LoopEngine 的 `install.py` 会自动写入两份配置：
>
> | 场景 | 配置文件 | 何时生效 |
> |---|---|---|
> | **ZCode 桌面版 MCP**（全局） | `~/.zcode/cli/config.json` → `mcp.servers.*` | 重启 ZCode 后生效（推荐） |
> | 当前工作区 / CLI | 项目根 `.mcp.json` → `mcpServers.*` | 当前项目内立即生效 |
>
> **以前只写项目根 `.mcp.json` 时，桌面版 MCP 列表里看不见 3 个 server——根因是入口不在那里。**
> 现在 `install.py` 会自动写两份，绝大多数用户无需手动改任何 JSON。

### 4.1 ZCode 桌面版的"真正"配置（全局）

文件位置：

| OS | 路径 |
|---|---|
| Windows | `C:\Users\<user>\.zcode\cli\config.json` |
| Linux/macOS | `~/.zcode/cli/config.json` |

**结构与项目根 `.mcp.json` 不一样**——用的是 `mcp.servers.<name>`，每个 server 必须带 `type: "stdio"`：

```json
{
  "provider": { ... },            // ← 用户已有的模型配置（install.py 不会覆盖）
  "mcp": {
    "servers": {
      "jcodemunch": {
        "type": "stdio",
        "command": "C:/Users/admin/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe",
        "args": ["serve"]
      },
      "repomix": {
        "type": "stdio",
        "command": "C:/Users/admin/AppData/Roaming/npm/repomix.cmd",
        "args": ["--mcp"]
      },
      "headroom": {
        "type": "stdio",
        "command": "C:/Users/admin/AppData/Roaming/Python/Python314/Scripts/headroom.exe",
        "args": ["mcp", "serve"]
      }
    }
  }
}
```

> **Windows 扩展名硬规则**：
> - pip 装的两个是 **`.exe`**（不是 `jcodemunch-mcp` 或 `headroom`）
> - npm 装的 repomix 是 **`.cmd`**（不是 `repomix`）
> - Node `spawn` 在 win32 上不会自动补扩展名，缺后缀就启动失败 → 列表里看不到
>
> `install.py` 会自动用绝对路径 + 正确后缀写入，无需手动改。

### 4.2 项目根 `.mcp.json`（CLI / 工作区级）

CLI 或某些 IDE 直接读项目根的 `.mcp.json`（结构 `mcpServers`，**无** `type` 字段）：

```json
{
  "mcpServers": {
    "jcodemunch": {
      "command": "jcodemunch-mcp",
      "args": ["serve"]
    },
    "repomix": {
      "command": "repomix",
      "args": ["--mcp"]
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp", "serve"]
    }
  }
}
```

`install.py` 也会自动写这份，依赖 PATH 解析。如果 PATH 不全（比如 Windows pip `--user` 装到 Scripts 但未加入 PATH），改成 §4.1 那种绝对路径即可。

### 4.3 手动 UI 配置（不推荐，install.py 已覆盖）

如果你不想跑 install.py，也可以在 ZCode 桌面版 UI 里"添加 MCP 服务"，把 §4.1 那个 JSON 串粘贴进去。**但 UI 一次只能配一个 server**，所以"三次才能配完"是正常的（每个 service 一次粘贴）。

---

## 五、首次使用：索引项目

jCodeMunch 需要先把项目**索引**到本地数据库（`~/.code-index/`），之后才能用 `search_symbols` 等工具。

### 5.1 索引当前项目

```bash
# 在项目根目录执行
jcodemunch-mcp index_folder .

# 或指定完整路径
jcodemunch-mcp index_folder "C:/tsfdsong/python-project/loop_engineering"
```

### 5.2 验证索引

```bash
# 列出已索引的项目
ls ~/.code-index/

# 应该看到类似：
# config.jsonc
# loop_engineering/
# loop_engineering.db
```

### 5.3 索引策略

| 场景 | 操作 |
|------|------|
| **首次使用** | 执行 `jcodemunch-mcp index_folder .` |
| **代码大量变更** | 重新执行 `jcodemunch-mcp index_folder .`（通常 3-10 秒） |
| **实时增量** | 启动 `jcodemunch-mcp watch`（文件监视自动更新索引） |
| **切换分支** | 重新执行 `index_folder`（符号定义可能变化） |

---

## 六、验证三件套工作正常

### 6.1 jCodeMunch 验证

```bash
# 启动 MCP server（应进入 stdio 监听，无报错）
jcodemunch-mcp serve --transport stdio --log-level INFO

# 在 AI 对话中调用：
# "用 get_repo_map 看看 loop_engineering 的结构"
# "用 search_symbols 找 install.py 里的 detect 逻辑"
```

### 6.2 Repomix 验证

```bash
# CLI 模式：生成压缩版项目快照
repomix --compress --output repomix-output.xml

# MCP 模式（供 AI 调用）：
repomix --mcp
```

### 6.3 Headroom 验证

```bash
# 启动 MCP server
headroom mcp serve

# CLI 模式：压缩一段文本
echo "long text..." | headroom compress
```

### 6.4 在 AI 对话中验证

启动 AI 会话后，发送以下提示：

```
请帮我做三件事，验证 MCP 三件套工作正常：
1. 调用 jcodemunch 的 get_repo_map，列出 loop_engineering 项目的顶层结构
2. 调用 repomix 的 pack_codebase（compress 模式），返回项目 token 数
3. 如果你已经进行了 20+ 轮对话，调用 headroom 压缩历史上下文
```

---

## 七、Token 节省量化数据

> 实测数据来自 `docs/token-optimization-guide.md` 第七节

### 7.1 单工具节省效果

| 工具 | 适用场景 | 平均节省 |
|------|---------|:---:|
| 🔍 **jCodeMunch** | 查函数 / 找引用 / 分析类结构 | **95%** |
| 📦 **Repomix** | 理解整体架构 / 打包大项目 | **70%** |
| 🗜️ **Headroom** | 长会话 / 大输出压缩 | **60-95%** |

### 7.2 典型场景对比

| 场景 | ZCode 自带工具（Glob+Grep+Read） | MCP 三件套组合 | 节省 |
|------|----------------------|--------|:---:|
| 阅读单个函数（300 行文件） | ~800 token（Read 全文） | ~40 token（search_symbols 精准读 30 行） | **95%** |
| 理解项目整体架构 | ~1,200,000 token（pack_codebase 全量） | ~370,000 token（repomix --compress） | **69%** |
| 长会话（50 轮对话） | ~40,000 token（无压缩） | ~12,000 token（headroom 压缩） | **70%** |
| pytest 输出（200 行） | ~1,200 token | ~200 token | **83%** |
| **典型场景平均** | — | — | **~80%** |

### 7.3 三大 token 节省来源

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   需要读代码？          → jCodeMunch（查符号）         │ 95%
│   需要理解架构？        → Repomix --compress（看结构） │ 70%
│   长会话/大量输出？     → Headroom（压缩上下文）       │ 60-95%
│                                                      │
│   三者叠加 ≈ 节省 80% token（典型场景）                │
└──────────────────────────────────────────────────────┘
```

---

## 八、高效使用工作流

### 8.1 新功能开发

```
1. repomix --compress              → 理解整体架构（省 70%）
2. jCodeMunch search_symbols       → 精确阅读相关函数（省 95%）
3. 编写代码                         → 正常消耗
4. Headroom 压缩长对话              → 保持上下文不膨胀（省 70%）
```

### 8.2 Bug 修复

```
1. jCodeMunch get_blast_radius     → 定位影响范围（省 90%）
2. jCodeMunch search_symbols       → 阅读相关代码（省 95%）
3. 修复 + 验证                      → 正常消耗
```

### 8.3 代码审查

```
1. repomix --include "改动目录"     → 打包变更范围（省 70%）
2. jCodeMunch get_changed_symbols  → 精确定位变更符号
3. 逐文件审查                       → 正常消耗
```

---

## 九、常见问题

### Q1: `command not found: jcodemunch-mcp`

**A**: pip 安装到了 `--user` 目录，但未在 PATH 中。

修复：
- **Windows**: 把 `C:\Users\<user>\AppData\Roaming\Python\Python<ver>\Scripts\` 加入 PATH
- **Linux/macOS**: 把 `$HOME/.local/bin` 加入 PATH，或 `pip install --user` 时不用 `--user`

或者直接在 `.mcp.json` 用绝对路径（见第四章末尾说明）。

### Q2: 索引需要多久？

**A**: loop_engineering 项目（~40 文件）约 3-5 秒。大型项目（>1000 文件）约 30-60 秒。

索引存储在 `~/.code-index/`，占用约 10-50MB 磁盘。

### Q3: 三个工具会冲突吗？

**A**: 不会。它们各司其职：
- jCodeMunch：符号级查询（**只读**，不修改代码）
- Repomix：打包（**只读**，生成 XML 快照）
- Headroom：压缩（**只读**，压缩工具输出）

### Q4: 需要每次手动触发吗？

**A**: 不需要。配置 `.mcp.json` 后，AI 会**自动选择**最合适的工具：
- 你说"看看这个函数" → AI 自动调 jCodeMunch
- 你说"理解架构" → AI 自动调 Repomix
- 对话很长时 → Headroom 自动压缩历史

你也可以在对话中**显式要求**："请用 jCodeMunch 搜索..."。

### Q5: Repomix 打包会泄露代码吗？

**A**: Repomix 是**本地工具**，打包文件留在本地（默认 `repomix-output.xml`），不会上传到任何服务器。MCP 模式下，AI 通过 stdio 调用，**不会持久化**任何代码。

### Q6: `jcodemunch-mcp index_folder` 报错 "folder not in trusted_folders"

**A**: 默认配置下 jCodeMunch 启用了 `trusted_folders_whitelist_mode`。

修复方法（选其一）：
1. 把项目路径加入白名单：编辑 `~/.code-index/config.jsonc`，在 `trusted_folders` 数组中添加项目路径
2. 切换到黑名单模式：`trusted_folders_whitelist_mode: false`

### Q7: install.py 安装后 MCP 工具还是不工作？

**A**: 检查清单：
- [ ] `.mcp.json` 在项目根
- [ ] `jcodemunch-mcp --version` 在终端能跑（说明 PATH 正确）
- [ ] `~/.code-index/` 目录有当前项目的索引
- [ ] 重启 ZCode / AI 客户端（让 MCP 配置生效）

---

## 十、参考资料

- `docs/token-optimization-guide.md` — 底层原理与详细使用指南
- `skills/go/SKILL.md` — go 全自动编排（含 family 路由 · MCP 调度见 `AGENTS.md`）
- `AGENTS.md` — MCP 红线规则
- [jCodeMunch GitHub](https://github.com/jgravelle/jcodemunch-mcp)
- [Repomix GitHub](https://github.com/yamadashy/repomix)
- [Headroom-ai GitHub](https://github.com/avivsinai/headroom)

---

## 附录：命令速查

```bash
# 安装
pip install --upgrade jcodemunch-mcp
pip install --upgrade headroom-ai
npm install -g repomix

# 索引
jcodemunch-mcp index_folder .
jcodemunch-mcp watch            # 文件监视
jcodemunch-mcp serve            # 启动 MCP server

# Repomix
repomix --compress              # 打包（压缩模式）
repomix --mcp                   # 启动 MCP server
repomix --include "skills/**"   # 只打包 skills 目录

# Headroom
headroom --version
headroom mcp serve              # 启动 MCP server
headroom mcp install            # 安装到 Claude Code
headroom mcp status             # 查看状态

---

## 九、ZCode 桌面版 MCP 配置问题（治本方案 · 2026-06-30 实战总结 · v1.1）

### 9.1 症状
按本文前八章装好 MCP 三件套，命令行 `jcodemunch-mcp --version` / `headroom --version` / `repomix --version` 都正常。
但在 ZCode 桌面版的 MCP 服务列表里**看不到** jcodemunch / repomix / headroom 任何一个。

### 9.2 根因（2026-06-30 实测铁证 · 推翻 v1.0 旧结论）

通过 `grep -rli jcodemunch ~/.zcode ~/AppData/Roaming/ZCode` 全局搜索确认：

```
C:/Users/admin/.zcode/cli/config.json   ← 桌面版 MCP 真正入口 [F]
C:/Users/admin/.zcode/cli/log/zcode-2026-06-30.jsonl   ← 仅日志
C:/Users/admin/.zcode/v2/tasks-index.sqlite            ← 任务索引（无关）
```

**桌面版 ZCode 加载 MCP 的真正入口是 `~/.zcode/cli/config.json`**（结构 `mcp.servers.<name>`），用户通过桌面 UI 配三次才成功，就是反复试错这个文件和它的 schema。

| # | 事实 [F] | 推翻 / 修正 |
|---|---------|-----------|
| 1 | 桌面版从 `~/.zcode/cli/config.json` 的 `mcp.servers` 读 MCP | ✅ 推翻 v1.0 "从 plugin.json 读" 的旧根因 |
| 2 | `marketplace.json` 被 ZCode 自动重写丢失 loopengine | ⚠️ 部分对，但 MCP 入口不在 marketplace |
| 3 | CLI 缓存的 `plugin.json` 缺 `mcpServers` 字段 | ⚠️ 部分对，但桌面版不读它 |

**v1.0 旧脚本的 3 大错误**：
1. ❌ 只写 `plugin.json` 缓存路径（桌面版根本不从那读）
2. ❌ 只写 `marketplace.json`（ZCode 会重写丢失）
3. ❌ 没写 `~/.zcode/cli/config.json`（真正入口）

### 9.3 治本方案（v1.1）`scripts/zcode-mcp-ensure.sh` + `install.py` MCP merge

LoopEngine 1.0.2+ 重写后一次跑完 5 件事：

| Step | 行为 | 路径 |
|------|------|------|
| 1 | 探测三个 MCP 可执行文件绝对路径 | — |
| 2 | 探测失败则中止 | — |
| **3** | **写入 `~/.zcode/cli/config.json` 的 `mcp.servers`** | **桌面版真正入口 [F]** |
| 4 | 兼容写入 `~/.zcode/cli/mcp-servers.json`（老 ZCode） | 向下兼容 |
| 5 | stdIO 握手验证（JSON-RPC `initialize`） | — |

**Step 3 关键 schema**（与 `.mcp.json` 不同）：
```json
{
  "mcp": {
    "servers": {
      "jcodemunch": {"type": "stdio", "command": ".../jcodemunch-mcp.exe", "args": ["serve"]},
      "repomix":    {"type": "stdio", "command": ".../repomix.cmd",        "args": ["--mcp"]},
      "headroom":   {"type": "stdio", "command": ".../headroom.exe",       "args": ["mcp", "serve"]}
    }
  }
}
```

自动调用（`install.py` 内部已集成）：
```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.py | python3
```

手动调用（重启 ZCode 后 MCP 还是不显示时）：
```bash
# 标准模式
bash scripts/zcode-mcp-ensure.sh

# 静默模式（CI / 自动任务）
bash scripts/zcode-mcp-ensure.sh --quiet
```

正常结尾输出：
```
✅ jcodemunch-mcp 握手通过（服务端: jcodemunch-mcp）
✅ repomix 握手通过（服务端: repomix-mcp-server）
✅ headroom 握手通过（服务端: headroom）
✅ 全部 3 个 MCP 工具握手通过
🎉 自愈完成 — ZCode 桌面版重启后 MCP 工具将自动加载
```

### 9.4 验证清单（重启后 MCP 仍不丢）

```bash
# 1) 桌面版 config.json 含三个 server
cat ~/.zcode/cli/config.json | python -c "import json,sys; d=json.load(sys.stdin); print(list(d['mcp']['servers'].keys()))"
# 期望: ['jcodemunch', 'repomix', 'headroom']

# 2) 三个 exe 路径能跑（5 秒超时）
~/.zcode/cli/config.json | python -c "import json,sys; d=json.load(sys.stdin); \
  [print(s, d['mcp']['servers'][s]['command']) for s in d['mcp']['servers']]"

# 3) 重跑自愈确认全绿
bash scripts/zcode-mcp-ensure.sh
```

### 9.5 永远不要做的事（v1.1 修订）
| ❌ 反模式 | 为什么错 |
|---------|---------|
| 只写项目根 `.mcp.json` | 桌面版**不读**项目根，只读 `~/.zcode/cli/config.json` |
| 只改 `内置包目录/.mcp.json` 或 `plugin.json` | 桌面版加载顺序中位置在 `cli/config.json` 之后，且可能不读 |
| 只改 `marketplace.json` | 下次 ZCode 启动会被自动重写丢失 |
| 命令路径写 `jcodemunch-mcp` 不带 `.exe` | Node spawn 在 win32 不补扩展名，启动失败 |
| 命令路径写 `repomix` 不带 `.cmd` | 同上 |
| `cli/config.json` 里漏 `type: "stdio"` | 部分 ZCode 版本 schema 校验失败 |

### 9.6 调试常见问题（v1.1 修订）
**Q：自愈脚本报告 `jcodemunch-mcp 未找到`？**
A：先 `pip install --user jcodemunch-mcp`，再跑 `install.py`，它会自动探测绝对路径。

**Q：握手通过但 ZCode 里仍看不到？**
A：99% 是 `~/.zcode/cli/config.json` 没写好。检查：
```bash
cat ~/.zcode/cli/config.json | python -m json.tool | grep -A1 "command"
```
确认 3 个 command 路径都能直接 `cmd /c` 跑起来（带正确 `.exe` / `.cmd` 后缀）。
然后**完全退出** ZCode（不是最小化窗口）→ 重新打开。

**Q：写完 config.json，重启 ZCode，3 个 server 又消失了？**
A：极少数情况下 ZCode 会在启动时清理 `cli/config.json` 中它"不认识"的 server。
**重新跑** `bash scripts/zcode-mcp-ensure.sh` 即可；或者把 `install.py install` 写成一个 ZCode 启动后任务（settings → onStartup）。
```