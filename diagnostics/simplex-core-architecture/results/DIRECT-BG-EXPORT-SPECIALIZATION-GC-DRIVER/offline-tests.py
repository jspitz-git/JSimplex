"""Exercise only new pure predicates and read-only admission gates. No launcher."""
from pathlib import Path
import json,copy,tempfile,ast,tomllib
from oracle import test_results,timeout_only,warning_log
import control as c
D=Path(__file__).resolve().parent;checks={}
def check(v,n):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def reject(fn,n):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError,FileNotFoundError):check(True,n)
 else:check(False,n)
expected=c.rd(D/'expected-tests.json');t=tomllib.loads((D/'expected-tests.toml').read_text())
for mode in ['red','green']:
 check(t[mode]['assertions']==expected[mode]['assertions'] and [[z[k] for k in ['name','pass','fail','error','broken']] for z in t[mode]['groups']]==expected[mode]['groups'],'json_toml_'+mode)
 phase=mode+'gc300';cfg=c.config(phase);loaded=c.loaded_for(cfg)
 def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic expected failure']*(f+e),children=[])
 root=node('root');root['children']=[node(*row) for row in expected[mode]['groups']]
 raw=dict(phase=phase,complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=root,preparation_calls=3,preparations_completed=3)
 check(test_results(raw,expected[mode],loaded,phase)['assertions']==expected[mode]['assertions'],'valid_'+mode)
 mutations={
 'missing':lambda x:x.pop('tests'),'extra':lambda x:x.update(extra=True),
 'incomplete':lambda x:x.update(complete=False),'fatal':lambda x:x.update(fatal='error'),
 'phase':lambda x:x.update(phase='wrong'),'threads_bool':lambda x:x.update(threads=True),
 'blas':lambda x:x.update(blas_threads=2),'path':lambda x:x['loaded'].update(JSimplex='/wrong'),
 'count':lambda x:x['tests']['children'][0].update(**{'pass':1}),
 'nested':lambda x:x['tests']['children'][0]['children'].append(node('extra')),
 'name':lambda x:x['tests']['children'][0].update(name='wrong'),
 'broken':lambda x:x['tests']['children'][0].update(broken=1),
 'error':lambda x:x['tests']['children'][0].update(error=1),
 'failstrings':lambda x:x['tests']['children'][0]['failures'].append('extra'),
 'rootpass':lambda x:x['tests'].update(**{'pass':1})}
 for name,mutate in mutations.items():
  x=copy.deepcopy(raw);mutate(x);reject(lambda:test_results(x,expected[mode],loaded,phase),'reject_'+mode+'_'+name)
 p=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False)
 log='BEGIN BG specialization driver '+phase
 check(timeout_only(p,sup,None,log,299.,300,loaded,phase),'pure_missing_raw_'+mode)
 partial=copy.deepcopy(raw);partial.update(complete=False);partial['tests']=node('root')
 check(timeout_only(p,sup,partial,log,299.,300,loaded,phase),'pure_partial_'+mode)
 for name,mutate in mutations.items():
  x=copy.deepcopy(partial)
  if name in ['count','nested','name','broken','error','failstrings']:x['tests']['children']=[node('partial')]
  mutate(x)
  # An incomplete flag is correct on a timeout; a nonzero passing prefix is also legal.
  if name in ['incomplete','count','name','nested']:continue
  check(not timeout_only(p,sup,x,log,299.,300,loaded,phase),'timeout_reject_'+mode+'_'+name)
 for token in ['TEST FAILURE:','BROKEN TEST:','ERROR:','FATAL DRIVER:','LoadError','GROUP/COUNT MISMATCH']:
  check(not timeout_only(p,sup,None,log+'\n'+token,299.,300,loaded,phase),'timeout_log_'+mode+'_'+token)
 for value in [float('nan'),float('inf'),301.,-1.]:check(not timeout_only(p,sup,None,log,value,300,loaded,phase),'timeout_elapsed_'+mode+str(value))
 check(not timeout_only(p,sup,None,'',299.,300,loaded,phase),'timeout_no_checkpoint_'+mode)
 check(not timeout_only(dict(p,reason='memory_guard'),sup,None,log,299.,300,loaded,phase),'timeout_memory_'+mode)
 check(not timeout_only(p,dict(sup,hard_timeout=True),None,log,299.,300,loaded,phase),'timeout_hard_'+mode)
 check(not timeout_only(dict(p,pins_unchanged=False),sup,None,log,299.,300,loaded,phase),'timeout_pins_'+mode)
 check(not timeout_only(p,sup,raw,log,299.,300,loaded,phase),'timeout_complete_'+mode)
for phase in ['redgc300','greengc300']:
 cfg=c.config(phase);check(cfg['seconds']==(300 if phase.endswith('300') else 600),'limit_'+phase)
 cmd=c.guard_command(cfg,D/'dummy-pins.json',123.)
 check(cmd[cmd.index('--seconds')+1]==str(cfg['seconds']-8),'inner_'+phase)
 check(cmd[cmd.index('--expected-exit')+1]==str(cfg['expected_exit']),'exit_'+phase)
