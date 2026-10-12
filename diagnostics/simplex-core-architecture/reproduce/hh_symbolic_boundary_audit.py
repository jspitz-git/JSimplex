"""Exclusive S4-F postexit audit; never rerun accepted output."""
from pathlib import Path
import json,tomllib,hashlib,shutil,math,struct,subprocess
from fractions import Fraction
root=Path.cwd();d=root/'diagnostics/simplex-core-architecture';out=d/'results/S4-F';base=root/'.superpowers/simplex-core-architecture/S4-F/boundary-1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=tomllib.loads((base/'report.toml').read_text());proc=json.loads((base/'process.json').read_text());pinpath=base.parent/'boundary-1-pins.json';pins=json.loads(pinpath.read_text());pre=json.loads((out/'preflight.json').read_text());host=json.loads((out/'host-after-boundary-1.json').read_text())
frombits=lambda x:Fraction.from_float(struct.unpack('>d',bytes.fromhex(x))[0])
def mat(q,zero=False):
 A=[[Fraction(0) for _ in range(q['n'])] for _ in range(q['m'])];offset=0 if zero else 1
 for j in range(q['n']):
  for k in range(q['colptr'][j]-offset,q['colptr'][j+1]-offset):A[q['rowval'][k]-offset][j]=frombits(q['bits'][k])
 return A
def mul(A,B):return [[sum((a*b for a,b in zip(row,col)),Fraction(0)) for col in zip(*B)] for row in A]
def sub(A,B):return [[a-b for a,b in zip(x,y)] for x,y in zip(A,B)]
def flatcolumn(A):return [a for col in zip(*A) for a in col]
exact=[]
for row in r['records']:
 A=mat(row['B1']);native=mat(row['native_after'],True)
 result={'case':row['case'],'side':row['side'],'target_native_equal':A==native}
 if row['case']<6:
  L,U=mat(row['L']),mat(row['U']);s=list(map(frombits,row['scaling_bits']));scaled=[[s[i]*x for x in A[i]] for i in range(len(A))];perm=[[scaled[i-1][j-1] for j in row['q']] for i in row['p']]
  factor=flatcolumn(sub(mul(L,U),perm));result['factor_exact_matches']=factor==[Fraction(x.replace('//','/')) for x in row['exact_factor_residual']]
  for mode,key,M in [('forward','x_bits',A),('transpose','y_bits',list(map(list,zip(*A))))]:
   v=[[frombits(x)] for x in row[key]];res=[x[0]-i for i,x in enumerate(mul(M,v),1)]
   result[mode+'_exact_matches']=res==[Fraction(x.replace('//','/')) for x in row[mode+'_exact_residual']]
 result['all_passed']=all(v for k,v in result.items() if k not in ['case','side']);exact.append(result)
rows=r['records'];success=[x for x in rows if x['case']<6];failed=[x for x in rows if x['case']==6];metrics=[v for x in rows for k,v in x.items() if k.endswith('_metrics')]
resource=[json.loads(x) for x in (base/'resources.jsonl').read_text().splitlines()]
checks={
'normal_exit':proc['returncode']==0 and proc['reason']=='exit0',
'guard_pins_unchanged':proc['pins_unchanged'],
'independent_pins':all(Path(k).resolve()==Path(v['resolved']) and sha(k)==v['sha256'] for k,v in pins['inventory'].items()),
'pin_digest':sha(pinpath)==proc['pins_sha256'],
'complete':r['complete'] and 'error' not in r,
'all179_checks':len(r['checks'])==179 and all(r['checks'].values()),
'exact_call_budget':r['entries']==pre['calls'],
'all12_case_sides':[(x['case'],x['side']) for x in rows]==[(i,s) for i in range(1,7) for s in ['reference','candidate']],
'native_loaded_pinned':pre['native_libraries'].get(r['native_path'])==r['native_sha256']==sha(r['native_path']),
'single_threads':r['threads']==r['blas_threads']==1,
'actual_package_source':r['source']==str(root/'src'),
'actual_driver':pre['driver_sha256']==sha(d/'reproduce/hh_symbolic_boundary.jl'),
'symbolic_identity_decisions':all(x['symbolic_same']==x['reuse'] for x in rows),
'candidate_pattern_rules':all(x['reuse']==(x['side']=='candidate' and x['case'] in [1,2,3,6]) for x in rows),
'new_numeric_all12':all(not x['numeric_same'] for x in rows),
'success10':len(success)==10 and all(x['status']==0 and x['exception']=='none' for x in success),
'expected_singular2':len(failed)==2 and all(x['exception']=='SingularException' and x['status']==1 and x['failed_candidate_discarded'] for x in failed),
'exact_representation_audit':all(x['all_passed'] for x in exact),
'fixed_bounds':all(x['factor_residual']<=x['factor_bound'] and x['forward_residual']<=x['forward_bound'] and x['transpose_residual']<=x['transpose_bound'] for x in success),
'metrics44':len(metrics)==44 and all(all(math.isfinite(v) and v>=0 for v in x.values()) for x in metrics),
'host_absent':not host['active'] and all(v['absent'] for v in host['identities'].values()),
'user_preserved':all(sha(k)==v for k,v in pre['user_hashes'].items()),
'no_production_test_ci_change':not subprocess.check_output(['git','diff','master','--','src','test','.github'],text=True),
'resource_guard':bool(resource) and all(x['available_kib']>=6*1024**2 and x['swap_used_kib']<=1024**2 for x in resource),
}
result={'checks':checks,'all_passed':all(checks.values()),'pins':len(pins['inventory']),'exact':exact,'pairs_equal':{str(x['case']):x['paired_equal'] for x in rows if 'paired_equal' in x},'compile_nonzero_entries':sum(x['compile_seconds']>0 for x in metrics),'resources':{'samples':len(resource),'min_available_kib':min(x['available_kib'] for x in resource),'max_swap_kib':max(x['swap_used_kib'] for x in resource)},'raw_report_sha256':sha(base/'report.toml'),'scope':'new native component only; no HH publication, speedup, native retained bound or historical CI proof'}
with (out/'boundary-1-audit.json').open('x') as f:json.dump(result,f,indent=2)
for name in ['report.toml','run.log','process.json','resources.jsonl']:
 with (out/('boundary-1-'+name)).open('xb') as f:f.write((base/name).read_bytes())
with (out/'boundary-1-pins.json').open('xb') as f:f.write(pinpath.read_bytes())
for src,dst in [(d/'reproduce/hh_symbolic_boundary.jl','driver.jl.txt'),(Path('/tmp/jsimplex-hh-symbolic-attempt.py'),'launcher.py.txt'),(Path('/tmp/s4-f-preflight.py'),'preflight.py.txt')]:
 with (out/dst).open('xb') as f:f.write(src.read_bytes())
print(json.dumps({k:v for k,v in result.items() if k!='exact'},indent=2));raise SystemExit(0 if result['all_passed'] else 1)
