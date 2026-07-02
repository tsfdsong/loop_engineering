# data-testid 约定

## 命名规则

| 组件类型 | 命名 | 示例 |
|---|---|---|
| 模态框根 | `<domain>-modal` | `login-modal`, `mcp-debug-modal` |
| 模态框内输入 | `<domain>-<field>-input` | `login-username-input` |
| 提交按钮 | `<domain>-submit` 或 `<domain>-<action>` | `skill-publish-button` |
| 列表卡片 | `<domain>-card` | `skill-card`, `mcp-card` |
| 列表空态 | `<domain>-<list>-empty` | `skill-list-empty` |
| Hub 切换器 | `hub-switcher` | — |
| Hub 子项 | `data-hub-key="<key>"` | `data-hub-key="skill"` |
| 通用 loading | `loading-skeleton` | — |
| 通用空态 | `empty-state-container` | — |
| 通用错误 toast | `error-toast` | — |

## 层级

- ✅ 根容器：1 个 `data-testid`
- ✅ 关键交互元素：1 个 `data-testid`
- ❌ 不要给每个 div 加 testid（噪音）

## Antd 组件示例

```tsx
// Modal
<Modal data-testid="login-modal" title="登录" open={open} onCancel={onCancel} footer={null}>
  <Input data-testid="login-username-input" />
  <Input.Password data-testid="login-password-input" />
  <Button data-testid="login-submit" htmlType="submit">登录</Button>
</Modal>

// Card
<Card data-testid="skill-card" hoverable onClick={...}>...</Card>

// 列表
<List
  dataSource={items}
  renderItem={(item) => <List.Item data-testid="skill-card" key={item.id}>...</List.Item>}
/>
```

## 选择器注册

**所有 testid 必须在 `e2e/utils/selectors.ts` 集中导出**：

```typescript
export const SEL = {
  loginModal: "login-modal",
  loginSubmit: "login-submit",
  // ...
} as const;
```

**禁止**：测试文件里直接写 `page.locator('[data-testid="..."]')`（散落难维护）。

## 反例

```tsx
// ❌ 不要这样
<div data-testid="wrapper">
  <div data-testid="inner-wrapper">
    <div data-testid="content">
      <span data-testid="text">...</span>
    </div>
  </div>
</div>

// ✅ 简化为
<div data-testid="content">...</div>
```
