# 组件 Spec 模板（component-spec-template.md）

## 模板
```markdown
## <ComponentName> Spec

### Props
| name | type | default | description |
|---|---|---|---|

### States
- default / hover / active / focus / disabled / loading / error

### Variants
- size: sm / md / lg
- color: primary / secondary / danger

### Accessibility
- ARIA 属性
- 键盘导航
- 屏幕阅读器

### Visual
- baseline 截图路径
- 设计 token 引用
```

## 编写时机
- 创建新组件前必写
- 重构组件前更新 spec
- spec 与代码同步（spec 漂移 = 技术债）
