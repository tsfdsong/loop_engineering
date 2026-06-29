# prompts/ — deep-research（深度调研） 提示词模板

> 4 个核心提示词模板，覆盖 4 阶段核心方法论。

---

## 模板列表

| 模板 | 用途 | 阶段 | 链接 |
|------|------|------|------|
| **source-tagging.md** | 动态来源分级（T1/T2/T3/Reject）| Search | [source-tagging.md](source-tagging.md) |
| **wdm-matrix.md** | WDM 加权决策矩阵 | Reason WDM | [wdm-matrix.md](wdm-matrix.md) |
| **munger-inversion.md** | Munger 反向自检 5 问 | Reason Munger | [munger-inversion.md](munger-inversion.md) |
| **reader-testing.md** | Reader Testing 模拟读者提问 | Reader Testing | [reader-testing.md](reader-testing.md) |

---

## 使用顺序

```
Search
  └─ source-tagging.md  ← 给每个来源打标签
       ↓
Reason
  ├─ wdm-matrix.md      ← 选胜出方案
  └─ munger-inversion.md  ← 对胜出方案反向自检
       ↓
Report
  └─ （撰写报告）
       ↓
Reader Testing
  └─ reader-testing.md  ← 模拟读者提问 + 回答
```

---

## 模板设计原则

1. **可直接使用**：复制提示词 → 替换占位符 → 用
2. **含示例**：每个模板都有"示例输入 / 示例输出"
3. **诚实标注限制**：每个模板有"已知限制"小节
4. **可扩展**：可以基于这些模板做变体

---

## 已知限制汇总

| 模板 | 主要限制 | 严重度 |
|------|---------|------|
| source-tagging | AI 分级可能错 | 🟡 |
| wdm-matrix | AI 评分主观 | 🟡 |
| munger-inversion | "自我评估"易敷衍 | 🟠 |
| reader-testing | 自问自答盲点相同 | 🟠 |

所有限制在各自模板中详细说明。
