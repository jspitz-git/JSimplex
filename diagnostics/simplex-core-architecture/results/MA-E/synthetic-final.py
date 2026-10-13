"""New offline tests only; no guard/launcher invocation or Julia subprocess."""
import sys
sys.dont_write_bytecode=True
import copy,json,math
from pathlib import Path
from auditor import *
from control import remaining,terminal,inventory_ok,seal_ok,STAGES,command,OUT
checks={}
def test(n,f):
 try:checks[n]=bool(f())
 except Exception as e:checks[n]=False;print(n,repr(e))
def rejects(f):
 try:f();return False
 except (ValueError,KeyError,TypeError,ZeroDivisionError):return True

def enc(q,label):
 q=Q(q);return dict(value=str(q),sign=q<0,precision=bits(label) if label.startswith('BigFloat') else 0)
def specimen(stage,side):
 raw=dict(stage=stage,side=side,source=str(D/'overlays'/side/'src/JSimplex.jl'),version='1.13.0',records=[],errors=[],ambient_ok=True,body_seconds=1.)
 if stage in ('red','qualification'):
  children=[]
  for name in (['MA upper dispatch and fallback'] if stage=='red' else COUNTS):
   non=[dict(kind=2,expression=e) for e in ['isdefined(J, :_markowitz_upper_solve!)','isdefined(J, :_markowitz_ma_scratch)']] if stage=='red' else []
   children.append(dict(name=name,counts=[0,2,0,0] if stage=='red' else [COUNTS[name],0,0,0],children=[],nonpasses=non))
  raw['tests']=dict(name='MA-E',counts=[0,0,0,0],children=children,nonpasses=[]);raw['counts']=[0,2,0,0] if stage=='red' else [381,0,0,0]
 metric0=dict(seconds=1.,bytes=10,allocations=2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
 if stage in ('red','qualification'):
  raw['compare_metrics']=[] if stage=='red' else [dict(reference=dict(metric0),candidate=dict(metric0)) for _ in range(77)]
  raw['full_metrics']=[] if stage=='red' else [dict(metric0) for _ in range(30)]
 if stage=='red':return raw
 metric0=dict(seconds=1.,bytes=10,allocations=2,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.)
 for f,l in [(f,l) for f in FIX['fixtures'] for l in FIX['scalar_cases']]:
  n=f['n'];s=n-2 if f['family']=='star' else 0;k=n-1 if s else 0;target=l not in ('Float32','Float64')
  inds=[list(range(2,n+1))]+[[] for _ in range(s-1)] if s else []
  vals=[[enc(Q(f['matrix'][0][j]),l) for j in range(1,n)]]+[[] for _ in range(s-1)] if s else []
  diag=[enc(2,l) for _ in range(s)]
  m=dict(S=s,K=k,E=int(target and s>0),rows=list(range(1,n+1)),columns=list(range(1,n+1)),upper_indices=inds,upper_values=vals,diagonal=diag)
  seed=[Q(f['rhs'][i]) if i<s else Q(1) for i in range(n)];ones=[enc(1,l) for _ in range(n)]
  r=dict(name=f['name'],scalar=l,metadata=m)
  if stage=='qualification':r.update(seed_ok=True,prefix=[enc(x,l) for x in seed],expected=ones,actual=ones,trace=[dict(pivot=p,value=[enc(1,l)]) for p in range(s,0,-1)])
  else:
   r.update(rhs=[enc(x,l) for x in f['rhs']],seed=[enc(x,l) for x in seed],full_first=ones,full_last=ones,upper_first=ones,upper_last=ones,retained_ok=True,rhs_preserved=True,backend_graph_bytes=200,scratch_present=target)
   for key in ('construction','first_full','steady_full','first_upper','steady_upper'):r[key]=dict(metric0)
   if target:r.update(scratch=dict(metric0),scratch_graph_bytes=100)
  raw['records'].append(r)
 return raw
red=specimen('red','reference');qual=specimen('qualification','candidate');ref=specimen('cost','reference');cand=specimen('cost','candidate')
for n,r,s,side in [('red',red,'red','reference'),('qualification',qual,'qualification','candidate'),('reference',ref,'cost','reference'),('candidate',cand,'cost','candidate')]:test(n+'_positive',lambda r=r,s=s,side=side:validate(r,s,side))
test('paired_positive',lambda:paired(ref,cand))
mutations=[('missing_case',lambda r:r['records'].pop()),('wrong_side',lambda r:r.update(side='reference')),('wrong_source',lambda r:r.update(source='/tmp/foreign.jl')),('errors',lambda r:r.update(errors=['err'])),('ambient',lambda r:r.update(ambient_ok=False)),('case_order',lambda r:r['records'].reverse()),('topology',lambda r:r['records'][0]['metadata'].update(K=0)),('compile',lambda r:r['records'][0]['steady_full'].update(compile_seconds=.1)),('recompile',lambda r:r['records'][0]['steady_upper'].update(recompile_seconds=.1)),('negative_bytes',lambda r:r['records'][0]['steady_full'].update(bytes=-1)),('nan_time',lambda r:r['records'][0]['construction'].update(seconds=float('nan'))),('retained',lambda r:r['records'][0].update(retained_ok=False)),('rhs',lambda r:r['records'][0].update(rhs_preserved=False)),('precision',lambda r:r['records'][0]['full_last'][0].update(precision=64)),('bad_value',lambda r:r['records'][0]['full_last'][0].update(value='100')),('wrong_seed',lambda r:r['records'][0]['seed'][0].update(value='1')),('scratch_missing',lambda r:r['records'][0].pop('scratch')),('bad_index',lambda r:r['records'][0]['metadata']['upper_indices'][0].__setitem__(0,100))]
for n,mut in mutations:
 r=copy.deepcopy(cand);mut(r);test('reject_'+n,lambda r=r:rejects(lambda:validate(r,'cost','candidate')))
for n,mut in [('missing_test',lambda r:r['tests']['children'].pop()),('count',lambda r:r['counts'].__setitem__(0,380)),('nonpass',lambda r:r['tests']['children'][0]['nonpasses'].append({})),('trace',lambda r:r['records'][0]['trace'].pop()),('prefix',lambda r:r['records'][0]['prefix'][0].update(value='9'))]:
 r=copy.deepcopy(qual);mut(r);test('reject_qual_'+n,lambda r=r:rejects(lambda:validate(r,'qualification','candidate')))
r=copy.deepcopy(red);r['tests']['children'][0]['nonpasses'][0]['expression']='unrelated';test('reject_unrelated_RED',lambda:rejects(lambda:validate(r,'red','reference')))
test('deadline_remaining',lambda:remaining(100,200,799,STAGES[2])==1)
test('deadline_expired',lambda:rejects(lambda:remaining(0,100,750,STAGES[2])))
test('invalid_clock',lambda:rejects(lambda:remaining(0,None,float('nan'),STAGES[0])))
p=dict(reason='exit0',returncode=0,command=['cmd'],pins_sha256='hash',pins_unchanged=True,elapsed_including_launch=1,terminal_memory=dict(available_kib=7*1024**2,swap_used_kib=0))
test('terminal_positive',lambda:terminal(p,2,['cmd'],'hash'))
for n,k,v in [('late','elapsed_including_launch',3),('pins','pins_unchanged',False),('exit','returncode',1),('reason','reason','wall_time'),('hash','pins_sha256','bad')]:
 x=copy.deepcopy(p);x[k]=v;test('terminal_reject_'+n,lambda x=x:not terminal(x,2,['cmd'],'hash'))
test('missing_manifest',lambda:not inventory_ok({},{}))
test('missing_seal',lambda:not seal_ok({}, {}, 'h'))
test('schedule22',lambda:len(STAGES)==22 and sum(s['stage']=='cost' for s in STAGES)==20)
# Pure syntax compile does not import/run guard/launcher, and never parses Julia.
for name in ('guard.py','launcher.py','seal.py','control.py','auditor.py'):
 test('python_syntax_'+name,lambda name=name:compile((D/name).read_text(),str(D/name),'exec') is not None)
with (D/'synthetic-final.json').open('x') as f:json.dump(dict(all_passed=all(checks.values()),checks=checks,scope='pure Python synthetic and syntax checks, no Julia or launcher'),f,indent=2);f.write('\n')
print(json.dumps(checks,indent=2));print(sum(checks.values()),'/',len(checks))
if not all(checks.values()):raise SystemExit(1)
