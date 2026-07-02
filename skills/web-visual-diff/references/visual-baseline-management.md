# 基线管理

## 生命周期

```
首次跑 → 生成基线（写入 e2e/__snapshots__/）
  ↓
后续跑 → 对比基线
  ├─ 无差异 → 通过
  └─ 有差异 → 输出 diff.png + 报告
      ├─ 预期变更 → 接受（更新基线）
      └─ 意外变更 → 修复代码
```

## 接受新基线

### 方式 1: 命令行 flag（推荐 CI 流程）

```bash
# CI 失败时，开发者本地接受变更
npx playwright test visual.spec.ts --update-snapshots
git add e2e/__snapshots__/
git commit -m "chore(visual): update baseline after <变更描述>"
```

### 方式 2: GitHub PR 模板提示

在 `.github/pull_request_template.md` 加：

```markdown
## 视觉回归检查
- [ ] 截图测试通过（`npx playwright test`）
- [ ] 如有 baseline 更新，已说明原因
- [ ] baseline 文件已提交
```

### 方式 3: 交互式审批

用 `playwright`'s `--ui` 模式开 diff viewer：

```bash
npx playwright test --ui
# 打开 http://localhost:9229 看每个失败的 diff
# 接受/拒绝/调整
```

## 基线更新规范

**DO**：
- 一次 PR 只更新一类基线（"只改 theme" → 只更新 theme 截图）
- 在 commit message 写明原因
- 大批量更新（>20 个截图）拆成多个 PR

**DON'T**：
- 不要 `--update-snapshots` 后不看不看 diff 直接 commit
- 不要把 baseline 文件加到 `.gitignore`
- 不要在 PR 里更新 baseline 但不跑测试

## 跨环境基线同步

- 本地生成的 baseline 必须和 CI 跑出来**视觉一致**（见 `pixelmatch-config.md` § 字体一致性）
- 用 Git LFS 存大 baseline 文件（>1MB）
- baseline 目录加入 `prettier` 自动格式化（保证图片以外文件干净）
