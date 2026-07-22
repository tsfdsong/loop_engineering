# Cursor AskUserQuestion MCP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

---
execution_path: # 用户选择后填写：subagent-driven | inline | go
---

**Spec:** `docs/2026-07-22-cursor-ask-user-question-mcp-design.md`  
**Goal:** 在 Cursor 上通过独立 MCP `loopengine-ask` 提供工具 `AskUserQuestion`（单选+多选、本地网页点选），兑现 C2；共享 AGENTS C2 与其它平台默认 MCP 不变。

**Architecture:** 仓库内纯 Python 包 `mcp/loopengine_ask/`（stdlib HTTP UI + 官方 `mcp` FastMCP）。Cursor `merge_mcp` 始终注册该 server（`python -m loopengine_ask` + `PYTHONPATH` 指向中央包/插件内 `mcp/`）。校验失败/超时/busy 返回 tool error，不降级 markdown。共享 `.plugin-template.json` 与 ZCode/Claude merge **不**注册该 server。

**Tech Stack:** Python 3.10+ · `mcp`（FastMCP）· `http.server` · `unittest` · 现有 `loopengine_install` Cursor adapter

## Verification Contract

| ID | 来源验收 | 命令/动作 | 预期 |
|----|----------|-----------|------|
| V1 | Cursor mcp.json 含 `loopengine-ask`，工具名 `AskUserQuestion` | 临时 home 跑 `CursorAdapter.merge_mcp`；`python -m loopengine_ask` 能 import；断言 mcp.json 含 server | server 键存在；command/args/env 正确 |
| V2 | 单选点选返回对应选项 | `pytest tests/test_loopengine_ask_ui.py -v`（HTTP 客户端模拟） | 返回 `selectedOptions` 含所选 id |
| V3 | 多选确认返回列表 | 同上 · multiSelect 用例 | 返回所选 id 列表 |
| V4 | 非法参数 / 超时 / busy → error；禁止 markdown 降级有文档/附录 | `pytest tests/test_loopengine_ask_validate.py tests/test_loopengine_ask_session.py -v`；读 Cursor 注入附录 | 校验/timeout/busy 失败；附录含「禁止 markdown 决策」 |
| V5 | 其它平台/template 不含该 server；共享 C2 无改 | `pytest tests/test_loopengine_ask_install_isolation.py -v`；`git diff AGENTS.md` / 读 `.plugin-template.json` | 无 `loopengine-ask`；AGENTS C2 未改 |
| V6 | 单元+集成测试绿 | `python -m unittest discover -s tests -p 'test_loopengine_ask*.py' -v` 与安装相关用例 | 退出码 0 |

## Termination Contract

**Done when:** V1–V6 全部通过；Cursor 安装路径写入 `loopengine-ask`；共享 C2 / template 未引入该 server。  
**Blocked when:** 目标环境无法稳定打开系统浏览器且用户未批准改降级策略（见 spec Stop Escalation）。  
**Degraded when:** 本轮不适用（spec 默认不降级 markdown）。  
**Handoff-required when:** Cursor 已提供原生 AskUserQuestion → 停止扩展本 MCP，回交产品决策是否退役。

## Escalation Mapping

- 执行路径：本 plan 为跨模块（MCP 包 + install + tests + 短文档）→ 推荐 **`/go`** 或 **subagent-driven** 按 task 执行；单会话可 **inline**（executing-plans）。
- Goal→loop：Cursor 无原生 Goal；子任务默认 loop（见 `docs/2026-07-21-goal-first-executor-routing-design.md`）。本 plan 不引入 Goal 路由变更。

## Non-goals

继承 spec：不改共享 C2 正文；不挂 jcodemunch/repomix/headroom；无自由文本；无 markdown 合法化兜底；无多题单次调用；不依赖 `cursor_dialog`。

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `mcp/loopengine_ask/__init__.py` | 包版本常量 |
| `mcp/loopengine_ask/__main__.py` | `python -m loopengine_ask` → 启动 MCP |
| `mcp/loopengine_ask/validate.py` | 参数校验（选项数、推荐标记） |
| `mcp/loopengine_ask/session.py` | 单飞锁、超时、token、结果 Future |
| `mcp/loopengine_ask/ui.py` | 本地 HTTP + HTML；模拟点选用 test client |
| `mcp/loopengine_ask/server.py` | FastMCP 工具 `AskUserQuestion` |
| `scripts/loopengine_install/package.py` | `build_central_package` 复制 `mcp/` |
| `scripts/loopengine_install/adapters/cursor.py` | `merge_mcp` 注册 ask；`inject_agents` 追加 Cursor 附录 |
| `scripts/loopengine_install/health.py` | 可选：Cursor 缺 ask 时告警 |
| `docs/mcp-setup-guide.md` | Cursor 专节：loopengine-ask |
| `tests/test_loopengine_ask_*.py` | 校验 / session / UI / install 隔离 |

