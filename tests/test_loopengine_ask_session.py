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
                s.wait_result(0.2)

    def test_submit_from_thread_delivers_selected(self):
        mgr = AskSessionManager(timeout_sec=2.0)

        def submitter():
            time.sleep(0.1)
            self.assertTrue(mgr.submit("t1", ["a", "b"]))

        th = threading.Thread(target=submitter)
        with mgr.session(token="t1") as s:
            th.start()
            result = s.wait_result(1.0)
            th.join()
        self.assertEqual(result, ["a", "b"])

    def test_submit_wrong_token_returns_false(self):
        mgr = AskSessionManager(timeout_sec=2.0)
        with mgr.session(token="t1") as s:
            self.assertFalse(mgr.submit("wrong", ["x"]))
            s.set_result(["ok"])
            self.assertEqual(s.wait_result(0.5), ["ok"])


if __name__ == "__main__":
    unittest.main()
