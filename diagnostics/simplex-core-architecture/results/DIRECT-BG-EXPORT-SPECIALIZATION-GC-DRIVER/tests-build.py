from pathlib import Path
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';P=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-DRIVER')
s=(D/'offline-tests.py').read_text();s=s.replace("phase=mode+'300'","phase=mode+'gc300'").replace('tests=root)','tests=root,preparation_calls=3,preparations_completed=3)')
s=s.replace("['red300','green300','red600','green600']","['redgc300','greengc300']").replace("c.predecessor('green300')","c.predecessor('greengc300')").replace("c.predecessor('red600')","c.config('redgc600')")
s=s.replace("with (D/'offline-tests.json').open('x')", "with (D/'offline-tests.json').open('x')")
pos=s.index("with (D/'offline-tests.json').open('x')");s=s[:pos]+'''
from preparation_oracle import preparation_results
from preparation_schema import validate_record

def prep_record(cell,phase='redgc300'):
 return dict(phase=phase,fixture=('sparse32','dense32','sparse96')[cell-1],cell=cell,after_pair=3,before_pair=4,requested_full_gc=True,calls=1,cumulative_calls=cell,returned=True,seconds=.1,bytes=128,events=2,gc_seconds=.15,compile_seconds=.02,recompile_seconds=.01,gc_pauses=2,full_collections=2)
def fake_raw(calls,done,complete=False):
 return dict(phase='redgc300',complete=complete,fatal='',loaded={},threads=1,blas_threads=1,tests=node('root'),preparation_calls=calls,preparations_completed=done)
prep={f'preparation-{i}.toml':prep_record(i) for i in range(1,4)}
schedule=list(rows)
for n in range(61):
 required=sum(n>b for b in [6,26,46]);reached=sum(n>=b for b in [6,26,46])
 for saved in range(required,reached+1):
  subset={k:prep[k] for k in list(prep)[:saved]};wins={k:rows[k] for k in schedule[:n]}
  check(preparation_results(subset,wins,None,'redgc300',False)['saved_preparations']==saved,f'prefix_{n}_{saved}')
  for calls in [saved,saved+1]:
   fn=lambda:preparation_results(subset,wins,fake_raw(calls,saved),'redgc300',False)
   if calls==saved or (calls<=3 and n==saved*20+6):check(fn()['saved_windows']==n,f'counter_prefix_{n}_{saved}_{calls}')
   else:reject(fn,f'counter_reject_{n}_{saved}_{calls}')
check(preparation_results(prep,rows,fake_raw(3,3,True),'redgc300',True)['saved_windows']==60,'full_preparation_positive')
for key in prep_record(1):
 x=prep_record(1);x.pop(key);reject(lambda:validate_record(x,1,'redgc300'),'prep_missing_'+key)
for key in ['bytes','events','gc_pauses','full_collections','cell','after_pair','before_pair','calls','cumulative_calls']:
 for value in [True,-1,1.5]:
  x=prep_record(1);x[key]=value;reject(lambda:validate_record(x,1,'redgc300'),'prep_bad_'+key+'_'+str(value))
for key in ['seconds','gc_seconds','compile_seconds','recompile_seconds']:
 for value in [-1.,float('nan'),float('inf'),True,1]:
  x=prep_record(1);x[key]=value;reject(lambda:validate_record(x,1,'redgc300'),'prep_bad_'+key+'_'+str(value))
for key,value in [('phase','red300'),('fixture','dense32'),('requested_full_gc',False),('returned',False),('extra',1)]:
 x=prep_record(1);x[key]=value;reject(lambda:validate_record(x,1,'redgc300'),'prep_bad_'+key)
for name,p,w,raw,complete in [
 ('missing',{},rows,None,False),('early',prep,{},None,False),
 ('gap',{'preparation-2.toml':prep['preparation-2.toml']},rows,None,False),
 ('raw_count',prep,rows,fake_raw(2,2),False),('complete_raw_missing',prep,rows,None,True),
 ('short_complete',prep,dict(list(rows.items())[:46]),fake_raw(3,3,True),True),
 ('boolcounter',{}, {},fake_raw(True,0),False),('unfinishedwrong',{}, {},fake_raw(1,0),False)]:
 reject(lambda:preparation_results(p,w,raw,'redgc300',complete),'reconcile_'+name)
# Missing counters must never be erased silently by the compatibility wrapper.
for key in ['preparation_calls','preparations_completed']:
 x=fake_raw(0,0);x.pop(key)
 check(not timeout_only(dict(reason='wall_time',returncode=-15,pins_unchanged=True),dict(returncode=1,hard_timeout=False),x,'BEGIN BG specialization driver redgc300',299.,300,{},'redgc300'),'timeout_missing_'+key)
# Safe definitions-only imports and source checks; no entrypoints executed.
import audit,seal,launch,outer
check(not (D/'outers').exists() and not (D/'runs').exists(),'no_run_or_waiting_outer')
for name,item in c.rd(D/'copied-files.json').items():check(c.sha(D/name)==c.sha(item['source'])==item['sha256'],'exact_copy_'+name)
for phase in ['red300','green300','redgc600','greengc600','red600','green600']:reject(lambda:c.config(phase),'old_or_unprepared_phase_'+phase)
check(outer.valid_release(dict(phase='redgc300',sealed_sha256='s',admission_sha256='r',outer_ready_sha256='i',one_attempt=True),'s','r','i','redgc300'),'release_positive')
check(not outer.valid_release(dict(phase='red300',sealed_sha256='s',admission_sha256='r',outer_ready_sha256='i',one_attempt=True),'s','r','i','redgc300'),'release_wrong_phase')
''' +s[pos:]
(P/'offline-tests.py').write_text(s)
(P/'tests-build.py').write_text(Path(__file__).read_text())
