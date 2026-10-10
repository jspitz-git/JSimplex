"""Exercise runner safety with small Python children; never start Julia."""
import fcntl
import json
import importlib.util
from unittest.mock import patch
import os
import signal
import time
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RUNNER = Path(__file__).with_name('guarded_run.py')


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'src'
        self.source.mkdir()
        (self.source / 'a.jl').write_text('baseline')
        self.child = self.root / 'child.py'
        self.child.write_text("print('executed')\n")
        self.pins = self.root / 'pins.json'
        self.out = self.root / 'attempt-1'
        self.lock = self.root / 'numerical.lock'

    def invoke(self, *args):
        return subprocess.run([sys.executable, str(RUNNER), *map(str, args)],
                              capture_output=True, text=True, timeout=15)

    def freeze(self):
        result = self.invoke('freeze', self.pins, '--tree', self.source,
                             '--file', self.child, '--file', sys.executable)
        self.assertEqual(result.returncode, 0, result.stderr)

    def run_child(self, seconds=5):
        return self.invoke('run', self.pins, self.out, '--lock', self.lock,
                           '--seconds', seconds, '--', sys.executable, self.child)

    def report(self):
        return json.loads((self.out / 'process.json').read_text())

    def test_records_success_identity_and_resource_limits(self):
        self.child.write_text("import os,resource,json\nprint(json.dumps({'vm':resource.getrlimit(resource.RLIMIT_AS)[0], 'threads':os.environ['JULIA_NUM_THREADS'], 'blas':os.environ['OPENBLAS_NUM_THREADS']}))\n")
        self.freeze()
        result = self.run_child()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.report()
        self.assertEqual(report['reason'], 'exit0')
        self.assertTrue(report['pins_unchanged'])
        self.assertGreater(report['child']['start_ticks'], 0)
        self.assertEqual(report['child']['pid'], report['child']['pgid'])
        child = json.loads((self.out / 'run.log').read_text())
        self.assertEqual(child, {'vm': 8 * 1024**3, 'threads': '1', 'blas': '1'})

    def test_refuses_changed_pin_before_child(self):
        self.freeze()
        (self.source / 'a.jl').write_text('changed')
        self.assertNotEqual(self.run_child().returncode, 0)
        self.assertFalse((self.out / 'run.log').exists())

    def test_refuses_added_source(self):
        self.freeze()
        (self.source / 'new.jl').write_text('new dependency')
        self.assertNotEqual(self.run_child().returncode, 0)
        self.assertFalse((self.out / 'run.log').exists())

    def test_rejects_directory_symlink_added_to_pinned_tree(self):
        self.freeze()
        external = self.root / 'external'
        external.mkdir()
        (external / 'extra.jl').write_text('new code')
        (self.source / 'alias').symlink_to(external, target_is_directory=True)
        result = self.run_child()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.out / 'run.log').exists())

    def test_refuses_directory_symlink_at_freeze(self):
        external = self.root / 'external'
        external.mkdir()
        (external / 'extra.jl').write_text('new code')
        (self.source / 'alias').symlink_to(external, target_is_directory=True)
        result = self.invoke('freeze', self.pins, '--tree', self.source)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.pins.exists())

    def test_refuses_missing_pin(self):
        self.freeze()
        (self.source / 'a.jl').unlink()
        self.assertNotEqual(self.run_child().returncode, 0)

    def test_refuses_existing_attempt_without_overwriting(self):
        self.freeze()
        self.out.mkdir()
        (self.out / 'marker').write_text('preserved')
        self.assertNotEqual(self.run_child().returncode, 0)
        self.assertEqual((self.out / 'marker').read_text(), 'preserved')
        self.assertFalse((self.out / 'run.log').exists())

    def test_refuses_lock_contention_even_without_julia(self):
        self.freeze()
        with self.lock.open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            result = self.run_child()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ownership', result.stderr)
        self.assertFalse(self.out.exists())

    def test_modified_pin_during_run_invalidates_exit_zero(self):
        self.child.write_text(f"from pathlib import Path\nPath({str(self.source / 'a.jl')!r}).write_text('changed while running')\n")
        self.freeze()
        self.assertNotEqual(self.run_child().returncode, 0)
        self.assertFalse(self.report()['pins_unchanged'])
        self.assertEqual(self.report()['returncode'], 0)

    def test_timeout_stops_owned_child_and_preserves_evidence(self):
        self.child.write_text('import time\ntime.sleep(30)\n')
        self.freeze()
        self.assertNotEqual(self.run_child(seconds=0.1).returncode, 0)
        report = self.report()
        self.assertEqual(report['reason'], 'wall_time')
        self.assertNotEqual(report['returncode'], 0)
        self.assertTrue((self.out / 'resources.jsonl').exists())

    def test_timeout_kills_descendant_ignoring_term(self):
        marker = self.root / 'grandchild.pid'
        grandchild = ("import os,signal,time;from pathlib import Path;"
                      "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                      f"Path({str(marker)!r}).write_text(str(os.getpid()));time.sleep(30)")
        self.child.write_text("import subprocess,sys,time\n"
                              f"subprocess.Popen([sys.executable,'-c',{grandchild!r}])\n"
                              "time.sleep(30)\n")
        self.freeze()
        result = self.run_child(seconds=0.5)
        self.assertNotEqual(result.returncode, 0)
        pid = int(marker.read_text())
        try:
            status = Path(f'/proc/{pid}/stat')
            running = status.exists() and status.read_text().split(') ')[1][0] != 'Z'
            self.assertFalse(running, 'owned descendant survived the guard')
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_natural_exit_with_live_descendant_is_not_success(self):
        marker = self.root / 'grandchild.pid'
        grandchild = ("import os,signal,time;from pathlib import Path;"
                      "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
                      f"Path({str(marker)!r}).write_text(str(os.getpid()));time.sleep(30)")
        self.child.write_text("import subprocess,sys,time\nfrom pathlib import Path\n"
                              f"subprocess.Popen([sys.executable,'-c',{grandchild!r}])\n"
                              f"while not Path({str(marker)!r}).exists():time.sleep(0.01)\n")
        self.freeze()
        result = self.run_child()
        pid = int(marker.read_text())
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(self.report()['reason'], 'unexpected_descendants')
            stat = Path(f'/proc/{pid}/stat')
            self.assertTrue(not stat.exists() or stat.read_text().split(') ')[1][0] == 'Z')
        finally:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_runner_sigterm_cleans_child_and_leaves_unrelated_process(self):
        self.child.write_text('import time\ntime.sleep(30)\n')
        self.freeze()
        unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(30)'])
        runner = subprocess.Popen([sys.executable, str(RUNNER), 'run', str(self.pins),
                                   str(self.out), '--lock', str(self.lock), '--seconds',
                                   '20', '--', sys.executable, str(self.child)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while not (self.out / 'current.json').exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue((self.out / 'current.json').exists())
            runner.terminate()
            runner.communicate(timeout=8)
            self.assertNotEqual(runner.returncode, 0)
            self.assertEqual(self.report()['reason'], 'interrupted')
            self.assertIsNone(unrelated.poll())
            child_pid = self.report()['child']['pid']
            self.assertFalse(Path(f'/proc/{child_pid}').exists())
        finally:
            if runner.poll() is None:
                runner.terminate()
                runner.communicate(timeout=8)
            unrelated.terminate()
            unrelated.wait(timeout=5)

    def test_memory_and_live_process_preflight_fail_closed(self):
        # Mock only host sensors; the real runner must refuse before any child.
        import argparse
        spec = importlib.util.spec_from_file_location('guard_under_test', RUNNER)
        guard = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(guard)
        self.freeze()
        args = argparse.Namespace(pins=self.pins, out=self.out, lock=self.lock,
                                  seconds=5, command=[sys.executable, str(self.child)])
        for sample in ({'available_kib': 1, 'swap_used_kib': 0},
                       {'available_kib': 8*1024**2, 'swap_used_kib': 2*1024**2}):
            with patch.object(guard, 'memory', return_value=sample):
                with self.assertRaisesRegex(ValueError, 'memory pressure'):
                    guard.run(args)
            self.assertFalse(self.out.exists())
        with patch.object(guard, 'live_julia', return_value=[{'pid': 123}]):
            with self.assertRaisesRegex(ValueError, 'live Julia'):
                guard.run(args)
        self.assertFalse(self.out.exists())

    def test_nonzero_exit_is_not_success(self):
        self.child.write_text('raise SystemExit(23)\n')
        self.freeze()
        self.assertNotEqual(self.run_child().returncode, 0)
        self.assertEqual(self.report()['returncode'], 23)

    def test_launch_failure_has_final_report(self):
        self.freeze()
        result = self.invoke('run', self.pins, self.out, '--lock', self.lock,
                             '--seconds', 5, '--', '/nonexistent/executable')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.report()['reason'], 'launch_error')

    def test_pin_manifest_is_immutable(self):
        self.freeze()
        before = self.pins.read_bytes()
        result = self.invoke('freeze', self.pins, '--tree', self.source)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.pins.read_bytes(), before)

    def test_refuses_forbidden_content_alias(self):
        forbidden = self.root / 'big.mps'
        forbidden.write_text('excluded input')
        alias = self.root / 'innocent.mps'
        alias.write_bytes(forbidden.read_bytes())
        result = self.invoke('freeze', self.pins, '--input', alias,
                             '--forbidden', forbidden, '--file', self.child)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('forbidden', result.stderr)
        self.assertFalse(self.pins.exists())


if __name__ == '__main__':
    unittest.main()
