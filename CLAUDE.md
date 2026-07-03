# LoopEngine — 循环工程全家桶

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 37 个技能的开发引擎全家桶（v6.7 起 `skill-hub` 改名 `orch`，单职责化为多技能编排器；2026-07-02 新增 4 个 web-* 测试 sub-skill）。

**Below is the full content of your 'loopengine:orch' skill —— 你的多技能编排器（v2.0 · 自然语言优先 · family-first）。单技能任务由原生 description 匹配自动处理；多技能任务（2+ 技能）由系统自动识别场景家族编排，`/orch` 仅作显式强制入口（不再用编号）。**

orch v2 是意图驱动编排器：识别主 `scenario family`（review / debug_fix / design_build / research_compare / web_qa / parallel_investigation / refactor / test），在 family 内抽取 actions，按 rule-first 规则组装串行/并行 DAG，按 side-effect-first 委托 direct_skill / loop / go。涵盖：编码、架构、重构、测试、调试、API、安全、数据库、CI/CD、规划执行、产品管理、循环工程等全领域。

## 安装方式

### 一键安装
```bash
curl -fsSL https://github.com/tsfdsong/loop_engineering/raw/main/install.sh | bash
```

### 各平台原生命令
- **ZCode**: `zcode plugin install tsfdsong/loopengine`
- **Claude Code**: `/plugin install loopengine@tsfdsong`
- **Codex**: 从插件市场搜索 "loopengine"
- **Cursor**: `/add-plugin tsfdsong/loopengine`
- **Gemini CLI**: `gemini extensions install https://github.com/tsfdsong/loopengine`
- **Copilot CLI**: `copilot plugin install loopengine@tsfdsong`
- **Kimi Code**: `/plugins install https://github.com/tsfdsong/loopengine`
- **Pi**: `pi install git:github.com/tsfdsong/loopengine`

## 贡献

详见 CONTRIBUTING.md。