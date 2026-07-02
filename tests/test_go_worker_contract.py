#!/usr/bin/env python3
"""Conformance tests for go Worker Contract v1 (C1–C6)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GO_SCRIPTS = ROOT / "skills" / "go" / "scripts"


def _load_module(name: str, rel_path: str):
    if name in sys.modules:
        return sys.modules[name]
    shared = ROOT / "skills" / "shared" / "scripts"
    if shared.is_dir() and str(shared) not in sys.path:
        sys.path.insert(0, str(shared))
    path = GO_SCRIPTS / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(GO_SCRIPTS))
    spec.loader.exec_module(module)
    sys.modules[name] = module
    return module


def init_git_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=path, check=True)
    (path / "README.md").write_text("init\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True)


class TestGoWorkerContractAssets(unittest.TestCase):
    def test_schema_and_golden_packet_files_exist(self):
        refs = ROOT / "skills" / "go" / "references"
        required = [
            refs / "worker-task-packet.schema.json",
            refs / "worker-result.schema.json",
            refs / "runtime-capabilities.schema.json",
            refs / "golden-packets" / "implement-t1.json",
            refs / "golden-packets" / "merge-resolve.json",
        ]
        for path in required:
            self.assertTrue(path.is_file(), str(path))

    def test_golden_packets_validate(self):
        wc = _load_module("worker_contract_test", "worker_contract.py")
        for name in ("implement-t1.json", "merge-resolve.json"):
            packet = wc.load_golden_packet(name)
            wc.validate_packet(packet)

    def test_routing_rules_v5_shape(self):
        text = (ROOT / "skills" / "go" / "routing-rules.yaml").read_text(encoding="utf-8")
        self.assertIn("runtimes:", text)
        self.assertIn("cursor:", text)
        self.assertIn("zcode:", text)
        self.assertNotIn("zcode_cli:", text)


class TestGoWorkerContractConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.wc = _load_module("worker_contract_c", "worker_contract.py")
        _load_module("worker_adapter_c", "worker_adapter.py")
        cls.stub_mod = _load_module("stub_adapter_c", "adapters/stub_adapter.py")
        cls.zcode_mod = _load_module("zcode_adapter_c", "adapters/zcode_subagent_adapter.py")
        cls.cursor_mod = _load_module("cursor_adapter_c", "adapters/cursor_subagent_adapter.py")
        cls.scheduler = _load_module("task_scheduler_c", "task_scheduler.py")

    def test_c1_packet_validation_rejects_invalid(self):
        adapter = self.stub_mod.StubWorkerAdapter(simulate_profile="zcode")
        bad = {"task_id": "X", "goal": "missing fields"}
        result = adapter.execute(bad)
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("missing required fields", result.get("error", ""))

    def test_c2_worktree_binding_stub_writes_only_workspace(self):
        adapter = self.stub_mod.StubWorkerAdapter(simulate_profile="zcode")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ws = root / "wt"
            ws.mkdir()
            packet = self.wc.load_golden_packet("implement-t1.json")
            packet["workspace"]["root"] = str(ws)
            packet["workspace"]["allowed_paths"] = ["app/models/points.py"]

            result = adapter.execute(packet)
            self.assertEqual(result["status"], "DONE")
            target = ws / "app/models/points.py"
            self.assertTrue(target.is_file())
            self.assertFalse((root / "app").exists())

    def test_c3_parallel_smoke_faster_than_serial(self):
        delay = 0.15
        adapter = self.stub_mod.StubWorkerAdapter(sleep_sec=delay, simulate_profile="zcode")

        def run_packet(task_id: str, workspace: Path):
            packet = self.wc.load_golden_packet("implement-t1.json")
            packet["task_id"] = task_id
            packet["workspace"]["root"] = str(workspace / task_id)
            packet["workspace"]["allowed_paths"] = [f"{task_id}.txt"]
            return adapter.execute(packet)

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            t0 = time.perf_counter()
            run_packet("T1", base)
            run_packet("T2", base)
            serial_ms = (time.perf_counter() - t0) * 1000

            results = []
            t1 = time.perf_counter()

            def worker(tid):
                results.append(run_packet(tid, base))

            threads = [threading.Thread(target=worker, args=(f"P{i}",)) for i in range(2)]
            for th in threads:
                th.start()
            for th in threads:
                th.join()
            parallel_ms = (time.perf_counter() - t1) * 1000

            self.assertEqual(len(results), 2)
            self.assertLess(parallel_ms, serial_ms * 0.85)

    def test_c4_handoff_roundtrip_in_packet(self):
        handoff_t1 = {
            "files_changed": ["app/models/points.py"],
            "new_interfaces": [{"type": "table", "name": "points"}],
            "artifacts": "done",
            "next_task_hint": "build API",
        }
        task = {
            "id": "T2",
            "name": "API",
            "files": ["app/api/points.py"],
            "depends_on": ["T1"],
        }
        packet = self.wc.build_packet_from_task(
            task,
            ROOT,
            ROOT / ".go/worktrees/T2",
            "implement API",
            handoffs=[{**handoff_t1, "task_id": "T1"}],
        )
        self.assertEqual(len(packet["context"]["handoffs"]), 1)
        self.assertEqual(packet["context"]["handoffs"][0]["new_interfaces"][0]["name"], "points")
        injected = json.dumps(packet["context"]["handoffs"])
        self.assertIn("points", injected)

    def test_c5_merge_resolve_clears_conflict_markers(self):
        adapter = self.stub_mod.StubWorkerAdapter(simulate_profile="cursor")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            conflict_file = root / "app/models/points.py"
            conflict_file.parent.mkdir(parents=True)
            conflict_file.write_text(
                "<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> branch\n",
                encoding="utf-8",
            )
            packet = self.wc.load_golden_packet("merge-resolve.json")
            packet["workspace"]["root"] = str(root)
            result = adapter.execute(packet)
            self.assertEqual(result["status"], "DONE")
            text = conflict_file.read_text(encoding="utf-8")
            self.assertNotIn("<<<<<<<", text)

    def test_c6_cross_runtime_parity_result_shape(self):
        packet = self.wc.load_golden_packet("implement-t1.json")
        with tempfile.TemporaryDirectory() as tmp:
            packet["workspace"]["root"] = str(Path(tmp) / "ws")
            z = self.stub_mod.StubWorkerAdapter(simulate_profile="zcode").execute(packet)
            c = self.stub_mod.StubWorkerAdapter(simulate_profile="cursor").execute(packet)
        z_keys = set(z.keys()) | {"runtime_meta"}
        c_keys = set(c.keys()) | {"runtime_meta"}
        self.assertEqual(z_keys, c_keys)
        for key in ("contract_version", "task_id", "status", "runtime_meta"):
            self.assertIn(key, z)
            self.assertIn(key, c)

    def test_cursor_adapter_blocked_outside_cursor(self):
        adapter = self.cursor_mod.CursorSubagentAdapter(force_blocked=True)
        packet = self.wc.load_golden_packet("implement-t1.json")
        result = adapter.execute(packet)
        self.assertEqual(result["status"], "BLOCKED")

    def test_zcode_capabilities_no_background_parallel(self):
        caps = self.zcode_mod.ZCodeSubagentAdapter().capabilities()
        self.assertFalse(caps["supports_background_parallel"])
        self.assertTrue(caps["supports_foreground_parallel"])

    def test_cursor_file_dispatch_roundtrip(self):
        bridge = _load_module("cursor_dispatch_bridge_t", "cursor_dispatch_bridge.py")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            packet = self.wc.load_golden_packet("implement-t1.json")
            packet["context"] = {"project_root": str(project), "handoffs": []}
            packet["workspace"]["root"] = str(project / "wt")
            (project / "wt").mkdir(parents=True)

            paths = bridge.enqueue_dispatch(project, packet)
            self.assertTrue(Path(paths["packet_path"]).is_file())
            self.assertTrue(Path(paths["prompt_path"]).is_file())

            result = {
                "contract_version": "1.0",
                "task_id": "T1",
                "status": "DONE",
                "handoff": {"files_changed": ["app/models/points.py"], "artifacts": "ok"},
                "runtime_meta": {"profile": "cursor", "degraded": False},
            }
            out = bridge.write_result(project, result)
            self.assertTrue(out.is_file())
            loaded = bridge.wait_for_result(project, "T1", timeout_sec=1)
            self.assertEqual(loaded["status"], "DONE")

    def test_cursor_adapter_file_bridge_receives_result(self):
        bridge = _load_module("cursor_dispatch_bridge_t2", "cursor_dispatch_bridge.py")
        import os

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            packet = self.wc.load_golden_packet("implement-t1.json")
            packet["context"] = {"project_root": str(project), "handoffs": []}
            packet["workspace"]["root"] = str(project / "wt")
            (project / "wt").mkdir(parents=True)

            result_payload = {
                "contract_version": "1.0",
                "task_id": "T1",
                "status": "DONE",
                "handoff": {"files_changed": [], "artifacts": "from host"},
                "runtime_meta": {"profile": "cursor", "degraded": False},
            }

            def host_agent():
                time.sleep(0.15)
                bridge.write_result(project, result_payload)

            os.environ["CURSOR_AGENT"] = "test"
            os.environ["LOOPENGINE_CURSOR_DISPATCH"] = "file"
            os.environ["LOOPENGINE_CURSOR_DISPATCH_POLL_SEC"] = "5"
            try:
                threading.Thread(target=host_agent, daemon=True).start()
                adapter = self.cursor_mod.CursorSubagentAdapter(use_file_bridge=True)
                out = adapter.execute(packet)
                self.assertEqual(out["status"], "DONE")
            finally:
                os.environ.pop("CURSOR_AGENT", None)
                os.environ.pop("LOOPENGINE_CURSOR_DISPATCH", None)
                os.environ.pop("LOOPENGINE_CURSOR_DISPATCH_POLL_SEC", None)

    def test_cursor_capabilities_background_parallel(self):
        caps = self.cursor_mod.CursorSubagentAdapter().capabilities()
        self.assertTrue(caps["supports_background_parallel"])

    def test_scheduler_paths_overlap_detection(self):
        self.assertTrue(
            self.scheduler.paths_overlap([
                {"files": ["a.py"]},
                {"files": ["a.py"]},
            ])
        )
        self.assertFalse(
            self.scheduler.paths_overlap([
                {"files": ["a.py"]},
                {"files": ["b.py"]},
            ])
        )

    def test_integration_execute_packet_with_git_worktree(self):
        stub = self.stub_mod.StubWorkerAdapter(simulate_profile="zcode")
        sm = _load_module("state_manager_test", "state_manager.py")
        git_ops = _load_module("git_ops_test", "git_ops.py")

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            init_git_repo(project)
            sm.create_state(project, "go/test", "feature", "L2")
            sm.atomic_update(project, lambda s: s.update({"feature_branch": "main", "base_branch": "main"}))
            task = {
                "id": "T1",
                "name": "stub task",
                "files": ["out.txt"],
                "depends_on": [],
                "status": sm.TASK_PENDING,
                "assigned_runtime": {"profile": "zcode", "adapter": "subagent"},
            }
            sm.add_tasks(project, [task])

            result = self.scheduler.execute_packet_in_worktree(
                project, task, adapter=stub, runtime_profile="zcode",
            )
            self.assertEqual(result["status"], "completed")
            head = git_ops.get_head(project)
            self.assertTrue(len(head) >= 7)


if __name__ == "__main__":
    unittest.main()
