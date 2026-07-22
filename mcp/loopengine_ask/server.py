"""FastMCP server and orchestration for AskUserQuestion."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from loopengine_ask.session import AskSessionManager, BusyError
from loopengine_ask.session import TimeoutError as SessionTimeoutError
from loopengine_ask.ui import AskUIServer, open_browser
from loopengine_ask.validate import validate_ask_args

mcp = FastMCP("loopengine-ask")


def run_ask_user_question(raw: dict) -> dict:
    """Validate args, open browser UI, wait for user selection, return result."""
    payload = validate_ask_args(raw)

    mgr = AskSessionManager(timeout_sec=600)
    token = mgr.new_token()
    ui = AskUIServer(mgr)

    ui.start(payload, token)
    try:
        if not open_browser(ui.url):
            raise RuntimeError("browser_error: failed to open browser")

        with mgr.session(token=token) as session:
            selected = session.wait_result(mgr.timeout_sec)

        return {
            "question": payload["question"],
            "selectedOptions": selected,
        }
    except SessionTimeoutError:
        raise
    except BusyError:
        raise RuntimeError("busy")
    finally:
        ui.stop()


@mcp.tool(name="AskUserQuestion")
def AskUserQuestion(question: str, options: list, multiSelect: bool = False) -> str:
    result = run_ask_user_question(
        {"question": question, "options": options, "multiSelect": multiSelect}
    )
    return json.dumps(result, ensure_ascii=False)
