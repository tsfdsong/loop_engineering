# Token 优化三件套 — 安装配置与高效使用指南

> 安装日期：2026-06-26  
> 适用环境：ZCode + Python 3.14 + Node.js v24

---

## 一、已安装的工具

| 工具 | 版本 | 类型 | 核心能力 | 削减效果 |
|------|------|------|---------|---------|
| **jCodeMunch-MCP** | 1.108.82 | Python | AST 符号级代码检索 | **95%** |
| **Repomix** | 1.15.0 | Node.js | 代码库打包 + 结构压缩 | **70%** |
| **Headroom-ai** | 0.20.15 | Python | 上下文压缩层 | **60-95%** |

### 项目索引状态

```
✅ jCodeMunch 已索引：396 文件 / 5109 符号
   语言分布：Python 234, TSX 103, TypeScript 29, YAML 10, Bash 8
   
✅ Repomix 已验证：全量打包约 1,231,791 tokens（压缩后约 370,000 tokens）
```

---

## 二、三个工具的分工

```
你的日常 AI 编程流程：

  "帮我看看 kb_service.py 的 create_knowledge_base 函数"
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  jCodeMunch-MCP                             │
  │  只返回该函数的 30 行源码，不读整个 300 行文件  │  ← 削减 95%
  └─────────────────────────────────────────────┘
  
  "帮我理解整个项目的架构"
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Repomix --compress                         │
  │  打包所有文件，只保留函数/类签名，去掉实现细节   │  ← 削减 70%
  └─────────────────────────────────────────────┘
  
  "帮我调试这个报错"（长会话，50+ 轮对话）
        │
        ▼
  ┌─────────────────────────────────────────────┐
  │  Headroom-ai                                │
  │  自动压缩对话历史、工具输出，避免上下文膨胀      │  ← 削减 60-95%
  └─────────────────────────────────────────────┘
```

---

## 三、jCodeMunch-MCP 使用指南（主力工具）

### 3.1 核心概念

jCodeMunch 将你的代码库变成了一个**可查询的符号数据库**。AI 不再需要 `Read` 整个文件，而是直接查询符号。

### 3.2 启动方式

```bash
# 方式一：直接启动 MCP 服务器（推荐，后台运行）
jcodemunch-mcp serve

# 方式二：在 ZCode 中作为 MCP 工具自动调用
# （需配置 .mcp.json，见第五节）
```

### 3.3 核心使用场景

| 你想做什么 | 传统方式（费 token） | jCodeMunch 方式（省 token） |
|-----------|---------------------|---------------------------|
| 查看某个函数 | `Read` 整个文件（300行） | `search_symbols` → `get_symbol_source`（30行） |
| 理解文件结构 | `Read` 整个文件 | `get_file_outline`（只返回签名列表） |
| 查找谁调用了某函数 | `Grep` 全仓库 | `get_blast_radius`（精确影响分析） |
| 查找谁导入了某模块 | `Grep` 全仓库 | `find_importers`（精确导入关系） |
| 理解类继承关系 | 手动追踪多个文件 | `get_class_hierarchy`（完整继承链） |
| 发现死代码 | 人工审查 | `find_dead_code`（自动检测） |

### 3.4 对话中如何触发

在与 AI 对话时，**自然地描述你的需求**，jCodeMunch 会自动选择最佳工具：

```
✅ "帮我看看 kb_service.py 里有哪些函数"
   → AI 调用 get_file_outline，只返回函数签名

✅ "create_knowledge_base 这个函数的完整代码是什么"
   → AI 调用 get_symbol_source，只返回该函数源码

✅ "修改 create_knowledge_base 会影响哪些地方"
   → AI 调用 get_blast_radius，返回所有受影响的位置

✅ "哪些文件导入了 kb_service"
   → AI 调用 find_importers，返回精确列表
```

### 3.5 更新索引

```bash
# 代码变更后重新索引（通常在 git pull / 切换分支后）
jcodemunch-mcp index "C:/tsfdsong/python-project/yimi-ai-hub"

# 或启动文件监视自动更新
jcodemunch-mcp watch
```

---

## 四、Repomix 使用指南（架构理解工具）

### 4.1 核心概念

Repomix 将整个仓库打包为一个 AI 友好的 XML 文件。`--compress` 模式利用 tree-sitter 只保留代码结构（类/函数签名），去掉实现细节。

### 4.2 使用场景

| 场景 | 命令 | 说明 |
|------|------|------|
| **理解整体架构** | `repomix --compress` | 只保留结构，省 70% token |
| **给 AI 完整上下文** | `repomix` | 全量打包（1.23M tokens） |
| **只看后端** | `repomix --include "backend/**/*.py"` | 只打包 Python 代码 |
| **只看前端** | `repomix --include "frontend/src/**/*.tsx"` | 只打包 React 组件 |
| **Token 预算控制** | `repomix --token-budget 100000` | 超出预算时报错 |
| **查看 token 分布** | `repomix --token-count-tree` | 找出 token 大户 |

### 4.3 对话中如何触发

