"""New pure preparation and rejection tests; no process launch."""
from control import *
import analysis as a,evidence,copy,tempfile,tomllib
checks={}
def check(n,v):req(v,n);checks[n]=True
def refuses(n,fn):
 try:fn()
 except (ValueError,KeyError,TypeError,IndexError,FileExistsError,tomllib.TOMLDecodeError):checks[n]=True;return
 raise ValueError('Accepted invalid '+n)
def mutate(o,p,v):
 o=copy.deepcopy(o);q=o
 for k in p[:-1]:q=q[k]
 q[p[-1]]=v;return o
for phase in ('cost1','cost2','probe','accuracy2',''):
 refuses('phase_'+phase,lambda phase=phase:expected_config(phase))
check('exact45second_command',phase_config('accuracy')==expected_config('accuracy') and phase_config('accuracy')['seconds']==45)
with tempfile.TemporaryDirectory(prefix='backend-review-test-') as tmp:
 p=Path(tmp)/'pin';p.write_text('test');review=dict(accepted=True,findings=[],pins_sha256=sha(p),sha256={str(p):sha(p)})
 validate_review(review,p,[str(p)]);check('review_exact_accepted',True)
 for name,path,v in [('reject_review',['accepted'],False),('finding',['findings'],['x']),('wrong_pin',['pins_sha256'],'bad'),('missing_binding',['sha256'],{}),('extra_binding',['sha256'],{str(p):sha(p),'extra':'x'})]:
  refuses(name,lambda path=path,v=v:validate_review(mutate(review,path,v),p,[str(p)]))
 refuses('duplicate_required',lambda:validate_review(review,p,[str(p),str(p)]))
cfg=phase_config('accuracy');ident=dict(pid=101,pgid=101,sid=101,start_ticks=100,command='test',boot_id='boot');child=dict(ident,pid=102,pgid=102,sid=102,start_ticks=101)
h=dict(head='head',master='master',boot_id='boot',matches=[],groups=[1,101,102]);s=dict(guard_identity=ident,elapsed_seconds=2,accepted=True,returncode=0)
p=dict(runner=ident,child=child,returncode=0,reason='exit0',pins_unchanged=True,command=cfg['command'],pins_sha256='pin');cur=dict(p)
reservation=dict(one_attempt=True,phase='accuracy',command=cfg['command'],pins_sha256='pin',review_sha256='review',max_seconds=45)
inv=dict(supervisor=s,monotonic_start=100,python=sys.executable,elapsed_seconds=3,command=cfg['command'],guard_command=guard_command(cfg,Q/'accuracy-launch-pins.json',100),pins_sha256='pin',review_sha256='review',reservation_sha256='reservation')
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
