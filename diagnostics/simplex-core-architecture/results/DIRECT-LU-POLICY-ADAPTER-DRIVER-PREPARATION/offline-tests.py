"""Exercise only new pure predicates and read-only admission gates. No launcher."""
from pathlib import Path
import json,copy,tempfile,ast,tomllib
from oracle import test_results,timeout_only
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
 phase=mode+'300';cfg=c.config(phase);loaded=c.loaded_for(cfg)
 def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic expected failure']*(f+e),children=[])
 root=node('root');root['children']=[node(*row) for row in expected[mode]['groups']]
 raw=dict(phase=phase,complete=True,fatal='',loaded=loaded,threads=1,blas_threads=1,tests=root)
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
 log='BEGIN adapter driver '+phase
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
for phase in ['red300','green300','red600','green600']:
 cfg=c.config(phase);check(cfg['seconds']==(300 if phase.endswith('300') else 600),'limit_'+phase)
 cmd=c.guard_command(cfg,D/'dummy-pins.json',123.)
 check(cmd[cmd.index('--seconds')+1]==str(cfg['seconds']-8),'inner_'+phase)
 check(cmd[cmd.index('--expected-exit')+1]==str(cfg['expected_exit']),'exit_'+phase)
reject(lambda:c.config('green'),'invalid_phase')
reject(lambda:c.predecessor('green300'),'no_red_result')
reject(lambda:c.predecessor('red600'),'no_timeout_result')
with tempfile.TemporaryDirectory(prefix='adapter-offline-') as tmp:
 f=Path(tmp)/'pins';f.write_text('fixed')
 good=dict(accepted=True,findings=[],scope='test',phase='red300',pins_sha256=c.sha(f),sha256={str(f):c.sha(f)})
 c.verify_review(good,f,[str(f)],'test','red300');check(True,'review_positive')
 for name,value in [('accepted',False),('findings',['finding']),('scope','wrong'),('phase','green300'),('pins_sha256','wrong'),('sha256',{})]:
  x=copy.deepcopy(good);x[name]=value;reject(lambda:c.verify_review(x,f,[str(f)],'test','red300'),'review_'+name)
 for path in sorted(D.glob('*.py')):ast.parse(path.read_text(),filename=str(path))
 check(True,'new_python_syntax_only')
check(not (D/'runs').exists(),'no_seal_reservation_output_or_launch')
with (D/'offline-tests.json').open('x') as f:json.dump(dict(all_passed=True,checks=checks,scope='Synthetic saved-data/control checks only; Julia not executed'),f,indent=2);f.write('\n')
print('New offline predicate tests PASS',len(checks))