```
✅ "帮我理解这个项目的整体架构"
   → 运行 repomix --compress，将输出文件内容提供给 AI

✅ "帮我审查 backend/app/rag_hub/ 的代码质量"
   → 运行 repomix --include "backend/app/rag_hub/**/*.py" --compress
```

### 4.4 项目专属优化

你的项目中有 3 个巨大的 XSD 文件（各 74,717 tokens），建议排除：

```bash
repomix --compress \
  --ignore "**/*.xsd" \
  --ignore "**/node_modules/**" \
  --ignore "**/__pycache__/**" \
  --ignore "**/.git/**"
```

---

## 五、Headroom-ai 使用指南（上下文压缩）

### 5.1 核心概念

Headroom 是一个**上下文压缩层**，在内容进入 LLM 之前自动压缩。支持：
- **SmartCrusher**：压缩 JSON 结构数据
- **CodeCompressor**：基于 AST 压缩代码
- **Kompress-base**：NLP 模型压缩自然语言

### 5.2 使用方式

```bash
# 方式一：直接压缩文本
headroom compress "你的长文本内容"

# 方式二：压缩文件
headroom compress-file backend/app/rag_hub/services/kb_service.py

# 方式三：作为 MCP 服务器（推荐）
headroom mcp
```

### 5.3 对话中如何触发

Headroom 在长会话中自动生效。当对话超过 20 轮时，AI 可以调用 Headroom 压缩历史上下文：

```
✅ 对话进行到第 30 轮，上下文窗口接近上限
   → AI 调用 headroom_retrieve 压缩历史，释放空间
```

---

## 六、ZCode MCP 集成配置

在项目根目录创建 `.mcp.json`：

```json
{
  "mcpServers": {
    "jcodemunch": {
      "command": "jcodemunch-mcp",
      "args": ["serve"],
      "cwd": "${projectDir}"
    },
    "repomix": {
      "command": "repomix",
      "args": ["--mcp"],
      "cwd": "${projectDir}"
    },
    "headroom": {
      "command": "headroom",
      "args": ["mcp"],
      "cwd": "${projectDir}"
    }
  }
}
```

> ⚠️ 注意：如果 `jcodemunch-mcp` 和 `headroom` 命令不在 PATH 中，需要使用完整路径：
> - `C:/Users/admin/AppData/Roaming/Python/Python314/Scripts/jcodemunch-mcp.exe`
> - `C:/Users/admin/AppData/Roaming/Python/Python314/Scripts/headroom.exe`

---

## 七、高效使用策略总结

### 黄金法则：按场景选择工具

```
┌──────────────────────────────────────────────────────┐
│                                                      │
│   需要读代码？          → jCodeMunch（查符号）         │
│   需要理解架构？        → Repomix --compress（看结构） │
│   长会话/大量输出？     → Headroom（压缩上下文）       │
│                                                      │
│   三者可以叠加使用，覆盖 token 消耗的三大来源           │
└──────────────────────────────────────────────────────┘
```

### 典型工作流

**场景一：新功能开发**
```
1. repomix --compress              → 理解整体架构（省 70%）
2. jCodeMunch 查相关函数           → 精确阅读代码（省 95%）
3. 编写代码                         → 正常消耗
4. Headroom 压缩长对话              → 保持上下文不膨胀
```

**场景二：Bug 修复**
```
1. jCodeMunch get_blast_radius     → 定位影响范围
2. jCodeMunch get_symbol_source    → 阅读相关代码
3. 修复 + 验证                      → 正常消耗
```

**场景三：代码审查**
```
1. repomix --include "改动的目录"   → 打包变更范围
2. jCodeMunch get_changed_symbols  → 精确定位变更符号
3. 逐文件审查                       → 正常消耗
```

### 预估节省效果

| 场景 | 无优化 | 组合后 | 节省 |
|------|--------|--------|------|
| 阅读 kb_service.py（300行） | ~800 token | ~40 token | **95%** |
| 理解项目整体架构 | ~1,200,000 token | ~370,000 token | **70%** |
| 长会话（50轮） | ~40,000 token | ~12,000 token | **70%** |
| pytest 输出（200行） | ~1,200 token | ~200 token | **83%** |

---

## 八、维护与更新

```bash
# 更新 jCodeMunch
pip install --upgrade jcodemunch-mcp

# 更新 Repomix
npm update -g repomix

# 更新 Headroom
pip install --upgrade headroom-ai

# 代码变更后重新索引
jcodemunch-mcp index "C:/tsfdsong/python-project/yimi-ai-hub"
```

---

## 九、常见问题

**Q: jCodeMunch 索引需要多久？**  
A: 你的项目（396 文件）只需 3.3 秒。

**Q: 索引会占用多少磁盘？**  
A: 约 10-50MB，存储在 `~/.code-index/`。

**Q: 三个工具同时运行会冲突吗？**  
A: 不会。它们各自独立，分别处理代码检索、打包、压缩。

**Q: 需要每次手动触发吗？**  
A: 配置 MCP 后，AI 会自动选择合适的工具。你也可以在对话中明确要求。
