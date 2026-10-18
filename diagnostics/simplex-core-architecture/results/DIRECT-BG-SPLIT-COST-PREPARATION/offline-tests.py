"""New synthetic failures only; no Julia or launch. Executable before controls."""
from pathlib import Path
import json,math,copy,struct,tomllib
from analysis import *
D=Path(__file__).resolve().parent
checks={}
def check(name,v):
 checks[name]=bool(v)
 if not v:raise RuntimeError(name)
def refuses(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,RuntimeError):check(name,True)
 else:check(name,False)
def tok(x):return struct.pack('>d',x).hex()
I=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1.),tok(1.)]);M=matrix(I)
check('exact_identity',residual(M,[tok(1.),tok(2.)],[tok(1.),tok(2.)]))
check('wrong_solution_rejected',not residual(M,[tok(1.),tok(3.)],[tok(1.),tok(2.)]))
refuses('nan_token',lambda:number(tok(float('nan'))));refuses('bad_token',lambda:number('bad'))
check('reversed_order',all(schedule(1,p)==schedule(2,p)[::-1] for p in range(1,11)))
fixtures=json.loads((D/'inputs.json').read_text())
check('toml_json_identical',tomllib.loads((D/'inputs.toml').read_text())==fixtures)
check('four_fixtures',[(f['name'],f['n']) for f in fixtures['fixtures']]==[('sparse32',32),('dense32',32),('sparse96',96),('dense96',96)])
for f in fixtures['fixtures']:
 n=f['n'];dense=[]
 for m in f['matrices']:
  rows,e,_=matrix(m);dense.append([[0.]*n for _ in range(n)])
  for i,row in enumerate(rows):
   for j,v in row:dense[-1][i][j]=float(Q(v,2**e))
 base=dense[0]
 for i in range(n):
  for j in range(n):
   ii=(i+3)%n;jj=n-j-1
   want=4. if ii==jj else ((-1. if (ii+jj)%2 else 1.)/16/n if f['name'].startswith('dense') else (-.5 if ii==jj+1 else .25 if jj==ii+1 else 0.))
   if tok(base[i][j])!=tok(want):raise RuntimeError('base bits')
 for k,s in enumerate(f['steps']):
  j=(7*k)%n;a=[row[j] for row in dense[k]];a[(j+1)%n]+=1/32
  check(f'{f["name"]}_step{k}',s['j']==j+1 and s['a']==list(map(tok,a)) and s['dse']==[tok(i/n) for i in range(1,n+1)] and s['unit']==[tok(float(i==j)) for i in range(n)] and all(dense[k+1][i][c]==(a[i] if c==j else dense[k][i][c]) for i in range(n) for c in range(n)))
 check(f'{f["name"]}_diagonal_margin',all(abs(base[i][n-1-((i+3)%n)])>sum(abs(x) for j,x in enumerate(base[i]) if j!=n-1-((i+3)%n)) for i in range(n)))
# Pure result-gate boundaries; no solver results invented.
a=dict(time_median_gate=True,allocation_gate=True,memory_gate=True,faster_pairs=5)
check('qualification_positive',qualify(a,a))
for field in ('time_median_gate','allocation_gate','memory_gate'):
 b=dict(a);b[field]=False;check('reject_'+field,not qualify(a,b))
b=dict(a,faster_pairs=4);check('reject_nine_faster',not qualify(a,b))

# Additional new matched-policy raw/gate synthetic tests, no solver outputs claimed.
import tempfile
import evidence as evidence, control as control
from unittest.mock import patch
identity=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[tok(1.),tok(1.)])
fixture=dict(name='synthetic',n=2,matrices=[identity]*9,steps=[dict(j=1,a=[tok(1.),tok(2.)],dse=[tok(1.),tok(2.)],unit=[tok(1.),tok(0.)]) for _ in range(8)])
row=dict(pair=4,order=1,side='candidate',measured=True,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=.9,bytes=100,events=3,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.01]*6,outputs=[[tok(1.),tok(2.)] if i%3!=2 else [tok(1.),tok(0.)] for i in range(24)])
matrices=[(matrix(identity),matrix(identity,True))]*9
check('valid_window',window_ok(row,fixture,1,4,1,matrices))
for name,value in [('bytes',True),('seconds',float('nan')),('events',-1),('compile_seconds',.001),('recompile_seconds',.001),('inputs_unchanged',False),('correct',False),('modes',['unknown']*3),('nested_seconds',[1.]*6),('pair',True),('outputs',row['outputs'][:23])]:
 bad=copy.deepcopy(row);bad[name]=value;refuses('window_reject_'+name,lambda:window_ok(bad,fixture,1,4,1,matrices))
