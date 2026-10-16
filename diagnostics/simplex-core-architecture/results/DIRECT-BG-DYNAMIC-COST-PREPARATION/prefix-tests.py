"""New synthetic output-prefix tests. Tiny identity data, never numerical evidence."""
from pathlib import Path
import tempfile,json,copy,struct
from unittest.mock import patch
import evidence as e
from control import config,loaded_for,save,D
checks={}
def check(n,b):
 checks[n]=bool(b)
 if not b:raise RuntimeError(n)
def refuse(n,fn):
 try:fn()
 except (RuntimeError,ValueError,KeyError,TypeError):check(n,True)
 else:check(n,False)
def token(x):return struct.pack('>d',x).hex()
def toml(d,prefix=''):
 lines=[]
 for k,v in d.items():
  if isinstance(v,dict) or (isinstance(v,list) and v and isinstance(v[0],dict)):continue
  lines.append(k+' = '+json.dumps(v))
 for k,v in d.items():
  key=prefix+k
  if isinstance(v,dict):lines+=['['+key+']',toml(v,key+'.')]
  elif isinstance(v,list) and v and isinstance(v[0],dict):
   for item in v:lines+=['[['+key+']]',toml(item,key+'.')]
 return '\n'.join(lines)+'\n'
I=dict(n=2,colptr=[1,2,3],rowval=[1,2],nzval=[token(1.)]*2)
f=dict(name='synthetic',n=2,matrices=[I]*9,steps=[dict(j=1,a=[token(1.),token(2.)],dse=[token(1.),token(2.)],unit=[token(1.),token(0.)]) for _ in range(8)])
fixtures=[dict(f,name='synthetic'+str(i)) for i in range(4)];cfg=config('cost1-300');real_rd=e.rd
with tempfile.TemporaryDirectory(prefix='cost-prefix-') as td,patch.object(e,'rd',lambda p:dict(fixtures=fixtures) if Path(p)==D/'inputs.json' else real_rd(p)):
 out=Path(td)
 for n in e.BASE:(out/n).write_text('synthetic')
 cell=0
 for fixture in fixtures:
  for manager in ['BG']:
   for backend in ['native','markowitz']:
    cell+=1;policy='threshold_one' if backend=='native' else 'default';ident=dict(fixture=fixture['name'],manager=manager,backend=backend,policy=policy)
    (out/f'started-{cell}.toml').write_text(toml(ident))
    controls=[token(0.)]*20;controls[3]=token(1.)
    observation=dict(kind=backend,policy=policy,control=controls if backend=='native' else [],expected_control=controls if backend=='native' else [],strategy=token(1.) if backend=='native' else '')
    pf=dict(reference=[observation]*3,candidate=[observation]*3,modes=['normalized']*3,inputs_unchanged=True,constructions=2,refactors=4,explicit_solves=0)
    (out/f'preflight-{cell}.toml').write_text(toml(pf))
    states=[]
    for k,r in [(0,False)]+[(k,r) for k in range(1,9) for r in ([False,True] if k in (4,8) else [False])]:
     states.append(dict(step=k,refactored=r,equal=True,graphs=[100,100,100],capacity=16,live=2,arena_graph_bytes=1024,array_graph_bytes=[8]*15,requested_payload_bytes=1024,copy_arena_payload_bound=2048,history_length=0 if r or k==0 else (k-1)%4+1,counts=[2,0,0,0,2,0]))
    output=[[token(1.),token(2.)] if i%3!=2 else [token(1.),token(0.)] for i in range(24)]
    probe=dict(states=states,outputs=[output]*3,inputs_unchanged=True,constructions=3,refactors=6,updates=24,ftran=48,btran=24,copies=0,counts=[2,0,0,0,2,0])
    (out/f'probe-{cell}.toml').write_text(toml(probe))
    for w in range(1,21):
     pair=(w+1)//2;order=1+(w-1)%2;side=e.window_ok.__globals__['schedule'](1,pair)[order-1]
     row=dict(pair=pair,order=order,side=side,policy=policy,measured=pair>3,correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=.9 if side=='candidate' else 1.,bytes=100,events=2,retained_bytes=0,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,nested_seconds=[0.]*6,outputs=[[token(1.),token(2.)] if i%3!=2 else [token(1.),token(0.)] for i in range(24)])
     (out/f'window-{cell}-{w}.toml').write_text(toml(row))
    (out/f'cell-{cell}.toml').write_text(toml(dict(ident,windows=20)))
 raw=dict(phase=cfg['phase'],loaded=loaded_for(cfg),completed=True,fatal='',cells=8,windows=160,threads=1,blas_threads=1);rawpath=out/'raw.toml';rawpath.write_text(toml(raw))
 result,counts=e.output_checks(out,cfg);check('complete198files160windows',counts==dict(cells=8,windows=160,exact_residuals=3840) and len(result)==8)
 def mutate(n,fn,label):
  p=out/n;before=p.read_text();d=e.tomllib.loads(before);fn(d);p.write_text(toml(d));refuse(label,lambda:e.output_checks(out,cfg));p.write_text(before)
 mutate('raw.toml',lambda d:d.update(completed=1),'raw_nonboolean_complete')
 mutate('raw.toml',lambda d:d.update(windows=159),'raw_wrong_count')
 mutate('preflight-1.toml',lambda d:d.update(inputs_unchanged=False),'preflight_false')
 mutate('window-1-7.toml',lambda d:d.update(compile_seconds=.01),'measured_compile_rejected')
 mutate('window-1-1.toml',lambda d:d.update(policy='default'),'wrong_policy')
 mutate('window-1-1.toml',lambda d:d.update(outputs=[[token(99.),token(2.)]]*24),'exact_residual_rejected')
 mutate('window-1-2.toml',lambda d:d.update(order=1),'order_rejected')
 mutate('probe-1.toml',lambda d:d['states'][0].update(equal=False),'probe_false_state')
 mutate('probe-1.toml',lambda d:d['states'][0].update(capacity=-1),'probe_bad_capacity')
 mutate('probe-1.toml',lambda d:d.update(ftran=49),'probe_wrong_budget')
 mutate('probe-1.toml',lambda d:d.update(counts=[3,0,0,0,2,0]),'probe_wrong_counter')
 mutate('probe-1.toml',lambda d:d['outputs'][1][0].__setitem__(0,token(99.)),'probe_output_drift')
 # Signed zero is within residual tolerance but must fail the DIRECT bitwise oracle.
 mutate('window-1-2.toml',lambda d:d['outputs'][2].__setitem__(1,token(-0.)),'paired_signed_zero_mismatch')
 (out/'unknown').write_text('x');refuse('extra_output',lambda:e.output_checks(out,cfg));(out/'unknown').unlink()
 rawpath.unlink();refuse('completed_windows_no_raw_not_timeout',lambda:e.output_checks(out,cfg,partial=True))
 # Retain a valid first-cell three-window prefix only.
 for p in list(out.iterdir()):
  if p.name not in e.BASE|{'started-1.toml','preflight-1.toml','probe-1.toml','window-1-1.toml','window-1-2.toml','window-1-3.toml'}:p.unlink()
 _,prefix=e.output_checks(out,cfg,partial=True);check('valid_partial_prefix',prefix==dict(cells=0,windows=3,exact_residuals=72))
 p=out/'window-1-2.toml';old=p.read_text();p.unlink();refuse('prefix_hole',lambda:e.output_checks(out,cfg,partial=True));p.write_text(old)
 (out/'raw.toml').write_text('partial =');refuse('partial_raw_rejected',lambda:e.output_checks(out,cfg,partial=True));(out/'raw.toml').unlink()
 (out/'preflight-1.toml').unlink();refuse('window_without_preflight',lambda:e.output_checks(out,cfg,partial=True))
 for p in list(out.glob('window-*')):p.unlink()
 (out/'probe-1.toml').unlink()
 _,prefix=e.output_checks(out,cfg,partial=True);check('started_before_preflight_valid_prefix',prefix['windows']==0)
 p=out/'started-2.toml';p.write_text((out/'started-1.toml').read_text());refuse('nonsequential_cell',lambda:e.output_checks(out,cfg,partial=True))
check('no_phase_runs',not (D/'runs').exists())
save(D/'prefix-tests.json',dict(all_passed=True,checks=checks,scope='Synthetic tiny identity outputs only; not Julia evidence'))
print('New prefix tests',len(checks),'PASS')
