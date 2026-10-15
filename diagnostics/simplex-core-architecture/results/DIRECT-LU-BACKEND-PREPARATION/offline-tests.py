"""Synthetic pure-function refusal tests; never starts Julia, seal, guard, or launcher."""
from control import *
import analysis as a,evidence,copy,struct,tempfile
checks={}
def check(name,v):
 req(v,name);checks[name]=True
def refuses(name,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,IndexError):checks[name]=True;return
 raise ValueError('Accepted invalid '+name)
def tok(x):return struct.pack('>d',float(x)).hex()
def vv(xs):return [tok(x) for x in xs]
def mutate(obj,path,value):
 obj=copy.deepcopy(obj);p=obj
 for k in path[:-1]:p=p[k]
 p[path[-1]]=value;return obj
m=dict(n=2,colptr=[1,3,5],rowval=[1,2,1,2],nzval=vv([4,2,2,4]))
c=dict(tokens=vv([0]*20),irstep_index=8,irstep_zero=True)
f=dict(n=2,lnz=3,unz=3,nzd=2,status=0,do_recip=0,
 L=dict(format='csr',ptr=[1,2,4],indices=[1,1,2],values=vv([1,1,1])),
 U=dict(format='csc',ptr=[1,2,4],indices=[1,1,2],values=vv([1,.5,1.5])),
 p=[2,1],q=[2,1],Rs=vv([2,4]),control=c['tokens'],info=vv([0]*90),native_owned=True,native_match=True,native_colptr=[0,2,4],native_rowval=[0,1,0,1],native_nzval=m['nzval'])
x=vv([1,2]);b=vv([8,10]);fixture=dict(matrices=[m]*5,steps=[dict(a=b,dse=b,unit=b,j=1)]*5)
fresh=dict(controls_before=c,controls_after=c,outputs=[x]*3,factor=f)
prefix=dict(controls_before=c,controls_after_refactor=c,controls_after=c,reset={k:True for k in a.RESET},prefix_outputs=[x]*12,tail_outputs=[x]*3,ordinary_before_base=[x]*2,factor=f,fresh_context_retained=True)
raw=dict(completed=True,fatal='',loaded_path='/synthetic/src/JSimplex.jl',counts=dict(factorization=3,ftran=13,btran=5,replace=4,refactor=1,snapshot=2),inputs_unchanged=True)
old=dict(outputs=[x]*24)
def analyze(rr=raw,ff=fresh,pp=prefix):return a.analyze(rr,ff,pp,fixture,old,'/synthetic')
r=analyze();check('all18synthetic_residuals',len(r['residuals'])==18 and not r['failed_residuals'])
check('division_orientation_permutations',r['decomposition']['fresh']['factor_identity_exact'])
g=mutate(f,['do_recip'],1);g['Rs']=vv([.5,.25]);check('multiply_orientation_same_identity',a.decomposition(a.factors(g,m),x,b)['factor_identity_exact'])
g=mutate(f,['U','values'],vv([1,.5,2]));z=a.decomposition(a.factors(g,m),x,b)
check('factor_error_distinct_from_original',not z['factor_identity_exact'] and z['scaled_original']==['0','0'] and z['combined_application']==z['representation_action'])
g=mutate(prefix,['tail_outputs'],[x,vv([1,3]),x]);g['ordinary_before_base']=g['tail_outputs'][:2];r=analyze(pp=g)
check('false_residual_preserved_no_retry',r['failed_residuals']==['tail_dse'] and r['cost_qualified'] is False and not r['comparisons']['ordinary_equals_base'] and not r['comparisons']['prefix_dse_matches_original_failure'])
for name,path,v in [('flag',['do_recip'],2),('zero_scale',['Rs'],vv([0,4])),('nan_scale',['Rs'],['7ff8000000000000',tok(4)]),('duplicate_perm',['p'],[1,1]),('bad_csr',['L','ptr'],[1,4,3]),('duplicate_csr',['L','indices'],[1,1,1]),('wrong_unit_lower',['L','values'],vv([2,1,1])),('singular_upper',['U','values'],vv([1,.5,0])),('native_alias',['native_owned'],False),('native_drift',['native_nzval'],vv([4,2,2,5])),('info_size',['info'],[])]:
 refuses(name,lambda path=path,v=v:a.factors(mutate(f,path,v),m))
