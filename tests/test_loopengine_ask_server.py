import threading
import time
import unittest
import urllib.parse
import urllib.request
from unittest.mock import patch

from loopengine_ask.server import run_ask_user_question
from loopengine_ask.ui import AskUIServer
from loopengine_ask.validate import ValidationError

_VALID_ARGS = {
    "question": "选方案？",
    "options": [
        {"id": "a", "label": "A (推荐)", "recommended": True},
        {"id": "b", "label": "B"},
    ],
}


class ServerTest(unittest.TestCase):
    @patch("loopengine_ask.server.open_browser")
    def test_validation_error_empty_question(self, mock_open_browser):
        with self.assertRaises(ValidationError):
            run_ask_user_question(
                {
                    "question": "  ",
                    "options": [
                        {"label": "A (推荐)"},
                        {"label": "B"},
                    ],
                }
            )
        mock_open_browser.assert_not_called()

    @patch("loopengine_ask.server.open_browser", return_value=False)
    def test_browser_error_stops_ui(self, mock_open_browser):
        with patch.object(AskUIServer, "stop") as mock_stop:
            with self.assertRaises(RuntimeError) as ctx:
                run_ask_user_question(_VALID_ARGS)
            self.assertIn("browser_error", str(ctx.exception))
            mock_stop.assert_called_once()
        mock_open_browser.assert_called_once()

    @patch("loopengine_ask.server.open_browser")
    def test_happy_path_auto_submit(self, mock_open_browser):
        def open_and_submit(url: str) -> bool:
            parsed = urllib.parse.urlparse(url)
            port = parsed.port
            token = urllib.parse.parse_qs(parsed.query)["token"][0]

            def submitter() -> None:
                time.sleep(0.15)
                submit_url = (
                    f"http://127.0.0.1:{port}/submit?"
                    f"token={urllib.parse.quote(token)}"
                )
                data = urllib.parse.urlencode({"selected": "a"}).encode()
                req = urllib.request.Request(submit_url, data=data, method="POST")
                urllib.request.urlopen(req, timeout=2)

            threading.Thread(target=submitter, daemon=True).start()
            return True

        mock_open_browser.side_effect = open_and_submit
        result = run_ask_user_question(_VALID_ARGS)

        self.assertEqual(result["question"], "选方案？")
        self.assertEqual(result["selectedOptions"], ["a"])
        mock_open_browser.assert_called_once()


if __name__ == "__main__":
    unittest.main()
