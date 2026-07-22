# 在 OpenCode 安装 LoopEngine

需要已安装 [OpenCode](https://opencode.ai)。

在 `opencode.json` 的 `plugin` 里加入：

```json
{
  "plugin": ["loopengine@git+https://github.com/tsfdsong/loopengine.git"]
}
```

重启 OpenCode。用 skill 工具加载 `loop` / `go` 等即可。

验证：问「LoopEngine 能做什么」。

| 动作 | 工具 |
|------|------|
| 待办 | `todowrite` |
| 派 subagent | `task` |
| 加载技能 | `skill` |
| 读文件 | `read` |
| 改文件 | `apply_patch` |
| 跑命令 | `bash` |