bad=copy.deepcopy(row);bad['extra']=1;refuses('window_extra_key',lambda:window_ok(bad,fixture,1,4,1,matrices))
bad=copy.deepcopy(row);bad['outputs'][0]=[tok(99.),tok(2.)];refuses('window_wrong_exact_residual',lambda:window_ok(bad,fixture,1,4,1,matrices))
for mode in ['direct','fallback']:
 rr=copy.deepcopy(row);rr['modes']=[mode]*3;check('observed_mode_'+mode,window_ok(rr,fixture,1,4,1,matrices))
controls=[tok(0.)]*20;controls[3]=tok(1.)
pf=dict(reference=[dict(kind='native',policy='threshold_one',control=controls,expected_control=controls,strategy=tok(1.)) for _ in range(3)],candidate=[dict(kind='native',policy='threshold_one',control=controls,expected_control=controls,strategy=tok(1.)) for _ in range(3)],modes=['normalized']*3,inputs_unchanged=True,constructions=2,refactors=4,explicit_solves=0)
check('preflight_valid',evidence.preflight_ok(pf,'native'))
for key,value in [('policy','default'),('strategy','bad'),('control',[tok(0.)]*20),('expected_control',[tok(0.)]*20)]:
 bad=copy.deepcopy(pf);bad['candidate'][0][key]=value;refuses('preflight_reject_'+key,lambda:evidence.preflight_ok(bad,'native'))
# Zero memory/reference metrics remain defined; no nested zero division.
rows=[]
for pair in range(4,11):
 for order,side in enumerate(schedule(1,pair),1):
  rr=copy.deepcopy(row);rr.update(pair=pair,order=order,side=side,seconds=1. if side=='reference' else .9,nested_seconds=[0.]*6,retained_bytes=0);rows.append(rr)
st=summarize(rows);check('zero_memory_equal',st['memory_gate']);check('zero_nested_safe',len(st['nested_seconds'])==6)
next(r for r in rows if r['side']=='candidate')['retained_bytes']=1;check('positive_from_zero_rejected',not summarize(rows)['memory_gate'])
# Gate review membership, stale manifest and missing acceptance fail closed.
with tempfile.TemporaryDirectory(prefix='adapter-cost-offline-') as tmp:
 t=Path(tmp);pin=t/'pins';pin.write_text('{}');source=t/'source';source.write_text('synthetic');required=[str(pin),str(source)]
 v=dict(accepted=True,findings=[],scope='synthetic',phase='cost1-300',pins_sha256=control.sha(pin),sha256={n:control.sha(n) for n in required})
 control.verify_review(v,pin,required,'synthetic','cost1-300');check('review_positive',True)
 for key,value in [('sha256',{}),('pins_sha256','bad'),('accepted',False),('phase','cost2-300')]:
  bad=copy.deepcopy(v);bad[key]=value
  try:control.verify_review(bad,pin,required,'synthetic','cost1-300')
  except RuntimeError:check('review_reject_'+key,True)
  else:check('review_reject_'+key,False)
check('output_membership199',len(evidence.expected_names())==199)
p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False,child_kill=False,guard_term=False,guard_kill=False)
check('timeout_candidate',evidence.timeout_ok(p,sup,'BEGIN matched policy cost cost1-300',292,300))
for marker in ['FATAL COST:','ERROR:','Traceback','Measured compilation; stop']:
 check('mixed_timeout_'+marker,not evidence.timeout_ok(p,sup,'BEGIN matched policy cost '+marker,292,300))
check('import_timeout_unknown',not evidence.timeout_ok(p,sup,'',292,300));check('late_cleanup_rejected',not evidence.timeout_ok(p,sup,'BEGIN matched policy cost ',301,300))
# Read-only syntax compilation applies ONLY to newly authored Python, never Julia.
for p in D.glob('*.py'):
 compile(p.read_text(),str(p),'exec')
check('new_python_syntax',True)
text=(D/'cost.jl').read_text()
check('matched_factories','J._direct_lu_factor(F,B,backend,policy(backend)' in text and 'J._split_bg_factor(B,backend,policy(backend))' in text)
check('no_accumulating_rows','push!(rows,row)' not in text and 'rows=Dict' not in text)
check('single_window_input_scan',text[text.index('function window'):text.index('# Untimed')].count('unchanged(f,source)')==1)
check('definitions_before_main',text.index('include("probe.jl")')<text.index('function main()') and text.rstrip().endswith('main()'))
check('new_phase_no_runtime',not (D/'runs').exists())
with (D/'offline-tests.json').open('x') as o:json.dump(dict(all_passed=all(checks.values()),checks=checks,scope='Synthetic/pure Python only; no Julia'),o,indent=2);o.write('\n')
print('Offline checks',len(checks),'PASS')
