"""Localhost HTTP UI for AskUserQuestion."""

from __future__ import annotations

import html
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from loopengine_ask.session import AskSessionManager

_SUBMITTED_HTML = (
    "<!DOCTYPE html><html><head><meta charset=\"utf-8\"></head>"
    "<body><p>已提交，可关闭</p></body></html>"
)


def open_browser(url: str) -> bool:
    """Open URL in the system browser; return False on failure."""
    try:
        return bool(webbrowser.open(url, new=2))
    except Exception:
        return False


def _render_html(payload: dict, token: str) -> str:
    question = html.escape(payload["question"])
    options = payload["options"]
    multi_select = bool(payload.get("multiSelect", False))
    token_q = urllib.parse.quote(token)
    action = f"/submit?token={token_q}"

    parts = [
        "<!DOCTYPE html>",
        "<html><head><meta charset=\"utf-8\"><title>AskUserQuestion</title>",
        "<style>",
        "body{font-family:system-ui,sans-serif;max-width:36rem;margin:2rem auto;padding:0 1rem;}",
        "h1{font-size:1.25rem;}",
        ".option{margin:0.5rem 0;}",
        "button{padding:0.5rem 1rem;cursor:pointer;}",
        ".recommended{font-weight:600;}",
        "</style></head><body>",
        f"<h1>{question}</h1>",
    ]

    if multi_select:
        parts.append(f'<form method="POST" action="{html.escape(action)}">')
        for opt in options:
            opt_id = html.escape(opt["id"])
            label = html.escape(opt["label"])
            rec = ' class="recommended"' if opt.get("recommended") else ""
            parts.append(
                f'<div class="option"><label{rec}>'
                f'<input type="checkbox" name="selected" value="{opt_id}"> {label}'
                f"</label></div>"
            )
        parts.append('<button type="submit">确认</button></form>')
    else:
        for opt in options:
            opt_id = html.escape(opt["id"])
            label = html.escape(opt["label"])
            rec = ' class="recommended"' if opt.get("recommended") else ""
            parts.append(
                f'<form method="POST" action="{html.escape(action)}" class="option">'
                f'<input type="hidden" name="selected" value="{opt_id}">'
                f'<button type="submit"{rec}>{label}</button>'
                f"</form>"
            )

    parts.append("</body></html>")
    return "\n".join(parts)


class AskUIServer:
    """Serves a localhost HTML page and accepts POST /submit for selections."""

    def __init__(
        self,
        mgr: AskSessionManager,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self._mgr = mgr
        self._host = host
        self._port = port
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._payload: dict | None = None
        self._token: str | None = None

    def start(self, payload: dict, token: str) -> None:
        self._payload = payload
        self._token = token
        handler_class = self._make_handler()
        self._server = ThreadingHTTPServer((self._host, self._port), handler_class)
        self._port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    @property
    def port(self) -> int:
        if self._server is None:
            raise RuntimeError("server not started")
        return self._port

    @property
    def url(self) -> str:
        if self._token is None:
            raise RuntimeError("server not started")
        token_q = urllib.parse.quote(self._token)
        return f"http://{self._host}:{self.port}/?token={token_q}"

    def _make_handler(self):
        mgr = self._mgr
        payload = self._payload
        expected_token = self._token

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args) -> None:
                return

            def _token_from_query(self) -> str | None:
                parsed = urllib.parse.urlparse(self.path)
                tokens = urllib.parse.parse_qs(parsed.query).get("token", [])
                if not tokens or tokens[0] != expected_token:
                    return None
                return tokens[0]

            def _send_plain(self, code: int, body: bytes) -> None:
                self.send_response(code)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path not in ("", "/"):
                    self.send_error(404)
                    return
                if self._token_from_query() is None:
                    self._send_plain(403, b"Forbidden")
                    return
                body = _render_html(payload, expected_token).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path != "/submit":
                    self.send_error(404)
                    return
                token = self._token_from_query()
                if token is None:
                    self._send_plain(403, b"Forbidden")
                    return

                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length).decode("utf-8")
                selected = urllib.parse.parse_qs(raw).get("selected", [])

                if payload.get("multiSelect") and not selected:
                    self._send_plain(400, b"Bad Request")
                    return

                if not mgr.submit(token, selected):
                    self._send_plain(403, b"Forbidden")
                    return

                body = _SUBMITTED_HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
