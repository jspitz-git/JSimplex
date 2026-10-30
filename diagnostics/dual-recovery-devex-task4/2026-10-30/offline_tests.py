"""Pure Python type/schema/bit rejection tests. Never imports guard/launcher."""
import sys,unittest,copy,math,json
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D));import audit

def valid():
 cases=[]
 for T in ('Float32','Float64'):
  for layout in ('sparse','dense'):
   for bad in (False,True):
    matrix=audit.expected_matrix(T,layout);zero=audit.bits(0,T)
    stats=dict(seconds=.1,bytes=0,events=0,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
    samples=[dict(stats,index=k,solve_entries=int(bad),stop_entries=int(bad),finite=True,reliable=not bad,owners_preserved=True,point_bits=[audit.bits(.5 if bad else 1,T)]+[zero]*63,rhs_bits=matrix[0::64],absolute_bits=audit.bits(32 if bad else 0,T),relative_bits=audit.bits(1/3 if bad else 0,T)) for k in range(1,8)]
    cases.append(dict(type=T,layout=layout,unreliable=bad,dimension=64,matrix_bits=matrix,nnz=sum(b!=zero for b in matrix),warm=[dict(stats) for _ in range(3)],samples=samples,preparation=dict(stats),post_warm_gc=dict(stats),solve_entries_total=10 if bad else 0,stop_entries_total=10 if bad else 0,retained_julia_bytes=1024))
 return dict(side='reference',cases=cases)
class AuditTests(unittest.TestCase):
 def test_valid(self):self.assertTrue(audit.check_cost(valid(),'reference'))
 def test_ordinary_summary(self):
  text='Test Summary: | Pass Fail Total Time\nTASK4_RED | 7 1 8 1.0s\n'
  self.assertEqual(audit.test_summary(text,'TASK4_RED'),dict(Pass=7,Fail=1,Total=8))
 def test_missing_summary(self):
  with self.assertRaises(ValueError):audit.test_summary('ERROR','TASK4_RED')
 def test_matrix_anchors(self):
  T='Float64';sparse=audit.expected_matrix(T,'sparse');dense=audit.expected_matrix(T,'dense')
  self.assertEqual(sum(v!=audit.bits(0,T) for v in sparse),190)
  self.assertEqual(sparse[0],audit.bits(64,T))
  self.assertEqual(sparse[64],audit.bits(1/64,T))
  self.assertEqual(sparse[1],audit.bits(5/64,T))
  self.assertEqual(sparse[128],audit.bits(0,T))
  self.assertEqual(dense[128],audit.bits(-3/64,T))
 def test_comparison(self):
  a=valid();b=valid();b['side']='candidate'
  self.assertEqual(len(audit.compare_cost(a,b)),8)
  for key in ('bytes','events'):
   bad=copy.deepcopy(b)
   for q in bad['cases'][0]['samples']:q[key]+=1
   with self.assertRaises(ValueError):audit.compare_cost(a,bad)
  bad=copy.deepcopy(b);bad['cases'][0]['retained_julia_bytes']+=1
  with self.assertRaises(ValueError):audit.compare_cost(a,bad)
 def test_bad_values(self):
  mutations=[lambda r:r['cases'].pop(),lambda r:r['cases'][0].update(dimension=True),lambda r:r['cases'][0].update(nnz=True),lambda r:r['cases'][0].update(unreliable=0),lambda r:r['cases'][0].update(solve_entries_total=False),lambda r:r['cases'][0].update(stop_entries_total=False),lambda r:r['cases'][0]['samples'].pop(),lambda r:r['cases'][0]['warm'].pop(),lambda r:r['cases'][0]['samples'][0].update(bytes=True),lambda r:r['cases'][0]['samples'][0].update(events=1.0),lambda r:r['cases'][0]['samples'][0].update(seconds=float('nan')),lambda r:r['cases'][0]['samples'][0].update(gc_seconds=float('inf')),lambda r:r['cases'][0]['samples'][0].update(compile_seconds=.1),lambda r:r['cases'][0]['samples'][0].update(recompile_seconds=.1),lambda r:r['cases'][0]['samples'][0].update(finite=1),lambda r:r['cases'][0]['samples'][0].update(owners_preserved=1),lambda r:r['cases'][0]['samples'][0].update(index=True),lambda r:r['cases'][0]['samples'][0].update(solve_entries=False),lambda r:r['cases'][0]['samples'][0].update(point_bits=['bad']),lambda r:r['cases'][0]['samples'][0].update(rhs_bits=['bad']),lambda r:r['cases'][0].update(matrix_bits=['bad']),lambda r:r['cases'][0]['samples'][0].update(relative_bits='bad')]
  for i,mutate in enumerate(mutations):
   with self.subTest(case=i):
    r=valid();mutate(r)
    with self.assertRaises((ValueError,KeyError)):audit.check_cost(r,'reference')
if __name__=='__main__':unittest.main()
