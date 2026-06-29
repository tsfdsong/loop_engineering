---
name: legacy-code
description: 遗留代码改造规则集 —— 安全有效地改造遗留系统。涵盖接缝、特征测试、依赖破除等技术。源自 Feathers《Working Effectively with Legacy Code》。
metadata:
  source: ciembor/agent-rules-books
  book: Working Effectively with Legacy Code by Michael Feathers
---

# Working Effectively with Legacy Code 规则集

当需要改造没有测试保护的遗留系统时使用此技能。遗留代码定义为"没有测试的代码"。

## 使用方式

加载此技能后，**必须**读取并严格遵循以下规则文件：

```
C:\Users\admin\.agents\skills\agent-rules-books\working-effectively-with-legacy-code\working-effectively-with-legacy-code.mini.md
```

## 规则概览

- 遗留代码是需要修改但没有测试的代码
- 先加测试再改代码
- 识别接缝（Seam）：可在不修改源码情况下改变行为的位置
- 破除依赖：参数化、提取接口、子类化并重写
- 特征测试（Characterization Test）：记录现有行为
- 小步改动，快速验证
- 高风险改动优先用安全手段

**_规则文件是此技能的核心。务必在改造前读取它。_**