**锁定工具 schema（全 plan 一致）：**

```python
# 输入
{
  "question": str,           # 必填
  "options": [               # 长度 2–4
    {
      "id": str,             # 稳定标识；缺省则用 label
      "label": str,          # 展示文案
      "description": str,    # 可选
      "recommended": bool,   # 可选；或 label 含 "(推荐)" / "(Recommended)"
    }
  ],
  "multiSelect": bool,       # 默认 False
}

# 成功返回（JSON 文本）
{
  "question": str,
  "selectedOptions": [str, ...]  # option id 列表
}

# 失败：MCP tool error，message 前缀之一：
# validation_error: | browser_error: | timeout | busy
```

默认超时：`ASK_TIMEOUT_SEC = 600`。

---

### Task 1: 校验模块（TDD）

**Verifies:** V4, V6

**Files:**
- Create: `mcp/loopengine_ask/__init__.py`
- Create: `mcp/loopengine_ask/validate.py`
- Create: `tests/test_loopengine_ask_validate.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_loopengine_ask_validate.py
import unittest
from loopengine_ask.validate import validate_ask_args, ValidationError

class ValidateAskArgsTest(unittest.TestCase):
    def test_ok_single_with_recommended_flag(self):
        out = validate_ask_args({
            "question": "选方案？",
            "options": [
                {"id": "a", "label": "A", "recommended": True},
                {"id": "b", "label": "B"},
            ],
        })
        self.assertFalse(out["multiSelect"])
        self.assertEqual(out["options"][0]["id"], "a")

    def test_ok_recommended_in_label(self):
        validate_ask_args({
            "question": "Q",
            "options": [
                {"label": "X (推荐)"},
                {"label": "Y"},
            ],
        })

    def test_reject_one_option(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({"question": "Q", "options": [{"label": "only (推荐)"}]})

    def test_reject_five_options(self):
        opts = [{"label": f"o{i}", "recommended": i == 0} for i in range(5)]
        with self.assertRaises(ValidationError):
            validate_ask_args({"question": "Q", "options": opts})

    def test_reject_no_recommended(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({
                "question": "Q",
                "options": [{"label": "A"}, {"label": "B"}],
            })

    def test_reject_empty_question(self):
        with self.assertRaises(ValidationError):
            validate_ask_args({
                "question": "  ",
                "options": [
                    {"label": "A (推荐)"},
                    {"label": "B"},
                ],
            })

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests — expect FAIL (import/module missing)**

```bash
cd <repo>
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_validate -v
```

Expected: FAIL（`No module named 'loopengine_ask'` 或缺符号）

- [ ] **Step 3: Minimal implementation**

```python
# mcp/loopengine_ask/__init__.py
__version__ = "0.1.0"

# mcp/loopengine_ask/validate.py
from __future__ import annotations

from typing import Any


class ValidationError(ValueError):
    pass


_REC_MARKERS = ("(推荐)", "(Recommended)", "(recommended)")


def _has_recommended(opt: dict[str, Any]) -> bool:
    if opt.get("recommended") is True:
        return True
    label = str(opt.get("label") or "")
    return any(m in label for m in _REC_MARKERS)


def validate_ask_args(raw: dict[str, Any]) -> dict[str, Any]:
    question = str(raw.get("question") or "").strip()
    if not question:
        raise ValidationError("validation_error: question required")
    options_in = raw.get("options")
    if not isinstance(options_in, list) or not (2 <= len(options_in) <= 4):
        raise ValidationError("validation_error: options must have 2–4 items")
    options: list[dict[str, Any]] = []
    for i, item in enumerate(options_in):
        if not isinstance(item, dict):
            raise ValidationError(f"validation_error: options[{i}] must be object")
        label = str(item.get("label") or "").strip()
        if not label:
            raise ValidationError(f"validation_error: options[{i}].label required")
        oid = str(item.get("id") or label).strip()
        options.append({
            "id": oid,
            "label": label,
            "description": str(item.get("description") or ""),
            "recommended": _has_recommended(item) or bool(item.get("recommended")),
        })
    if not any(_has_recommended(o) or o["recommended"] for o in options):
        # re-check using normalized labels
        if not any(_has_recommended({"label": o["label"], "recommended": o["recommended"]}) for o in options):
            raise ValidationError("validation_error: at least one option must be recommended")
    multi = bool(raw.get("multiSelect") or False)
    return {"question": question, "options": options, "multiSelect": multi}
