# 设计文档外部仓

主仓不放大段 spec/plan。可选设计文档在独立仓库：

| 项 | 值 |
|---|---|
| 仓库 | `https://github.com/tsfdsong/loop_engineering_specs` |
| 本地 | `~/.loopengine/specs/` |

```bash
mkdir -p ~/.loopengine
git clone https://github.com/tsfdsong/loop_engineering_specs ~/.loopengine/specs
# 更新：cd ~/.loopengine/specs && git pull
```

clone 失败不影响 `python3 install.py install`。

引用时用章节号（如 `spec §15.3`），不要绑死本机路径。

| 症状 | 处理 |
|------|------|
| 目录空 | 手动 clone |
| 内容旧 | `git pull` |
| 测试要求强制有 specs | `LOOPENGINE_REQUIRE_SPECS=1` |
