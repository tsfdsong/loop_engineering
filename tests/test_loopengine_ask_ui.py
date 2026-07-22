import threading
import unittest
import urllib.error
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
            result_holder: list[list[str] | None] = [None]
            session_ready = threading.Event()

            def run() -> None:
                with mgr.session(token=token) as s:
                    session_ready.set()
                    result_holder[0] = s.wait_result(5)

            th = threading.Thread(target=run)
            th.start()
            self.assertTrue(session_ready.wait(2))

            url = f"http://127.0.0.1:{ui.port}/submit?token={urllib.parse.quote(token)}"
            data = urllib.parse.urlencode({"selected": "a"}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=2) as resp:
                self.assertEqual(resp.status, 200)
            th.join(5)
            self.assertEqual(result_holder[0], ["a"])
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
            result_holder: list[list[str] | None] = [None]
            session_ready = threading.Event()

            def run() -> None:
                with mgr.session(token=token) as s:
                    session_ready.set()
                    result_holder[0] = s.wait_result(5)

            th = threading.Thread(target=run)
            th.start()
            self.assertTrue(session_ready.wait(2))

            url = f"http://127.0.0.1:{ui.port}/submit?token={urllib.parse.quote(token)}"
            data = urllib.parse.urlencode([("selected", "a"), ("selected", "c")]).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=2) as resp:
                self.assertEqual(resp.status, 200)
            th.join(5)
            self.assertEqual(sorted(result_holder[0] or []), ["a", "c"])
        finally:
            ui.stop()

    def test_bad_token_forbidden(self):
        mgr = AskSessionManager(timeout_sec=5)
        token = mgr.new_token()
        payload = {
            "question": "Q",
            "options": [
                {"id": "a", "label": "A (推荐)", "recommended": True},
                {"id": "b", "label": "B"},
            ],
            "multiSelect": False,
        }
        ui = AskUIServer(mgr, host="127.0.0.1", port=0)
        ui.start(payload, token)
        try:
            bad = "wrong-token"
            get_url = f"http://127.0.0.1:{ui.port}/?token={urllib.parse.quote(bad)}"
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(get_url, timeout=2)
            self.assertEqual(ctx.exception.code, 403)

            post_url = f"http://127.0.0.1:{ui.port}/submit?token={urllib.parse.quote(bad)}"
            data = urllib.parse.urlencode({"selected": "a"}).encode()
            req = urllib.request.Request(post_url, data=data, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=2)
            self.assertEqual(ctx.exception.code, 403)
        finally:
            ui.stop()


if __name__ == "__main__":
    unittest.main()