```

Fix recommended check to a single clear path: after normalize, `if not any(o["recommended"] for o in options)` where `recommended` is set True if flag or marker in label.

- [ ] **Step 4: Re-run tests — expect PASS**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_validate -v
```

Expected: OK

- [ ] **Step 5: Commit**

```bash
git add mcp/loopengine_ask/__init__.py mcp/loopengine_ask/validate.py tests/test_loopengine_ask_validate.py
git commit -m "feat(ask): add AskUserQuestion argument validation"
```

---

### Task 2: Session 单飞 / 超时（TDD）

**Verifies:** V4, V6

**Files:**
- Create: `mcp/loopengine_ask/session.py`
- Create: `tests/test_loopengine_ask_session.py`

- [ ] **Step 1: Failing tests**

```python
# tests/test_loopengine_ask_session.py
import threading
import time
import unittest
from loopengine_ask.session import AskSessionManager, BusyError, TimeoutError

class SessionTest(unittest.TestCase):
    def test_busy_rejects_second(self):
        mgr = AskSessionManager(timeout_sec=2.0)
        started = threading.Event()
        def holder():
            with mgr.session(token="t1") as s:
                started.set()
                time.sleep(0.5)
                s.set_result(["a"])
        th = threading.Thread(target=holder)
        th.start()
        self.assertTrue(started.wait(1))
        with self.assertRaises(BusyError):
            with mgr.session(token="t2"):
                pass
        th.join()

    def test_timeout(self):
        mgr = AskSessionManager(timeout_sec=0.2)
        with self.assertRaises(TimeoutError):
            with mgr.session(token="t") as s:
                s.wait_result()  # nobody submits

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run — expect FAIL**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_session -v
```

- [ ] **Step 3: Implement `session.py`**

```python
# mcp/loopengine_ask/session.py
from __future__ import annotations

import secrets
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator


class BusyError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("busy")


class TimeoutError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("timeout")


@dataclass
class AskSession:
    token: str
    _result: list[str] | None = None
    _event: threading.Event = field(default_factory=threading.Event)

    def set_result(self, selected: list[str]) -> None:
        self._result = list(selected)
        self._event.set()

    def wait_result(self, timeout_sec: float) -> list[str]:
        if not self._event.wait(timeout_sec):
            raise TimeoutError()
        return list(self._result or [])


class AskSessionManager:
    def __init__(self, timeout_sec: float = 600.0) -> None:
        self.timeout_sec = timeout_sec
        self._lock = threading.Lock()
        self._active: AskSession | None = None

    def new_token(self) -> str:
        return secrets.token_urlsafe(16)

    @contextmanager
    def session(self, token: str | None = None) -> Iterator[AskSession]:
        tok = token or self.new_token()
        sess = AskSession(token=tok)
        with self._lock:
            if self._active is not None:
                raise BusyError()
            self._active = sess
        try:
            yield sess
        finally:
            with self._lock:
                if self._active is sess:
                    self._active = None

    def submit(self, token: str, selected: list[str]) -> bool:
        with self._lock:
            if self._active is None or self._active.token != token:
                return False
            self._active.set_result(selected)
            return True
```

Adjust tests to call `s.wait_result(mgr.timeout_sec)` or pass timeout into `wait_result`. Align `AskSession.wait_result` signature with tests.

- [ ] **Step 4: PASS + Commit**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_session -v
git add mcp/loopengine_ask/session.py tests/test_loopengine_ask_session.py
git commit -m "feat(ask): add single-flight ask session with timeout"
```

---

### Task 3: 本地 UI HTTP（无浏览器集成测）

**Verifies:** V2, V3, V6

**Files:**
- Create: `mcp/loopengine_ask/ui.py`
- Create: `tests/test_loopengine_ask_ui.py`

- [ ] **Step 1: Failing tests — start server, GET page, POST submit**

```python
# tests/test_loopengine_ask_ui.py
import json
import threading
import unittest
import urllib.parse
import urllib.request
from loopengine_ask.session import AskSessionManager
from loopengine_ask.ui import AskUIServer

