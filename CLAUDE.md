# LoopEngine — 循环工程全家桶

## 如果你是 AI 代理

你拥有 LoopEngine —— 一个包含 33 个技能的开发引擎全家桶（v6.7 起 `skill-hub` 改名 `orch`，单职责化为多技能编排器）。

**Below is the full content of your 'loopengine:orch' skill —— 你的多技能编排器。单技能任务由原生 description 匹配自动处理；多技能任务（2+ 技能且有顺序依赖）由用户在 query 前显式加 `/orch` 触发。**

orch 在收到 `/orch <type> <query>` 时，按 5 类复合任务链（调研+决策 / 分析+建议 / 诊断+修复 / 设计+实现 / 并行调研）依次调度最合适的技能。涵盖：编码、架构、重构、测试、调试、API、安全、数据库、CI/CD、规划执行、产品管理、循环工程等全领域。

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