import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('long_audit',Path(__file__).with_name('long_audit.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class AuditTests(unittest.TestCase):
 def valid(self):
  return ({'reason':'exit0','returncode':0,'pins_unchanged':True},
   {'mode':'counted','solver_returned':True,'counter_labels':['_original_optimality_certified'],
    'result':{'recorder_tail':{'windows':1},'status':'OPTIMAL','original_primal_feasible':True,'counts':{'_original_optimality_certified':1}}},
   [{'reason':'final_partial','phase':'phase_two','accepted_steps':2,'seconds':1.0,'counter_deltas':[1]}])
 def test_certified_phase_two(self):
  self.assertTrue(m.audit(*self.valid())['chronology_reference_success'])
 def test_prefix_is_incomplete(self):
  p,r,w=self.valid();r['result']['status']='ITERATION_LIMIT';self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_phase_name_alone_is_insufficient(self):
  p,r,w=self.valid();w[0]['accepted_steps']=0;self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_auxiliary_is_not_phase_two(self):
  p,r,w=self.valid();w[0]['phase']='auxiliary';self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_exit_and_pins_required(self):
  for key,value in [('reason','wall_limit'),('returncode',-15),('pins_unchanged',False)]:
   p,r,w=self.valid();p[key]=value;self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_feasible_certificate_and_counters_required(self):
  p,r,w=self.valid();r['result']['original_primal_feasible']=False;self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
  p,r,w=self.valid();r['result']['counts']['_original_optimality_certified']=0;self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
  p,r,w=self.valid();w[0]['counter_deltas']=[0];self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_incomplete_outputs(self):
  p,r,w=self.valid()
  for args in [(None,r,w),(p,None,w),(p,r,None),(p,r,[])]:self.assertFalse(m.audit(*args)['chronology_reference_success'])
 def test_final_window_required(self):
  p,r,w=self.valid();w[0]['reason']='periodic';self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_missing_zero_counter_window(self):
  p,r,w=self.valid();r['result']['recorder_tail']['windows']=2;self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
 def test_plain_does_not_claim_observed_phase(self):
  p,r,w=self.valid();r['mode']='plain';self.assertFalse(m.audit(p,r,w)['chronology_reference_success'])
if __name__=='__main__':unittest.main()
