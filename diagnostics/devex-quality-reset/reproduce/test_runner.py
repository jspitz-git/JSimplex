import ast,contextlib,io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run
class QueueTests(unittest.TestCase):
    def test_schedule(self):
        jobs=list(run.schedule());self.assertEqual(len(jobs),34)
        self.assertEqual(len(set(jobs)),34)
        self.assertEqual(sum(i=='runtime' and j.endswith('-audit') for p,i,j in jobs),6)
        first=[(p,i,n[:-2]) for p,i,n in jobs if n.endswith('.1')]
        second=[(p,i,n[:-2]) for p,i,n in jobs if n.endswith('.2')]
        self.assertEqual(second,first[::-1])
    def test_predecessor_repair_and_running_block(self):
        for s in ('running','failed','interrupted_requires_recovery','waiting_for_previous_measurements'):
            self.assertFalse(run.predecessor_ready({'state':s}))
        self.assertTrue(run.predecessor_ready({'state':'finished'}))
    def test_started_marker_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'started.json';run.create(p,{'begun':True})
            with self.assertRaises(FileExistsError):run.create(p,{'begun':False})
            self.assertTrue(json.loads(p.read_text())['begun'])
    def test_children_inherit_locks(self):
        tree=ast.parse(Path(run.__file__).read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='Popen']
        self.assertEqual(len(calls),1)
        self.assertTrue(any(k.arg=='pass_fds' and isinstance(k.value,ast.Name) and k.value.id=='locks' for k in calls[0].keywords))
    def test_partial_unverified_quartet_not_timed(self):
        import summarize
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);(out/'source-provenance.json').write_text('{"sources":{}}')
            (out/'sources.json').write_text('{}');(out/'references.json').write_text('{}')
            (out/'status.json').write_text('{"state":"running"}')
            folder=out/'huangfu_hall-production/runtime';folder.mkdir(parents=True)
            for a in ('off','active'):
                for i in (1,2):(folder/f'{a}.{i}.toml').write_text('status="OPTIMAL"\nseconds=10.0\nloop=9.0\n')
            with patch.object(summarize,'out',out),patch.object(run,'verify_pins'),contextlib.redirect_stdout(io.StringIO()): summarize.main()
            self.assertFalse((out/'pairs.csv').exists())
            self.assertEqual(json.loads((out/'partial-verification.json').read_text())['timing'],[])
if __name__=='__main__':unittest.main()
