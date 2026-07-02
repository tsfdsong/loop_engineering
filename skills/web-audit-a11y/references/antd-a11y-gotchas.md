# Antd a11y 已知问题

## 默认没问题（Antd 5.x 已修）

- ✅ Modal 自动管理 focus trap
- ✅ Dropdown 有 `aria-expanded`
- ✅ Form label 关联 input
- ✅ Button 有 `role="button"`

## 仍需手动关注

### 1. Icon-only Button

```tsx
// ❌ axe 会报 "Buttons must have discernible text"
<Button icon={<DeleteOutlined />} />

// ✅ 加 aria-label
<Button icon={<DeleteOutlined />} aria-label="删除" />
```

### 2. 自定义 Tooltip 替代品

Antd `Tooltip` 默认有 `role="tooltip"`，但如果用自定义 hover 替代：
```tsx
// ❌
<div onMouseEnter={showHint}>...</div>

// ✅
<Tooltip title="..."><span>...</span></Tooltip>
```

### 3. Modal 内嵌表单

Antd Modal 自动 `aria-modal="true"`，但若自定义 footer：
```tsx
// ❌ axe 报 focus trap 问题
<Modal footer={<button onClick={onCancel}>取消</button>}>...</Modal>

// ✅ 用 Antd 标准 footer 模式
<Modal onCancel={onCancel} footer={null}>
  <Button onClick={onCancel}>取消</Button>
</Modal>
```

### 4. 颜色对比

Antd 默认主题在白底上对比度 4.5:1（合规），但自定义 token：
```tsx
// ❌ antd ConfigProvider 自定义浅色 → 可能不达标
<ConfigProvider theme={{ token: { colorPrimary: "#abcdef" } }}>

// ✅ 跑 axe color-contrast 验证
```

### 5. 动态加载内容

Spin / Skeleton 默认 `aria-live="polite"`，但自定义 loader：
```tsx
// ❌
<div className="custom-loader" />

// ✅
<div className="custom-loader" role="status" aria-live="polite">加载中...</div>
```

## Antd 5 升级修复

Antd 5.x 比 4.x 改善：
- 全部 Icon 组件自动带 `aria-hidden`
- Form 自动加 `aria-required` / `aria-invalid`
- Table 加 `role="table"` + `aria-sort`

如果还在 Antd 4.x，建议升级。