reject(lambda:c.config('green'),'invalid_phase')
reject(lambda:c.predecessor('greengc300'),'no_red_result')
reject(lambda:c.config('redgc600'),'no_timeout_result')
with tempfile.TemporaryDirectory(prefix='adapter-offline-') as tmp:
 f=Path(tmp)/'pins';f.write_text('fixed')
 good=dict(accepted=True,findings=[],scope='test',phase='red300',pins_sha256=c.sha(f),sha256={str(f):c.sha(f)})
 c.verify_review(good,f,[str(f)],'test','red300');check(True,'review_positive')
 for name,value in [('accepted',False),('findings',['finding']),('scope','wrong'),('phase','green300'),('pins_sha256','wrong'),('sha256',{})]:
  x=copy.deepcopy(good);x[name]=value;reject(lambda:c.verify_review(x,f,[str(f)],'test','red300'),'review_'+name)
 for path in sorted(D.glob('*.py')):ast.parse(path.read_text(),filename=str(path))
 check(True,'new_python_syntax_only')
for token in ['WARNING: world age','Warning: a warning','world-age','world age']:
 check(warning_log(token),'warning_'+token)
check(not warning_log('normal output'),'ordinary_log')
check(c.host_safe(dict(matches=[],unreadable_identity_pids=[])),'readable_host')
check(not c.host_safe(dict(matches=[{}],unreadable_identity_pids=[])),'process_host_refusal')
check(not c.host_safe(dict(matches=[],unreadable_identity_pids=[1])),'identity_host_refusal')
# An exclusive reservation cannot be reused. Exercise only save on a temporary file.
with tempfile.TemporaryDirectory(prefix='bgx-reservation-') as td:
 p=Path(td)/'reservation.json';c.save(p,dict(one_attempt=True))
 try:c.save(p,dict(one_attempt=True))
 except FileExistsError:check(True,'exclusive_reservation_refuses_reuse')
 else:check(False,'exclusive_reservation_refuses_reuse')
check(not (D/'runs').exists(),'no_seal_reservation_output_or_launch')

from allocation_oracle import allocation_results,partial_windows
import struct
bt=lambda x:struct.pack('>d',float(x)).hex()
fixtures=[];rows={}
for cell,name in enumerate(('sparse32','dense32','sparse96'),1):
 m=dict(n=1,colptr=[1,2],rowval=[1],nzval=[bt(1)])
 f=dict(name=name,n=1,matrices=[copy.deepcopy(m) for _ in range(9)],steps=[dict(j=1,a=[bt(1)],dse=[bt(1)],unit=[bt(1)]) for _ in range(8)])
 fixtures.append(f)
 for pair in range(1,11):
  for order in (1,2):
   side=('reference','candidate')[(order-1) if pair%2 else (2-order)]
   rows[f'window-{cell}-{2*(pair-1)+order}.toml']=dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=100 if side=='reference' else 90,events=10 if side=='reference' else 9,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.1]*6,outputs=[[bt(1)] for _ in range(24)])
check(len(allocation_results(rows,fixtures,'green'))==3,'allocation_green_positive')
redrows=copy.deepcopy(rows)
for r in redrows.values():
 if r['side']=='candidate':r['events']=11
check(len(allocation_results(redrows,fixtures,'red'))==3,'allocation_red_three_failures')
reject(lambda:allocation_results(rows,fixtures,'red'),'red_unexpected_pass')
reject(lambda:allocation_results(redrows,fixtures,'green'),'green_increase')
for name,mut in {
 'missing_window':lambda r:r.pop('window-1-1.toml'),
 'bad_order':lambda r:r['window-1-1.toml'].update(order=2),
 'nan_time':lambda r:r['window-1-1.toml'].update(seconds=float('nan')),
 'compilation':lambda r:r['window-1-7.toml'].update(compile_seconds=.1),
 'bad_residual':lambda r:r['window-1-1.toml']['outputs'][0].__setitem__(0,bt(2)),
 'input_mutated':lambda r:r['window-1-1.toml'].update(inputs_unchanged=False),
 'mode_difference':lambda r:r['window-1-1.toml'].update(modes=['direct']*3),
 'policy':lambda r:r['window-1-1.toml'].update(policy='default'),
 'boolean_count':lambda r:r['window-1-1.toml'].update(events=True),
 'nested_overflow':lambda r:r['window-1-1.toml'].update(nested_seconds=[1.]*6),
 'false_correctness':lambda r:r['window-1-1.toml'].update(correct=False)}.items():
 x=copy.deepcopy(rows);mut(x);reject(lambda:allocation_results(x,fixtures,'green'),'allocation_'+name)
check(partial_windows({},fixtures),'empty_prefix')
check(partial_windows({k:rows[k] for k in ['window-1-1.toml','window-1-2.toml']},fixtures),'valid_prefix')
reject(lambda:partial_windows({'window-1-2.toml':rows['window-1-2.toml']},fixtures),'partial_missing_first')
# Hash and stage refusal uses temporary files only, not seal/launch.
with tempfile.TemporaryDirectory(prefix='bgxs-hash-') as td:
 p=Path(td)/'stage';p.mkdir();f=p/'source';f.write_text('original')
 pins=dict(files=[str(f)],trees=[str(p)],inventory=c.guard.inventory([str(f)],[str(p)]),inputs=[])
 check(c.guard.pins_match(pins),'hash_stage_valid')
 f.write_text('changed');check(not c.guard.pins_match(pins),'hash_refusal');f.write_text('original')
 (p/'extra').write_text('extra');check(not c.guard.pins_match(pins),'stage_membership_refusal')


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
with (D/'offline-tests.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='Synthetic saved-data/control checks only; Julia not executed'),f,indent=2);f.write('\n')
print('New offline predicate tests PASS',len(checks))