class UITest(unittest.TestCase):
    def test_single_select_via_http(self):
        mgr = AskSessionManager(timeout_sec=5)
        token = mgr.new_token()
        payload = {
            "question": "选？",
            "options": [
                {"id": "a", "label": "A (推荐)", "recommended": True},
                {"id": "b", "label": "B"},
            ],
            "multiSelect": False,
        }
        ui = AskUIServer(mgr, host="127.0.0.1", port=0)
        ui.start(payload, token)
        try:
            def run():
                with mgr.session(token=token) as s:
                    self._result = s.wait_result(5)

            self._result = None
            th = threading.Thread(target=run)
            th.start()
            # POST choose a
            url = f"http://127.0.0.1:{ui.port}/submit?token={urllib.parse.quote(token)}"
            data = urllib.parse.urlencode({"selected": "a"}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=2) as resp:
                self.assertEqual(resp.status, 200)
            th.join(5)
            self.assertEqual(self._result, ["a"])
        finally:
            ui.stop()

    def test_multi_select_via_http(self):
        mgr = AskSessionManager(timeout_sec=5)
        token = mgr.new_token()
        payload = {
            "question": "多选",
            "options": [
                {"id": "a", "label": "A (推荐)", "recommended": True},
                {"id": "b", "label": "B"},
                {"id": "c", "label": "C"},
            ],
            "multiSelect": True,
        }
        ui = AskUIServer(mgr, host="127.0.0.1", port=0)
        ui.start(payload, token)
        try:
            def run():
                with mgr.session(token=token) as s:
                    self._result = s.wait_result(5)
            self._result = None
            th = threading.Thread(target=run)
            th.start()
            url = f"http://127.0.0.1:{ui.port}/submit?token={urllib.parse.quote(token)}"
            data = urllib.parse.urlencode([("selected", "a"), ("selected", "c")]).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=2) as resp:
                self.assertEqual(resp.status, 200)
            th.join(5)
            self.assertEqual(sorted(self._result), ["a", "c"])
        finally:
            ui.stop()

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run — FAIL**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_ui -v
```

- [ ] **Step 3: Implement `ui.py`**

实现要点：
- `ThreadingHTTPServer(("127.0.0.1", 0), Handler)`
- `GET /?token=` 返回 HTML：单选为 button form；多选为 checkbox + 确认
- `POST /submit?token=`：校验 token → `mgr.submit` → 返回「已提交，可关闭」
- 错误 token → 403
- `start` / `stop`；暴露 `port`、`url`
- **不**在单元测试路径调用 `webbrowser.open`（单独函数 `open_browser(url) -> bool`，server 层可注入/mock）

- [ ] **Step 4: PASS + Commit**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_ui -v
git add mcp/loopengine_ask/ui.py tests/test_loopengine_ask_ui.py
git commit -m "feat(ask): add localhost AskUserQuestion web UI"
```

---

### Task 4: FastMCP 工具 `AskUserQuestion`

**Verifies:** V1, V2, V3, V4, V6

**Files:**
- Create: `mcp/loopengine_ask/server.py`
- Create: `mcp/loopengine_ask/__main__.py`
- Create: `tests/test_loopengine_ask_server.py`

- [ ] **Step 1: Failing tests for orchestration helper（可测，不启 stdio MCP）**

```python
# tests/test_loopengine_ask_server.py
import unittest
from unittest.mock import patch
from loopengine_ask.server import run_ask_user_question
from loopengine_ask.validate import ValidationError

class ServerHelperTest(unittest.TestCase):
    def test_validation_error_no_browser(self):
        with patch("loopengine_ask.server.open_browser") as ob:
            with self.assertRaises(ValidationError):
                run_ask_user_question({"question": "", "options": []})
            ob.assert_not_called()

    def test_browser_failure(self):
        with patch("loopengine_ask.server.open_browser", return_value=False):
            with patch("loopengine_ask.server.AskUIServer") as UI:
                inst = UI.return_value
                inst.port = 9
                inst.url = "http://127.0.0.1:9/"
                with self.assertRaisesRegex(RuntimeError, "browser_error"):
                    run_ask_user_question({
                        "question": "Q",
                        "options": [
                            {"id": "a", "label": "A (推荐)"},
                            {"id": "b", "label": "B"},
                        ],
                    })

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Implement `run_ask_user_question` + FastMCP wrapper**

```python
# mcp/loopengine_ask/server.py — 核心流程（示意）
# 1. validate_ask_args
# 2. mgr.session + ui.start
# 3. open_browser(ui.url) — False → stop ui → raise RuntimeError("browser_error: ...")
# 4. wait_result(timeout) — TimeoutError → cleanup → re-raise
# 5. return {"question", "selectedOptions"}
# 6. finally ui.stop()

