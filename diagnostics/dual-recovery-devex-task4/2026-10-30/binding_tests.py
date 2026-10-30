"""New offline binding regressions only; no main/guard/Julia invocation."""
import unittest,tempfile,sys,importlib.util,importlib.machinery
from pathlib import Path
import common as C
import binding_checks as B
D=Path(__file__).resolve().parent
class BindingTests(unittest.TestCase):
 def test_interpreter_valid_and_wrong_path(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp)/'python';p.write_bytes(b'bound interpreter');other=Path(tmp)/'other';other.write_bytes(p.read_bytes())
   seal={'guard_python':str(p)};pins={'inventory':{str(p):{'resolved':str(p.resolve()),'sha256':C.sha(p)}}}
   B.interpreter(seal,pins,str(p))
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(other))
   p.write_bytes(b'changed')
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(p))
   with self.assertRaises(ValueError):B.interpreter({'guard_python':True},pins,str(p))
 def test_changed_interpreter_resolution(self):
  with tempfile.TemporaryDirectory() as tmp:
   a=Path(tmp)/'a';b=Path(tmp)/'b';p=Path(tmp)/'python'
   a.write_bytes(b'same');b.write_bytes(b'same');p.symlink_to(a)
   seal={'guard_python':str(p)};pins={'inventory':{str(p):{'resolved':str(a.resolve()),'sha256':C.sha(p)}}}
   B.interpreter(seal,pins,str(p));p.unlink();p.symlink_to(b)
   with self.assertRaises(ValueError):B.interpreter(seal,pins,str(p))
 def test_head_at_every_boundary(self):
  seal={'head':'a'*40};ad={'head':'a'*40};B.head(seal,ad,'a'*40)
  with self.assertRaises(ValueError):B.head(seal,ad,'b'*40)
  with self.assertRaises(ValueError):B.head(seal,{'head':'b'*40},'a'*40)
  with self.assertRaises(ValueError):B.head(seal,ad,True)
 def test_auditor_bound_before_shadow_directory(self):
  # Definitions-only import. This would fail for the original late import.
  spec=importlib.util.spec_from_file_location('task4_reviewed_launch_definitions',D/'launch-reviewed.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as tmp:
   shadow=Path(tmp)/'audit.py';shadow.write_text('raise RuntimeError("unexpected shadow execution")\n')
   old=importlib.machinery.PathFinder.find_spec('audit',[tmp,str(D)])
   self.assertEqual(Path(old.origin),shadow)
   sys.path.insert(0,tmp)
   try:self.assertEqual(Path(module.audit.__file__).resolve(),(D/'audit_reviewed.py').resolve())
   finally:sys.path.pop(0)
  self.assertEqual(module.audit.__name__,'audit_reviewed')
if __name__=='__main__':unittest.main()
