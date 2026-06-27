# 降级兜底机制(DeepSeek · 自动无缝)

> 配额耗尽时自动切 DeepSeek,执行不打断用户,验收时透明化告知。

---

## 触发方式

**决策**: 自动无缝降级(A方案),执行时不打断,验收时透明化标记。

捕获以下错误自动触发降级:
- `429` (rate limit)
- `quota_exceeded` / `insufficient_quota` (配额耗尽)
- `model_overloaded` (模型过载)

---

## 降级链

**决策**: 直接跳 DeepSeek,不做三级降级链(简单,且 ZCode Coding Plan 不含 DeepSeek,切换零成本)。

```
正常态: 各工具用主力模型
  GLM-5.2(ZCode) / Sonnet(Cursor) / Claude4(Trae)
        │
   捕获 429/quota_exceeded/model_overloaded
        │
        ▼
自动切 DeepSeek(deepseek-v4-pro/flash)
        │
   执行任务(不打断用户)
        │
   状态文件标记 degraded: true
        │
        ▼
验收时: 报告高亮"⚠️ 本任务降级执行,建议人工复核"
        │
   DeepSeek 也限流?
        │
        ▼
暂停 + 人工介入(保存状态,等待配额恢复,支持断点续跑)
```

---

## 双通道接入(A+C 组合)

**决策**: A+C 组合,按场景选择。

### 方案A: ZCode config 切换(保留 ZCode 工具能力)

**适用**: 子任务需要 ZCode 的工具能力(文件读写/MCP/代码执行)。

**流程**:
```
1. 备份当前 config: cp config.json config.json.bak
2. 写入 DeepSeek config:
   {
     "provider": {
       "deepseek": {
         "kind": "openai-compatible",
         "options": {"baseURL": "https://api.deepseek.com", "apiKey": "sk-xxx"}
       }
     },
     "model": {"main": "deepseek/deepseek-chat"}
   }
3. 执行任务: node zcode.cjs --prompt "..." --cwd {project}
4. 恢复 config: mv config.json.bak config.json
```

**⚠️ 副作用**: 降级期间 ZCode GUI 会话也会切到 DeepSeek,所以方案A适合**短时任务**(单子任务级),执行完立即恢复。

### 方案C: DeepSeek API 直连(零干扰)

**适用**: 编排层自身逻辑需要 LLM(如结果摘要、复杂度判断),且不想干扰任何工具会话。

**流程**:
```bash
curl -s https://api.deepseek.com/chat/completions \
  -H "Authorization: Bearer sk-xxx" \
  -H "content-type: application/json" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"..."}]}'
```

**✓ 优点**: 完全不碰 ZCode 环境,零干扰。

---

## 透明化标记

降级执行的任务在状态文件标记:
```json
{
  "degraded": true,
  "degraded_reason": "quota_exhausted",
  "original_model": "glm-5.2",
  "actual_model": "deepseek-chat"
}
```

**验收报告高亮**:
```
⚠️ 降级任务提示(建议人工复核):
  [T2] 积分累积API — 因配额耗尽从 GLM-5.2 降级到 DeepSeek 执行
```

**核心逻辑**: 执行时不打断(保效率),验收时必告知(保安全)。

---

## 实测验证(2026-06-26)

| 测试项 | 结果 |
|--------|------|
| DeepSeek Anthropic 兼容接口 | ✅ 连通 |
| DeepSeek OpenAI 兼容接口 | ✅ 连通 |
| ZCode config 切换 DeepSeek | ✅ 成功响应 |
| config 格式 | `model.main` = `"deepseek/deepseek-chat"` 字符串格式 |

---

## DeepSeek API key 说明

- **来源**: 用户自行配置(非 ZCode Coding Plan 包含)
- **成本**: 按量自费(deepseek-v4-pro/flash)
- **角色**: 终极兜底——所有主力模型都挂了,DeepSeek 接管
- **可行性**: 研究表明小模型+语义缓存组合,准确率仍能保持 96%,成本只增加 4%
