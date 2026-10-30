"""New cost schema/clock/refusal tests only; no Julia, guard or executable main."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
import common as C
import cost_checks as K
import audit
def valid(side):
 stats=dict(seconds=.001,bytes=64,events=1,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
 cases=[]
 for T,layout,bad in K.KEYS:
  matrix=K.expected_matrix(T,layout);zero=K.bits(0,T)
  samples=[dict(stats,index=i,solve_entries=int(bad),stop_entries=int(bad),finite=True,reliable=not bad,owners_preserved=True,absolute_bits=K.bits(32 if bad else 0,T),relative_bits=K.bits(1/3 if bad else 0,T),point_bits=[K.bits(.5 if bad else 1,T)]+[zero]*63,rhs_bits=matrix[0::64]) for i in range(1,8)]
  cases.append(dict(type=T,layout=layout,unreliable=bad,dimension=64,matrix_bits=matrix,nnz=190 if layout=='sparse' else 4096,warm=[dict(stats) for _ in range(3)],samples=samples,preparation=dict(stats),post_warm_gc=dict(stats),solve_entries_total=10 if bad else 0,stop_entries_total=10 if bad else 0,retained_julia_bytes=1000,policy_solve_tolerance_bits=K.bits(2.**(-15 if T=='Float32' else -44),T)))
 return dict(side=side,cases=cases)
class Cost(unittest.TestCase):
 def test_valid_whole_records(self):
  self.assertTrue(K.check_cost(valid('reference'),'reference'))
  self.assertTrue(K.check_cost(valid('candidate'),'candidate'))
 def test_literal_anchors(self):
  a=K.expected_matrix('Float64','sparse');b=K.expected_matrix('Float64','dense')
  self.assertEqual((a[0],a[64],a[1],a[128],b[128]),('4050000000000000','3f90000000000000','3fb4000000000000','0000000000000000','bfa8000000000000'))
  self.assertEqual([K.bits(2.**-15,'Float32'),K.bits(2.**-44,'Float64')],['38000000','3d30000000000000'])
 def test_malformed_case_and_profile_refusals(self):
  mutations=[lambda r:r['cases'].pop(),lambda r:r['cases'].reverse(),lambda r:r['cases'][0].update(dimension=True),lambda r:r['cases'][0].update(nnz=True),lambda r:r['cases'][0].update(unreliable=0),lambda r:r['cases'][0].update(solve_entries_total=False),lambda r:r['cases'][0].update(stop_entries_total=False),lambda r:r['cases'][0]['samples'].pop(),lambda r:r['cases'][0]['warm'].pop(),lambda r:r['cases'][0]['samples'][0].update(bytes=True),lambda r:r['cases'][0]['samples'][0].update(events=1.0),lambda r:r['cases'][0]['samples'][0].update(seconds=float('nan')),lambda r:r['cases'][0]['samples'][0].update(gc_seconds=float('inf')),lambda r:r['cases'][0]['samples'][0].update(compile_seconds=.1),lambda r:r['cases'][0]['samples'][0].update(recompile_seconds=.1),lambda r:r['cases'][0]['samples'][0].update(finite=1),lambda r:r['cases'][0]['samples'][0].update(owners_preserved=1),lambda r:r['cases'][0]['samples'][0].update(index=True),lambda r:r['cases'][0]['samples'][0].update(solve_entries=False),lambda r:r['cases'][0]['samples'][0].update(point_bits=['bad']),lambda r:r['cases'][0]['samples'][0].update(rhs_bits=['bad']),lambda r:r['cases'][0].update(matrix_bits=['bad']),lambda r:r['cases'][0]['samples'][0].update(relative_bits='bad'),lambda r:r['cases'][0].update(policy_solve_tolerance_bits='bad'),lambda r:r['cases'][0].update(retained_julia_bytes=True),lambda r:r['cases'][0]['warm'][0].update(bytes=False)]
  for i,mutation in enumerate(mutations):
   with self.subTest(i=i):
    r=valid('reference');mutation(r)
    with self.assertRaises((ValueError,KeyError)):K.check_cost(r,'reference')
 def test_complete_comparison_without_allocation_waiver(self):
  ref=valid('reference');can=valid('candidate');q=K.comparison_data(ref,can)
  self.assertTrue(q['accepted']);self.assertEqual(len(q['cases']),8)
  for key in ('bytes','events'):
   bad=copy.deepcopy(can)
   for s in bad['cases'][0]['samples']:s[key]+=1
   report=K.comparison_data(ref,bad)
   self.assertFalse(report['accepted']);self.assertEqual(len(report['cases']),8)
   with self.assertRaises(ValueError):K.compare_cost(ref,bad)
  bad=copy.deepcopy(can);bad['cases'][0]['retained_julia_bytes']+=1
  self.assertFalse(K.comparison_data(ref,bad)['accepted'])
 def test_normal_summary_no_nested_rows(self):
  log='Test Summary: | Pass Total Time\nTASK4_COST | 272 272 1.0s\nTASK4_COST_COMPLETED reference\n'
  self.assertEqual(audit.ordinary(log,'reference-cost')['Pass'],272)
  for bad in [log.replace('272 272','271 271'),log.replace('reference','candidate'),log+log,'ERROR: failure\n'+log,log.replace('TASK4_COST_COMPLETED reference','')]:
   with self.assertRaises(ValueError):audit.ordinary(bad,'reference-cost')
 def test_real_base_time_and_phase_order(self):
  used,facts=C.prior('reference-cost');self.assertEqual(used,1033.6005972509156)
  self.assertEqual([x['accepted'] for x in facts],[True,False,True])
  self.assertEqual(C.TOTAL-used,766.3994027490844)
  with self.assertRaises((ValueError,FileNotFoundError)):C.prior('candidate-cost')
  with self.assertRaises(ValueError):C.out('green2')
 def test_inventory_and_interpreter_side(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'input';p.write_bytes(b'exact')
   pins=dict(files=[str(p)],trees=[],inputs=[],inventory={str(p):dict(resolved=str(p),sha256=C.sha(p))})
   C.check_inventory(pins,[str(p)])
   for key,value in [('files',[]),('inputs',[str(p)]),('inventory',{})]:
    bad=copy.deepcopy(pins);bad[key]=value
    with self.assertRaises(ValueError):C.check_inventory(bad,[str(p)])
 def test_admission_phase_and_command(self):
  phase='reference-cost';seal=dict(phase=phase,head='a'*40,command=C.command(phase));ad=dict(accepted=True,scope='numerical_admission',phase=phase,head='a'*40,command=C.command(phase))
  C.admission_fields(seal,ad,'a'*40,phase)
  for k,v in [('accepted',1),('phase','candidate-cost'),('head','b'*40),('scope','offline_preparation'),('command',['other'])]:
   bad=copy.deepcopy(ad);bad[k]=v
   with self.assertRaises(ValueError):C.admission_fields(seal,bad,'a'*40,phase)
 def test_shared_clock_never_reset(self):
  used=1033.6005972509156
  good=dict(elapsed_inclusive_seconds=100.,total_inclusive_seconds=used+100.,limit_seconds=1800,supervisor_accepted=True)
  sup=dict(accepted=True,returncode=0,elapsed_seconds=99.,soft_timeout=False,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False,abnormal_cleanup_attempted=False,child_cleanup_attempted=False)
  proc=dict(returncode=0,reason='exit0',pins_unchanged=True,command=C.command('reference-cost'))
  audit.process(good,sup,proc,'reference-cost',used)
  for key,value in [('total_inclusive_seconds',100.),('total_inclusive_seconds',1801.),('elapsed_inclusive_seconds',True),('supervisor_accepted',False)]:
   bad=copy.deepcopy(good);bad[key]=value
   with self.assertRaises(ValueError):audit.process(bad,sup,proc,'reference-cost',used)
 def test_canonical_failure_record_and_attempt_refusal(self):
  original=C.RUN
  with tempfile.TemporaryDirectory() as t:
   try:
    C.RUN=Path(t);C.out('reference-cost').mkdir()
    self.assertFalse(audit.main('reference-cost'))
    self.assertIs(C.read(C.out('reference-cost')/'audit.json')['accepted'],False)
    with self.assertRaises(ValueError):C.ensure_unused('reference-cost')
   finally:C.RUN=original
 def test_definitions_only_imports(self):
  import seal,launch,close
  self.assertNotIn('guard_reviewed',sys.modules);self.assertNotIn('supervisor_reviewed',sys.modules)
  self.assertFalse(C.RUN.exists())
if __name__=='__main__':unittest.main()
