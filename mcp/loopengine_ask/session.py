"""Single-flight ask session with timeout."""

from __future__ import annotations

import secrets
import threading
from contextlib import contextmanager
from typing import Iterator


class BusyError(RuntimeError):
    """Raised when a second session is attempted while one is active."""

    def __init__(self) -> None:
        super().__init__("busy")


class TimeoutError(RuntimeError):
    """Raised when wait_result exceeds the allotted time."""

    def __init__(self) -> None:
        super().__init__("timeout")


class AskSession:
    """Active ask session bound to a token."""

    def __init__(self, token: str) -> None:
        self.token = token
        self._event = threading.Event()
        self._lock = threading.Lock()
        self._result: list[str] | None = None

    def set_result(self, selected: list[str]) -> None:
        with self._lock:
            self._result = list(selected)
        self._event.set()

    def wait_result(self, timeout_sec: float) -> list[str]:
        if not self._event.wait(timeout_sec):
            raise TimeoutError()
        with self._lock:
            assert self._result is not None
            return list(self._result)


class AskSessionManager:
    """Manages at most one active ask session at a time."""

    def __init__(self, timeout_sec: float = 600) -> None:
        self.timeout_sec = timeout_sec
        self._lock = threading.Lock()
        self._active: AskSession | None = None
        self._active_token: str | None = None

    def new_token(self) -> str:
        return secrets.token_urlsafe()

    @contextmanager
    def session(self, token: str | None = None) -> Iterator[AskSession]:
        if token is None:
            token = self.new_token()

        with self._lock:
            if self._active is not None:
                raise BusyError()
            ask_session = AskSession(token)
            self._active = ask_session
            self._active_token = token

        try:
            yield ask_session
        finally:
            with self._lock:
                self._active = None
                self._active_token = None

    def submit(self, token: str, selected: list[str]) -> bool:
        with self._lock:
            if self._active is None or self._active_token != token:
                return False
            ask_session = self._active

        ask_session.set_result(selected)
        return True
