"""Synthetic exact closure/outer/phase controls only; no process entrypoint."""
from pathlib import Path
import sys,copy,json
from unittest.mock import patch
from contextlib import ExitStack
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import control as c,outer
checks={}
def ck(n,v):
 checks[n]=bool(v)
 if not v:raise RuntimeError(n)
def reject(n,fn):
 try:fn()
 except (ValueError,RuntimeError,KeyError,TypeError):ck(n,True)
 else:ck(n,False)
phase='redgc300';cfg=c.config(phase);run=Path(cfg['run']);o=c.outer_dir(phase)
identity=dict(pid=8,pgid=8,sid=8,start_ticks=9,boot_id='b',command=['outer'])
seal=dict(groups=[1],outer_identity=identity,head='h',master=c.MASTER,boot_id='b')
post=dict(groups=[1,2,3],head='h',master=c.MASTER,boot_id='b')
closure=dict(all_passed=True,outer_identity=identity,sha256={str(p):'hash' for p in c.closure_paths(phase)},host=dict(groups=[1,2,3,8],head='h',master=c.MASTER,boot_id='b',matches=[],unreadable_identity_pids=[],remote='h\trefs/heads/codex/simplex-core-architecture\n'+c.MASTER+'\trefs/heads/master'))
docs={str(run/'sealed.json'):seal,str(run/'posthost.json'):post,str(run/'outer-closure.json'):closure,str(run/'audit.json'):dict(all_passed=True,pure_timeout=False,phase=phase),str(o/'outer-outcome.json'):dict(identity=identity,launched=True,returncode=0,error='')}
realrd=c.rd
with ExitStack() as stack:
 stack.enter_context(patch.object(c,'rd',lambda p:docs[str(p)] if str(p) in docs else realrd(p)));stack.enter_context(patch.object(c,'bindings',lambda v:True));stack.enter_context(patch.object(c,'verify_outer_invocation',lambda *x:identity));stack.enter_context(patch.object(c.guard,'pins_match',lambda v:True));stack.enter_context(patch.object(c,'result_review',lambda *x:([str(run/'result-review.json')],[1,2,3])))
 ck('valid_exact_closure',c.validate_result_closure(phase,closure))
 files,groups=c.predecessor('greengc300');ck('all_eight_outer_closure_bindings_in_GREEN',set(closure['sha256'])<=set(files) and set([1,2,3,8])<=set(groups))
 mutations={
 'missing_binding':lambda x:x['sha256'].pop(str(o/'outer-outcome.json')),
 'extra_binding':lambda x:x['sha256'].update(extra='hash'),
 'missing_outer_group':lambda x:x['host'].update(groups=[1,2,3]),
 'missing_prior_group':lambda x:x['host'].update(groups=[2,3,8]),
 'missing_child_group':lambda x:x['host'].update(groups=[1,2,8]),
 'boot':lambda x:x['host'].update(boot_id='wrong'),
 'head':lambda x:x['host'].update(head='wrong'),
 'master':lambda x:x['host'].update(master='wrong'),
 'remote':lambda x:x['host'].update(remote=''),
 'live_group':lambda x:x['host'].update(matches=[{}]),
 'unreadable':lambda x:x['host'].update(unreadable_identity_pids=[1]),
 'identity':lambda x:x['outer_identity'].update(start_ticks=10),
 'all_passed_int':lambda x:x.update(all_passed=1)}
 for n,f in mutations.items():
  x=copy.deepcopy(closure);f(x);reject(n,lambda:c.validate_result_closure(phase,x))
 for key,val in [('all_passed',False),('pure_timeout',True),('phase','red300')]:
  old=docs[str(run/'audit.json')];docs[str(run/'audit.json')]=dict(old,**{key:val});reject('predecessor_'+key,lambda:c.predecessor('greengc300'));docs[str(run/'audit.json')]=old
 for key,val in [('identity',dict(identity,start_ticks=99)),('launched',False),('returncode',2),('error','fatal')]:
  old=docs[str(o/'outer-outcome.json')];docs[str(o/'outer-outcome.json')]=dict(old,**{key:val});reject('outer_outcome_'+key,lambda:c.predecessor('greengc300'));docs[str(o/'outer-outcome.json')]=old
v=dict(phase=phase,sealed_sha256='s',admission_sha256='r',outer_ready_sha256='i',one_attempt=True)
ck('strict_release_true',outer.valid_release(v,'s','r','i',phase))
for val in [1,False,0,'true',None]:ck('strict_release_reject_'+str(val),not outer.valid_release(dict(v,one_attempt=val),'s','r','i',phase))
# Initial hashes map to exact before-review bytes; never silently repin initial evidence.
m=c.rd(P/'preparation-pins.json');mapping=c.rd(P/'review-fix-source.json')['before_mapping']
ck('all_initial_manifest_bindings_preserved',all(c.sha(mapping.get(p,p))==h for p,h in m['sha256'].items()))
ck('original_failure_unchanged',c.rd(P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER')/'runs/red300/audit.json')['all_passed'] is False)
ck('no_run_or_outer',not (P/'runs').exists() and not (P/'outers').exists())
c.save(P/'closure-tests-3.json',dict(all_passed=True,checks=checks,scope=__doc__))
print('Closure/refusal tests PASS',len(checks))
