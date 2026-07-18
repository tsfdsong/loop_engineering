# 设计 Token 规范（design-tokens.md）

## token 分类

### Color
- 主色 / 辅色 / 强调色 / 背景色 / 文本色
- 暗色模式映射

### Spacing
- 4px / 8px / 16px / 24px / 32px / 48px / 64px（8 倍数体系）

### Typography
- 字体族 / 字号梯度 / 行高 / 字重

### Shadow
- elevation 0-5（material 风格）

### Radius
- 圆角梯度

## token 文件示例
- CSS 变量：`:root { --color-primary: #xxx; }`
- Tailwind config：`theme.extend.colors.primary = '#xxx'`
- styled-components：`theme.color.primary`
