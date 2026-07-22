"""FastMCP server and orchestration for AskUserQuestion."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from loopengine_ask.session import AskSessionManager, BusyError
from loopengine_ask.session import TimeoutError as SessionTimeoutError
from loopengine_ask.ui import AskUIServer, open_browser
from loopengine_ask.validate import validate_ask_args

mcp = FastMCP("loopengine-ask")
_MANAGER = AskSessionManager(timeout_sec=600)


def run_ask_user_question(raw: dict) -> dict:
    """Validate args, open browser UI, wait for user selection, return result."""
    payload = validate_ask_args(raw)

    token = _MANAGER.new_token()
    ui = AskUIServer(_MANAGER)

    try:
        with _MANAGER.session(token=token) as session:
            ui.start(payload, token)
            if not open_browser(ui.url):
                raise RuntimeError("browser_error: failed to open browser")
            selected = session.wait_result(_MANAGER.timeout_sec)
    except SessionTimeoutError:
        raise
    except BusyError:
        raise RuntimeError("busy")
    finally:
        ui.stop()

    return {
        "question": payload["question"],
        "selectedOptions": selected,
    }


@mcp.tool(name="AskUserQuestion")
def AskUserQuestion(question: str, options: list, multiSelect: bool = False) -> str:
    result = run_ask_user_question(
        {"question": question, "options": options, "multiSelect": multiSelect}
    )
    return json.dumps(result, ensure_ascii=False)
