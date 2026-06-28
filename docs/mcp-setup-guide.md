# MCP 三件套安装配置与高效使用指南

> 适用版本：LoopEngine 1.0.1+
> 文档日期：2026-06-28
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
curl -fsSL https://raw.githubusercontent.com/tsfdsong/loop_engineering/main/install.sh | bash
```

脚本会自动：
1. 检测 Node.js / Python / pip
2. 用 `pip install` 安装 jcodemunch-mcp 和 headroom-ai
3. 用 `npm install -g` 安装 repomix
4. 把 Python Scripts 目录加入 PATH（持久化）
5. 在项目根创建 `.mcp.json`

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

## 四、配置 `.mcp.json`

在项目根创建 `.mcp.json`（LoopEngine install.sh 会自动生成此文件）：

```json
{
  "mcpServers": {
    "jcodemunch": {
      "command": "jcodemunch-mcp",
      "args": ["serve"],
      "cwd": "${workspaceFolder}"
    },
    "repomix": {
      "command": "repomix",
      "args": ["--mcp"],
      "cwd": "${workspaceFolder}"
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp", "serve"],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

> 如果 `jcodemunch-mcp` / `headroom` 不在 PATH 中，把 `command` 改成绝对路径：
> ```json
> "jcodemunch": {
>   "command": "C:/Users/admin/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe",
>   "args": ["serve"]
> }
> ```

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
# "用 search_symbols 找 install.sh 里的 detect_tool 函数"
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

### Q7: install.sh 安装后 MCP 工具还是不工作？

**A**: 检查清单：
- [ ] `.mcp.json` 在项目根
- [ ] `jcodemunch-mcp --version` 在终端能跑（说明 PATH 正确）
- [ ] `~/.code-index/` 目录有当前项目的索引
- [ ] 重启 ZCode / AI 客户端（让 MCP 配置生效）

---

## 十、参考资料

- `docs/token-optimization-guide.md` — 底层原理与详细使用指南
- `skills/skill-hub/SKILL.md` 第 202-234 行 — MCP 工具调度规则
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

## 九、ZCode 桌面版 MCP 重启丢失问题（治本方案 · 2026-06-28 实战总结）

### 9.1 症状
按本文前八章装好 MCP 三件套，ZCode 桌面版里能看到 jcodemunch/repomix/headroom 三个 server。
**但重启 ZCode 后这三个 server 又消失了。** 重装 / 更新 install.sh / 改 `marketplace.json` 都无效。

### 9.2 根因（铁证）
2026-06-28 实测发现 ZCode 桌面版有三条隐性规则：

| # | 规则 | 后果 |
|---|------|------|
| 1 | ZCode 启动时**自动重写** `~/.zcode/cli/plugins/marketplaces/*/marketplace.json` | 我们手动加的 loopengine 条目被反复删除 |
| 2 | ZCode 优先从 **CLI 缓存** `plugins/cache/.../loopengine/<ver>/.zcode-plugin/plugin.json` 加载 MCP | 改"内置包目录"或"项目源"都不生效 |
| 3 | CLI 缓存的 `plugin.json` 默认**没有** `mcpServers` 字段 | 插件加载成功，但 MCP server 列表为空 |

时间线证据（24 小时内）：
```
22:02  CLI 缓存 plugin.json 写入（无 mcpServers）     ← ZCode 初始化
22:55  ~/.zcode/cli/mcp-servers.json 修复为绝对路径    ← 我们第一次修
22:59  内置包目录 plugin.json 写入（含 mcpServers）     ← 我们手动改
23:00  项目源 plugin.json 提交（含 mcpServers）        ← 我们 commit
23:04  marketplace.json 被 ZCode 重写（无 loopengine）  ← ZCode 启动清理
→ 下次启动时 ZCode 找不到 loopengine → MCP 全消失
```

### 9.3 治本方案：`scripts/zcode-mcp-ensure.sh`
LoopEngine 1.0.2+ 内置自愈脚本，一次跑完 4 件事：

1. **探测三个 MCP 可执行文件绝对路径**（jcodemunch-mcp / headroom / repomix）
2. **把 mcpServers 注入到所有 plugin.json 缓存位置**：
   - `内置包目录/.zcode-plugin/plugin.json`（v1.0.0）
   - `内置包目录/package.json`（v1.0.0 兼容）
   - `CLI 缓存 zcode-plugins-official/loopengine/*/.zcode-plugin/plugin.json`
   - `CLI 缓存 loopengine-local/loopengine/*/.zcode-plugin/plugin.json`
   - `项目源/.zcode-plugin/plugin.json` 与 `项目源/.mcp.json`
3. **在两个 marketplace.json 中加回 loopengine 注册**（双保险）
4. **stdIO 握手验证**：发 JSON-RPC `initialize` 请求，确认三个 server 都返回 `serverInfo`

由 `install.sh` / `update.sh` 在 ZCode 同步段自动调用，**也可手动跑**：

```bash
# 标准模式（带彩色输出）
bash scripts/zcode-mcp-ensure.sh

# 静默模式（只输出错误，适合 CI / 自动任务）
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
# 1) CLI 缓存 plugin.json 含 mcpServers
grep -A2 "mcpServers" ~/.zcode/cli/plugins/cache/zcode-plugins-official/loopengine/*/.zcode-plugin/plugin.json

# 2) marketplace.json 含 loopengine
grep "loopengine" ~/.zcode/cli/plugins/marketplaces/*/marketplace.json

# 3) 重跑自愈确认全绿
bash scripts/zcode-mcp-ensure.sh
```

### 9.5 永远不要做的事
| ❌ 反模式 | 为什么错 |
|---------|---------|
| 只改 `内置包目录/plugin.json` | ZCode 启动后**不从它**加载 MCP |
| 只改 `项目源/.zcode-plugin/plugin.json` | 不会自动同步到 CLI 缓存 |
| 只改 `marketplace.json` | 下次 ZCode 启动会被自动重写丢失 |
| `plugin.json` 里写 `jcodemunch-mcp` 等命令名 | 依赖 PATH，重启后可能找不到（pip --user 装到 Scripts 目录） |
| 把 `enabledPlugins` 改成 `false` 再改回 `true` | 不会修复 plugin.json 缺失的 mcpServers 字段 |

### 9.6 调试常见问题
**Q：自愈脚本报告 `jcodemunch-mcp 未找到`？**
A：先 `pip install --upgrade jcodemunch-mcp`，然后跑 `install.sh`，它会自动把 Python Scripts 加到 PATH。

**Q：握手通过但 ZCode 里仍看不到？**
A：99% 是 CLI 缓存的 plugin.json 还没注入。手动跑 `bash scripts/zcode-mcp-ensure.sh`，然后**完全退出并重启** ZCode（不是最小化窗口）。

**Q：marketplace.json 总被 ZCode 重写丢失 loopengine？**
A：正常现象。ZCode 在每次启动时都会清理"未在内置包目录找到对应版本"的条目。**靠自愈脚本每次启动后修复即可**，不要靠手改 marketplace.json。
```