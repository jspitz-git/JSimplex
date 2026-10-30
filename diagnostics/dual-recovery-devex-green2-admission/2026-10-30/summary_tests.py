"""Source-derived normal Julia Test rendering; pure parser tests, no Julia."""
import importlib.util,sys,unittest
from pathlib import Path
target=Path(sys.argv.pop(1));sys.path.insert(0,str(target.parent));spec=importlib.util.spec_from_file_location('summary_audit',target);A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
class NonverboseSummary(unittest.TestCase):
 def test_successful_nested_testsets_do_not_need_printed_child_rows(self):
  log=''.join('TASK4_INCLUDED '+p+'\n' for p in A.C.includes())
  log+='Test Summary: | Pass Total Time\nTASK4_GREEN | 6000 6000 1.0s\nTASK4_GREEN_COMPLETED\n'
  try:r=A.ordinary(log)
  except ValueError as error:self.fail(str(error))
  self.assertEqual(r,dict(Pass=6000,Total=6000))
if __name__=='__main__':unittest.main()