# FastMCP:
# mcp = FastMCP("loopengine-ask")
# @mcp.tool(name="AskUserQuestion")
# def AskUserQuestion(question: str, options: list[dict], multiSelect: bool = False) -> str:
#     result = run_ask_user_question({...})
#     return json.dumps(result, ensure_ascii=False)

# __main__.py: mcp.run()  # stdio
```

依赖：运行环境需已安装 `mcp`（与 jcodemunch 一样由用户/安装文档说明 `pip install mcp`）。在 `docs/mcp-setup-guide.md` 写明。

- [ ] **Step 3: PASS + Commit**

```bash
PYTHONPATH=mcp python3 -m unittest tests.test_loopengine_ask_server -v
git add mcp/loopengine_ask/server.py mcp/loopengine_ask/__main__.py tests/test_loopengine_ask_server.py
git commit -m "feat(ask): wire FastMCP AskUserQuestion tool"
```

---

### Task 5: 中央包复制 `mcp/` + Cursor merge 注册

**Verifies:** V1, V5, V6

**Files:**
- Modify: `scripts/loopengine_install/package.py`（`build_central_package` 增加复制 `mcp/`）
- Modify: `scripts/loopengine_install/adapters/cursor.py`（`merge_mcp`）
- Modify: `tests/test_loopengine_install_cursor.py`（或新建 `tests/test_loopengine_ask_install_isolation.py` 中的 Cursor 段）

- [ ] **Step 1: Failing install test**

```python
# tests/test_loopengine_ask_install_isolation.py（部分）
def test_cursor_merge_registers_loopengine_ask(self):
    # tempfile home + build_central_package
    # CursorAdapter().merge_mcp(ctx) 即使 mcp_bins 全空也要写入 loopengine-ask
    data = json.loads((home / ".cursor" / "mcp.json").read_text())
    self.assertIn("loopengine-ask", data["mcpServers"])
    entry = data["mcpServers"]["loopengine-ask"]
    self.assertIn("-m", entry["args"])
    self.assertIn("loopengine_ask", entry["args"])
    self.assertIn("PYTHONPATH", entry.get("env") or {})

def test_plugin_template_has_no_loopengine_ask(self):
    tmpl = json.loads((repo / ".plugin-template.json").read_text())
    self.assertNotIn("loopengine-ask", (tmpl.get("mcpServers") or {}))
```

- [ ] **Step 2: `package.py` 增加**

```python
for name in ("skills", "hooks", "commands", "mcp"):
    _copy_tree(repo_root / name, dest / name)
```

- [ ] **Step 3: 改写 `CursorAdapter.merge_mcp`**

关键行为变更：
1. **删除**「若无 jcode/repo/hdrm 则 `return []`」——`loopengine-ask` 始终注册。
2. 解析 ask 根：`ask_mcp_root = (ctx.central / "mcp").resolve()`；若插件已 sync，可用 `self.plugin_root(ctx) / "mcp"`（优先 central，fallback plugin）。
3. 写入：

```python
servers["loopengine-ask"] = {
    "command": sys.executable,
    "args": ["-m", "loopengine_ask"],
    "env": {"PYTHONPATH": str(ask_mcp_root)},
}
keys.append("loopengine-ask")
```

4. 仍按需合并 jcodemunch/repomix/headroom。
5. `merge_keys` 含 `loopengine-ask`。
6. 同步写 plugin `mcp.json` 时包含该 server。

- [ ] **Step 4: PASS + Commit**

```bash
PYTHONPATH=scripts:mcp python3 -m unittest tests.test_loopengine_ask_install_isolation -v
git add scripts/loopengine_install/package.py scripts/loopengine_install/adapters/cursor.py tests/test_loopengine_ask_install_isolation.py
git commit -m "feat(install): register Cursor-only loopengine-ask MCP"
```

---

### Task 6: Cursor 规则附录（禁止 markdown 降级）+ 文档

**Verifies:** V4, V5

**Files:**
- Modify: `scripts/loopengine_install/adapters/cursor.py`（`inject_agents`）
- Modify: `docs/mcp-setup-guide.md`
- Extend: `tests/test_loopengine_ask_install_isolation.py`

- [ ] **Step 1: 在 `inject_agents` 于写入 `loopengine-interaction.mdc` 之后追加附录（在 managed marker 之外）**

```markdown
<!-- BEGIN LOOPENGINE-CURSOR-ASK-NOTE -->
## Cursor C2 兑现说明（本平台专用 · 非共享 AGENTS 正文）