for name,path,v in [('count',['counts','ftran'],14),('incomplete',['completed'],False),('input_changed',['inputs_unchanged'],False),('wrong_source',['loaded_path'],'wrong'),('fatal',['fatal'],'failure')]:
 refuses(name,lambda path=path,v=v:analyze(rr=mutate(raw,path,v)))
for name,path,v in [('reset',['reset','empty_history'],False),('retention',['fresh_context_retained'],False),('later_mutation',['ordinary_before_base'],[x,vv([2,2])]),('missing_output',['prefix_outputs'],[x]*11),('control_drift',['controls_after','tokens'],vv([1]+[0]*19)),('refinement',['controls_after','irstep_zero'],False)]:
 refuses(name,lambda path=path,v=v:analyze(pp=mutate(prefix,path,v)))
refuses('malformed_token',lambda:a.q('bad'))
refuses('infinite_solution',lambda:a.residual(a.matrix(m),['7ff0000000000000',tok(1)],b))
for phase in ('cost1','cost2','probe2',''):
 refuses('phase_'+phase,lambda phase=phase:expected_config(phase))
check('exact45second_command',phase_config('probe')==expected_config('probe') and phase_config('probe')['seconds']==45)
with tempfile.TemporaryDirectory(prefix='backend-review-test-') as tmp:
 p=Path(tmp)/'pin';p.write_text('test');review=dict(accepted=True,findings=[],pins_sha256=sha(p),sha256={str(p):sha(p)})
 validate_review(review,p,[str(p)]);check('review_exact_accepted',True)
 for name,path,v in [('reject_review',['accepted'],False),('finding',['findings'],['x']),('wrong_pin',['pins_sha256'],'bad'),('missing_binding',['sha256'],{}),('extra_binding',['sha256'],{str(p):sha(p),'extra':'x'})]:
  refuses(name,lambda path=path,v=v:validate_review(mutate(review,path,v),p,[str(p)]))
 refuses('duplicate_required',lambda:validate_review(review,p,[str(p),str(p)]))
cfg=phase_config('probe');ident=dict(pid=101,pgid=101,sid=101,start_ticks=100,command='test',boot_id='boot');child=dict(ident,pid=102,pgid=102,sid=102,start_ticks=101)
h=dict(head='head',master='master',boot_id='boot',matches=[],groups=[1,101,102]);s=dict(guard_identity=ident,elapsed_seconds=2,accepted=True,returncode=0)
p=dict(runner=ident,child=child,returncode=0,reason='exit0',pins_unchanged=True,command=cfg['command'],pins_sha256='pin');cur=dict(p)
reservation=dict(one_attempt=True,phase='probe',command=cfg['command'],pins_sha256='pin',review_sha256='review',max_seconds=45)
inv=dict(supervisor=s,monotonic_start=100,python=sys.executable,elapsed_seconds=3,command=cfg['command'],guard_command=guard_command(cfg,D/'probe-launch-pins.json',100),pins_sha256='pin',review_sha256='review',reservation_sha256='reservation')
def process(ii=inv,pp=p,hh=h,rr=reservation):return evidence.execution_checks(cfg,ii,hh,pp,cur,h,h,h,{},'pin','review',rr,'reservation')
check('process_valid',all(process().values()))
for name,path,v in [('late',['elapsed_seconds'],46),('bad_guard',['guard_command'],[]),('timeout',['supervisor','accepted'],False),('cleanup',['supervisor','cleanup_error'],'x'),('review_link',['review_sha256'],'wrong')]:
 check(name,not all(process(ii=mutate(inv,path,v)).values()))
check('live_group',not all(process(hh=mutate(h,['matches'],[ident])).values()))
check('session_omission',not all(process(hh=mutate(h,['groups'],[1,101])).values()))
check('nonzero_exit',not all(process(pp=mutate(p,['returncode'],2)).values()))
check('reservation_limit',not all(process(rr=mutate(reservation,['max_seconds'],90)).values()))
# Compile Python text only; no Julia parsing or future launcher invocation.
for path in D.glob('*.py'):compile(path.read_text(),str(path),'exec')
check('python_syntax',True)
save(D/'offline-tests.json',dict(all_passed=all(checks.values()),checks=checks,scope='Pure synthetic Python helpers; no Julia, seal, guard, launcher or original auditor execution',sha256={str(p):sha(p) for p in [Path(__file__),D/'analysis.py',D/'control.py',D/'evidence.py',D/'launch.py',D/'seal.py',D/'audit.py']}))
print(len(checks),'PASS')
