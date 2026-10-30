"""New GREEN2 refusal tests; no launch/seal/guard/Julia execution."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
import common as C
import audit_reviewed as audit
class Checks(unittest.TestCase):
 def test_prior_time_never_reset(self):
  self.assertEqual(C.accumulate([33.35953255696222,494.6009602919803]),527.9604928489425)
  self.assertEqual(1800-C.accumulate([33.35953255696222,494.6009602919803]),1272.0395071510575)
 def test_bad_times_rejected(self):
  for value in [True,False,-1,0,float('nan'),float('inf'),'494']:
   with self.subTest(value=value),self.assertRaises(ValueError):C.accumulate([value])
 def test_inventory_membership_and_target(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'input';p.write_bytes(b'EXACT')
   good=dict(files=[str(p)],trees=[],inputs=[str(p)],inventory={str(p):dict(resolved=str(p),sha256=C.sha(p))})
   C.check_inventory(good,[str(p)],[str(p)])
   for key in ('files','inventory','inputs'):
    bad=copy.deepcopy(good);bad[key]=[] if key!='inventory' else {}
    with self.subTest(key=key),self.assertRaises(ValueError):C.check_inventory(bad,[str(p)],[str(p)])
   p.write_bytes(b'CHANGED')
   with self.assertRaises(ValueError):C.check_inventory(good,[str(p)],[str(p)])
 def test_stored_failed_green_rejected(self):
  log=(C.OLD_GREEN/'green/guard/run.log').read_text()
  with self.assertRaises(ValueError):audit.ordinary(log)
 def test_ordinary_accepts_only_wholly_green_exact_includes(self):
  log=''.join('TASK4_INCLUDED '+p+'\n' for p in C.includes())+'Test Summary: | Pass Total Time\nTASK4_GREEN | 6000 6000 1.0s\n  TASK4_POST_FALLBACK | 46 46 0.1s\nTASK4_GREEN_COMPLETED\n'
  self.assertEqual(audit.ordinary(log)['Pass'],6000)
  for bad in [log.replace('6000 6000','5999 6000'),log.replace('TASK4_GREEN_COMPLETED',''),log.replace('TASK4_INCLUDED endpoint.jl\n',''),log.replace('46 46','45 45'),log+'ERROR: broken\n',log+log]:
   with self.subTest(log=bad[-90:]),self.assertRaises(ValueError):audit.ordinary(bad)
 def test_endpoint_preserved_real_values_and_bad_mutations(self):
  import tomllib
  records=tomllib.loads((C.OLD_GREEN/'green/result.toml').read_text())['cases']
  audit.endpoint(records)
  mutations=[('iterations',True),('factorizations',0),('point',[True,0]),('witness',[2,0]),('final_ftran',3),('final_btran',5),('retained_julia_bytes',False),('original_primal_certified',False)]
  for key,value in mutations:
   bad=copy.deepcopy(records);bad[0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):audit.endpoint(bad)
  bad=copy.deepcopy(records);bad[1]['type']=bad[0]['type']
  with self.assertRaises(ValueError):audit.endpoint(bad)
  for key,value in [('seconds',float('nan')),('bytes',True),('events',-1),('compile_seconds','0')]:
   bad=copy.deepcopy(records);bad[0]['whole_fallback'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):audit.endpoint(bad)
 def test_budget_and_process_controls(self):
  done=dict(elapsed_inclusive_seconds=500.,total_inclusive_seconds=1027.9604928489425,limit_seconds=1800,supervisor_accepted=True)
  sup=dict(accepted=True,returncode=0,elapsed_seconds=499.,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,abnormal_cleanup_attempted=False,child_cleanup_attempted=False)
  proc=dict(returncode=0,reason='exit0',pins_unchanged=True,command=C.command())
  audit.process(done,sup,proc)
  for obj,key,value in [(done,'total_inclusive_seconds',500.),(done,'total_inclusive_seconds',1801.),(done,'supervisor_accepted',False),(done,'elapsed_inclusive_seconds',True),(sup,'soft_timeout',True),(sup,'returncode',1),(proc,'returncode',False),(proc,'reason','exit1'),(proc,'pins_unchanged',False),(proc,'command',['other'])]:
   args=[copy.deepcopy(v) for v in (done,sup,proc)];index=0 if obj is done else 1 if obj is sup else 2;args[index][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):audit.process(*args)
 def test_resource_and_closure_controls(self):
  good={'available_kib':8*1024**2,'swap_used_kib':0};audit.resource(good)
  for bad in [dict(good,available_kib=True),dict(good,available_kib=1),dict(good,swap_used_kib=2*1024**2)]:
   with self.assertRaises(ValueError):audit.resource(bad)
 def test_admission_required_exact_scope(self):
  seal=dict(head='a'*40,phase='green2',command=C.command())
  ad=dict(accepted=True,scope='numerical_admission',phase='green2',head='a'*40,command=C.command())
  C.admission_fields(seal,ad,'a'*40)
  for key,value in [('accepted',1),('phase','green'),('head','b'*40),('scope','offline_preparation'),('command',['other'])]:
   bad=copy.deepcopy(ad);bad[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):C.admission_fields(seal,bad,'a'*40)
 def test_canonical_failure_record_without_result(self):
  original=C.OUT
  with tempfile.TemporaryDirectory() as t:
   try:
    C.OUT=Path(t)
    self.assertFalse(audit.main())
    r=json.loads((Path(t)/'audit.json').read_text())
    self.assertIs(r['accepted'],False);self.assertIn('FileNotFoundError',r['error'])
   finally:C.OUT=original
 def test_attempt_and_output_reservations(self):
  for name in ('attempt.json','guard','result.toml','completion.json','audit.json'):
   with self.subTest(name=name),tempfile.TemporaryDirectory() as t:
    p=Path(t);C.ensure_unused(p);(p/name).touch()
    with self.assertRaises(ValueError):C.ensure_unused(p)
 def test_definitions_only_launcher_import(self):
  import importlib.util
  spec=importlib.util.spec_from_file_location('reviewed_launcher',Path(__file__).with_name('launch-reviewed.py'))
  launch=importlib.util.module_from_spec(spec);spec.loader.exec_module(launch)
  self.assertEqual(Path(launch.audit.__file__).resolve(),Path(audit.__file__).resolve())
  self.assertNotIn('supervisor_reviewed',sys.modules)
  self.assertFalse(C.OUT.exists())
 def test_real_prior_failed_time_not_waived(self):
  used,facts=C.prior()
  self.assertEqual(used,527.9604928489425)
  self.assertEqual([f['accepted'] for f in facts],[True,False])
 def test_exact_corrected_fixture_graph(self):
  q=C.fixtures()
  self.assertEqual((q['program_count'],q['fixture_count'],q['include_edges']),(15,2,14))
 def test_exact_fixed_command_and_environment(self):
  self.assertEqual(C.command()[-1],str(C.PREPARED/'green.jl'))
  self.assertIn('--project='+str(C.PREPARED/'overlays/candidate'),C.command())
  self.assertEqual(C.environment()['TASK4_OUTPUT'],str(C.OUT/'result.toml'))
  self.assertEqual(C.environment()['JULIA_NUM_THREADS'],'1')
 def test_nonverbose_parent_success_needs_no_printed_child(self):
  log=''.join('TASK4_INCLUDED '+p+'\n' for p in C.includes())+'Test Summary: | Pass Total Time\nTASK4_GREEN | 6000 6000 1.0s\nTASK4_GREEN_COMPLETED\n'
  self.assertEqual(audit.ordinary(log),dict(Pass=6000,Total=6000))
if __name__=='__main__':unittest.main()
