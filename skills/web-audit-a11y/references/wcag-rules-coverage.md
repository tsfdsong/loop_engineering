# WCAG 规则覆盖

## axe-core 覆盖范围

axe-core 覆盖 **WCAG 2.0 / 2.1 / 2.2** 全部 A/AA 级规则 + 部分 AAA。AAA 覆盖不完整，需要人工补。

## 标签分类

| Tag | 覆盖范围 |
|---|---|
| `wcag2a` | WCAG 2.0 Level A |
| `wcag2aa` | WCAG 2.0 Level AA |
| `wcag2aaa` | WCAG 2.0 Level AAA（部分）|
| `wcag21a` | WCAG 2.1 Level A |
| `wcag21aa` | WCAG 2.1 Level AA |
| `wcag22aa` | WCAG 2.2 Level AA |
| `best-practice` | axe 推荐实践（不属 WCAG 强制）|

## 推荐配置

**Level AA 严格审计**（默认）：
```typescript
.withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"])
```

**Level AA + best practice**：
```typescript
.withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "best-practice"])
```

**仅 critical**（快速 smoke test）：
```typescript
.withTags(["wcag2aa"])
.disableRules(["color-contrast"])  // 跳过对比度（运行时单独查）
```

## axe-core 不覆盖的

- 屏幕阅读器实际体验（需要 NVDA/JAWS 手动测）
- 键盘导航的"流畅度"（axe 只查存在性，不查用户体验）
- 字幕/音频描述（媒体类）
- 复杂的 ARIA pattern（如 combobox 完整流程）

**这些必须人工补**——见 `false-positive-handling.md` § 人工测试清单。
