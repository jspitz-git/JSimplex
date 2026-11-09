import importlib.util
import unittest
import tempfile
import json
import contextlib
import io
from pathlib import Path
from unittest.mock import patch

spec=importlib.util.spec_from_file_location("experiment",Path(__file__).with_name("run.py"))
run=importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)

class HarnessTests(unittest.TestCase):
    def endpoint(self, **changes):
        d=dict(input_sha=run.expected_sha,arch='aarch64',threads=1,blas_threads=1,
               seconds=500.,loop=499.,mode_initial=1,mode_refactors=2,refactors=2,status='OPTIMAL',
               original_feasible=True)
        d.update(changes)
        return d

    def test_plan_and_reversal(self):
        jobs=list(run.schedule())
        self.assertEqual(len(run.combinations),22)
        self.assertEqual(sum(j[2]=='unit' for j in jobs),11)
        self.assertEqual(sum(j[2]=='shadow' for j in jobs),22)
        first=[(p,q,n.split('.')[0]) for p,q,n in jobs if n.endswith('.1')]
        second=[(p,q,n.split('.')[0]) for p,q,n in jobs if n.endswith('.2')]
        self.assertEqual(len(first),44)
        self.assertEqual(second,list(reversed(first)))

    def test_false_optimal_fails(self):
        with self.assertRaises(AssertionError):
            run.final_check(self.endpoint(original_feasible=False))

    def test_nonoptimal_is_recordable(self):
        run.final_check(self.endpoint(status='NUMERICAL_ERROR',original_feasible=False))

    def test_invalid_timing_fails(self):
        for t in (float('nan'),float('inf'),-1.):
            with self.assertRaises(AssertionError):
                run.final_check(self.endpoint(seconds=t))

    def test_modes_and_threads(self):
        for kwargs in (dict(mode_refactors=1),dict(threads=2),dict(input_sha='wrong')):
            with self.assertRaises(AssertionError):
                run.final_check(self.endpoint(**kwargs))

    def test_plain_match_does_not_assert_trace(self):
        d=self.endpoint()
        d.update({k:d.get(k,1) for k in run.final_keys})
        with patch.object(run,'load',return_value=d),patch.object(run,'digest',return_value='sha'):
            result=run.compare(Path('/unused'),'candidate.1')
        self.assertTrue(result['exact_endpoint'])
        self.assertNotIn('exact_trace',result)

class PartialSummaryTests(unittest.TestCase):
    def test_unverified_quartet_stays_out_of_timings(self):
        spec=importlib.util.spec_from_file_location("summary",Path(__file__).with_name("summarize.py"))
        summary=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(summary)
        with tempfile.TemporaryDirectory() as temporary:
            out=Path(temporary)
            for name,data in (("sources.json",{}),("source-provenance.json",{"sources":{}}),("status.json",{"state":"running"})):
                (out/name).write_text(json.dumps(data))
            folder=out/"test"/"dantzig";folder.mkdir(parents=True)
            for name in ("reference.1","candidate.1","candidate.2","reference.2"):
                (folder/(name+".toml")).write_text('status = "OPTIMAL"')
            jobs=[("test","dantzig",n) for n in ("reference.1","candidate.1","candidate.2","reference.2")]
            with patch.object(summary,"out",out),patch.object(summary.run,"schedule",side_effect=lambda:iter(jobs)), \
                 patch.object(summary.run,"combinations",[("test","dantzig")]), \
                 patch.object(summary.run,"digest",return_value=run.expected_sha),contextlib.redirect_stdout(io.StringIO()):
                summary.main()
            self.assertFalse((out/"pairs.csv").exists())
            result=json.loads((out/"partial-verification.json").read_text())
            self.assertFalse(result["complete"])
            self.assertEqual(result["verified"],{})

if __name__=='__main__':
    unittest.main()
