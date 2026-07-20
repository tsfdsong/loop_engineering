# LoopEngine — 循环工程全家桶

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 **32** 个技能的开发引擎全家桶（**v2.0**：原 `orch` 已合并进 `go` Step 0 · family-first 路由）。

**Below is the full content of your 'loopengine:go' skill —— 你的全自动编排器（v2.0 · family-first · worktree 并发）。单技能任务由原生 description 匹配自动处理；跨模块/多步工程目标用 `/go`。`/orch` 仅为兼容别名。**

go 在 Step 0 识别主 `scenario family`（review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test），组装 DAG，按 side-effect-first 委托 direct_skill / loop / go 自身。

## 安装方式

### 一键安装（推荐 · 所有平台通用）
```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

install.sh 自动检测已安装的 AI 工具并部署：plugin manifest 渲染 + skills/hooks/commands 复制 + MCP 配置 + 12 条红线注入（2 H2 sentinel 块）。

### Windows PowerShell
```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$le = "$env:TEMP\le-install-$([DateTime]::UtcNow.Ticks).ps1"
irm https://github.com/tsfdsong/loop_engineering/raw/main/install.ps1 -OutFile $le
& $le
Remove-Item $le -Force
```

### 部署验证（v1.4 新增）
```bash
python3 scripts/audit_tools.py    # 6 维度部署审计（A 工具部署/B 技能/C 红线/D MCP/E 版本/F Schema）
```

详见 [README.md](README.md)。

## 贡献

详见 CONTRIBUTING.md。