本平台通过 MCP `loopengine-ask` 提供工具 **AskUserQuestion**（本地网页点选）。
决策点必须调用该工具。若工具返回 `validation_error` / `browser_error` / `timeout` / `busy`：
**重试工具或上报阻塞**，禁止改用 markdown 列表呈现决策选项继续执行。
<!-- END LOOPENGINE-CURSOR-ASK-NOTE -->
```

**禁止**修改 `AGENTS.md` 内 `INTERACTION-RULES` 块。

- [ ] **Step 2: `docs/mcp-setup-guide.md` 增加 Cursor 小节**

内容：依赖 `pip install mcp`；安装 LoopEngine 后应出现 `loopengine-ask`；工具名 `AskUserQuestion`；故障时不要 markdown 逃逸。

- [ ] **Step 3: 测试断言**

- Cursor 注入后的 mdc 含 `LOOPENGINE-CURSOR-ASK-NOTE` 与「禁止改用 markdown」
- `AGENTS.md` 中 C2 块仍为原样（可用 marker 内文本 hash/片段断言未改，或仅断言测试未写 AGENTS）
- `.plugin-template.json` 无 `loopengine-ask`

- [ ] **Step 4: Commit**

```bash
git add scripts/loopengine_install/adapters/cursor.py docs/mcp-setup-guide.md tests/test_loopengine_ask_install_isolation.py
git commit -m "docs(cursor): note AskUserQuestion MCP and forbid markdown fallback"
```

---

### Task 7: Health（可选但建议）+ 全量回归

**Verifies:** V1, V5, V6

**Files:**
- Modify: `scripts/loopengine_install/health.py`（Cursor 已安装且 manifest 含 cursor 时，若 `~/.cursor/mcp.json` 缺 `loopengine-ask` → HealthIssue）
- Test: 扩展 isolation 或 health 测试

- [ ] **Step 1: 实现 health 检查 + 测试**
- [ ] **Step 2: 跑全套 ask 相关测试**

```bash
PYTHONPATH=scripts:mcp python3 -m unittest \
  tests.test_loopengine_ask_validate \
  tests.test_loopengine_ask_session \
  tests.test_loopengine_ask_ui \
  tests.test_loopengine_ask_server \
  tests.test_loopengine_ask_install_isolation \
  -v
```

Expected: 全部 OK

- [ ] **Step 3: 确认隔离**

```bash
grep -n 'loopengine-ask' .plugin-template.json && echo FAIL || echo OK
git diff -- AGENTS.md | head   # 应为空（本 feature 不改 AGENTS）
```

- [ ] **Step 4: Commit**

```bash
git add scripts/loopengine_install/health.py tests/
git commit -m "test(ask): cover Cursor Ask MCP health and isolation"
```

---

## Spec coverage checklist（self-review）

| Spec 项 | Task |
|---------|------|
| 独立 MCP + 本地网页 | T1–T4 |
| 单选 + 多选 | T3, T4 |
| 工具名 AskUserQuestion；共享 C2 不改 | T4, T6 |
| 仅 Cursor 安装接线 | T5, T6, T7 |
| 非法/超时/busy；不降级 markdown | T2, T4, T6 |
| template/其它平台不含 | T5, T7 |
| 测试 | 各 Task + T7 |

**Placeholder scan:** 无 TBD；schema 已锁定。  
**Type consistency:** `selectedOptions` / `BusyError` / `validation_error:` 前缀全 plan 一致。  
**Loop contract:** V1–V6 覆盖全部 Acceptance；Termination 仅四态；无 G0–G9 粘贴。

---

## 执行交接

Plan 已保存至 `docs/2026-07-22-cursor-ask-user-question-mcp-plan.md`。

三种执行方式：

1. **Subagent-Driven（推荐 · 中等复杂度）** — 每 task 新 subagent + 两阶段审查 → `subagent-driven-development`
2. **Inline Execution** — 本会话按 task 执行 → `executing-plans`
3. **/go Engineering Mode** — worktree + 自动拆分（本 plan ≥4 task / 跨模块，也适用）

选哪一种？
