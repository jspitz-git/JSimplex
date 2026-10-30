"""Offline tests: detect missing, changed, unlisted or escaping fixture inputs."""
from pathlib import Path
import hashlib,json,sys,tempfile,unittest
sys.dont_write_bytecode=True
import fixture_check as F
ROOT=Path(sys.argv.pop(1));MANIFEST=Path(sys.argv.pop(1))
class Fixtures(unittest.TestCase):
 def test_all_original_green_dependencies_available(self):
  try:r=F.check(ROOT,json.loads(MANIFEST.read_text()))
  except ValueError as e:self.fail(str(e))
  self.assertEqual(r['program_count'],15)
  self.assertEqual(r['fixture_count'],2)
  self.assertEqual(r['include_edges'],14)
 def fixture(self,source='read_mps(joinpath(@__DIR__,"fixtures","x.mps"))'):
  t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup);p=Path(t.name)
  (p/'green.jl').write_text(source+'\n');(p/'fixtures').mkdir();(p/'fixtures/x.mps').write_bytes(b'EXACT INPUT\n')
  m={'entry':'green.jl','programs':{'green.jl':F.sha(p/'green.jl')},'fixtures':{'fixtures/x.mps':F.sha(p/'fixtures/x.mps')},'output_calls':[]}
  return p,m
 def test_missing_fixture_rejected(self):
  p,m=self.fixture();(p/'fixtures/x.mps').unlink()
  with self.assertRaisesRegex(ValueError,'missing fixture'):F.check(p,m)
 def test_changed_fixture_rejected(self):
  p,m=self.fixture();(p/'fixtures/x.mps').write_bytes(b'OTHER\n')
  with self.assertRaisesRegex(ValueError,'fixture hash'):F.check(p,m)
 def test_unlisted_input_rejected(self):
  p,m=self.fixture();m['fixtures']={}
  with self.assertRaisesRegex(ValueError,'fixture inventory'):F.check(p,m)
 def test_dynamic_input_rejected(self):
  p,m=self.fixture('read_mps(input_path)')
  with self.assertRaisesRegex(ValueError,'unsupported input'):F.check(p,m)
 def test_dynamic_include_rejected(self):
  p,m=self.fixture('include(helper)')
  with self.assertRaisesRegex(ValueError,'unsupported include'):F.check(p,m)
 def test_escaping_input_rejected(self):
  p,m=self.fixture('read_mps(joinpath(@__DIR__,"..","x.mps"))')
  with self.assertRaisesRegex(ValueError,'escaping path'):F.check(p,m)
 def test_undeclared_io_rejected(self):
  p,m=self.fixture('open(input_path)')
  with self.assertRaisesRegex(ValueError,'unclassified IO'):F.check(p,m)
 def test_changed_program_rejected(self):
  p,m=self.fixture();(p/'green.jl').write_text('read_mps(unknown)\n')
  with self.assertRaisesRegex(ValueError,'program hash'):F.check(p,m)
if __name__=='__main__':unittest.main()
