"""Independent OFFLINE review. Definitions/pure helpers and synthetic control only.
No existing checker script, operational main(), Julia, subprocess launch or audit()
is executed. git read-only and /proc snapshots are the only real process work.
"""
from pathlib import Path
import ast,copy,hashlib,json,os,struct,subprocess,sys,tempfile,time
from unittest.mock import patch
from contextlib import ExitStack
P=Path(__file__).resolve().parent; R=P.parents[3]; sys.path.insert(0,str(P))
import control as c, outer, oracle, preparation_schema as ps, preparation_oracle as po
import allocation_oracle as ao, analysis as an
checks={}; findings=[]
def ck(name,v):
    checks[name]=bool(v)
    if not v: raise AssertionError(name)
def rejects(name,fn):
    try: fn()
    except (ValueError,RuntimeError,KeyError,TypeError,FileNotFoundError,FileExistsError):ck(name,True)
    else:ck(name,False)
def digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
manifest=read(P/'preparation-pins-final.json'); hashes={}; size=0; start=time.monotonic()
for n,h in manifest['sha256'].items():
    hashes[n]=digest(n);size+=Path(n).stat().st_size
    ck('hash:'+n,hashes[n]==h)
ck('reviewed_manifest_count',len(hashes)==2325)
ck('required_exact',set(hashes)==set(read(P/'required-paths-final.json')['paths']))
fullhash=dict(paths=len(hashes),bytes=size,elapsed_seconds=time.monotonic()-start,sha256=hashes)
for name,v in read(P/'copied-files.json').items():ck('copy:'+name,digest(P/name)==digest(v['source'])==v['sha256'])
for name in ('runs','outers'):ck('absent:'+name,not (P/name).exists())
for p in P.glob('*.py'):
    if p.name!='closure.py':ast.parse(p.read_text(),filename=str(p))
ck('preserved_unexecuted_draft',read(P/'closure-draft-diagnostic.json')['executed'] is False and digest(P/'closure.py')==read(P/'closure-draft-diagnostic.json')['source_sha256'])
ck('python_ast_only',True)
N=P.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-GC-PREPARATION')
old=read(N/'preparation-pins.json'); canonical=read(N/'preparation-pins-reviewed.json'); rev=read(N/'review.json')
for n,h in old['sha256'].items():
    mapped=Path(n+'.before-count-fix') if n==str(N/'PREPARATION.md') else Path(n)
    ck('initial_amendment:'+n,digest(mapped)==h)
ck('canonical_review_acceptance',rev['accepted'] is True and rev['findings']==[] and rev['scope']=='BG specialization fixed GC preparation' and rev['launch_admitted'] is False)
ck('canonical_review_exact',set(rev['sha256'])==set(canonical['sha256'])|{str(N/'preparation-pins-reviewed.json')})
ck('canonical_review_manifest',rev['pins_sha256']==digest(N/'preparation-pins-reviewed.json'))
for n,h in rev['sha256'].items():ck('amendment_review:'+n,digest(n)==h)
for n,h in rev['evidence_sha256'].items():ck('amendment_evidence:'+n,digest(n)==h)
# Independent read-only git and proc snapshot, never author host/check entrypoints.
def git(*a):return subprocess.check_output(['git',*a],cwd=R,text=True).strip()
refs=dict(head=git('rev-parse','HEAD'),master=git('rev-parse','master'),remote=git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'),tracked=git('diff','--name-only'),cached=git('diff','--cached','--name-only'))
ck('refs',refs['head']=='ff248544e8f89cc05aecff64806bf60d8b2bd9cf' and refs['master']=='26e2291745999f485a74f643298ca997d65c7205' and refs['head']+'\trefs/heads/codex/simplex-core-architecture' in refs['remote'] and refs['master']+'\trefs/heads/master' in refs['remote'] and not refs['tracked'] and not refs['cached'])
groups=set(read(P/'host-entry.json')['groups']);matches=[];unreadable=[];unreadable_exe=[]
ck('259_prior_groups',len(groups)==259)
for p in Path('/proc').glob('[0-9]*'):
    try:
        st=(p/'stat').read_text().rsplit(')',1)[1].split();comm=(p/'comm').read_text().strip();argv=(p/'cmdline').read_bytes().split(b'\0')[0].decode(errors='replace');exe=''
        try:exe=str((p/'exe').resolve(strict=True))
        except PermissionError:unreadable_exe.append(int(p.name))
        except FileNotFoundError:pass
        if int(st[2]) in groups or int(st[3]) in groups or any(Path(x).name.lower().startswith('julia') for x in [comm,argv,exe]):matches.append(dict(pid=int(p.name),pgid=int(st[2]),sid=int(st[3]),comm=comm,argv0=argv,exe=exe))
    except (ProcessLookupError,FileNotFoundError):pass
    except PermissionError:unreadable.append(int(p.name))
ck('fresh_processes',not matches and not unreadable)
host=dict(groups=sorted(groups),matches=matches,unreadable_identity_pids=unreadable,unreadable_exe_pids=unreadable_exe,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip())
# Exhaustive boundary reconciliation using minimal synthetic rows.
def node(name,p=0,f=0,e=0,b=0):return dict(name=name,**{'pass':p,'fail':f,'error':e,'broken':b},failures=['synthetic expected allocation failure']*(f+e),children=[])
def raw(phase='redgc300',calls=3,done=3,complete=True):return dict(phase=phase,complete=complete,fatal='',loaded={},threads=1,blas_threads=1,tests=node('root'),preparation_calls=calls,preparations_completed=done)
def record(i,phase='redgc300'):return dict(phase=phase,fixture=ps.CELLS[i-1],cell=i,after_pair=3,before_pair=4,requested_full_gc=True,calls=1,cumulative_calls=i,returned=True,seconds=.125,bytes=128,events=3,gc_seconds=.25,compile_seconds=.5,recompile_seconds=.2,gc_pauses=3,full_collections=2)
ck('17_fields',len(record(1))==17)
schedule=[f'window-{i}-{j}.toml' for i in range(1,4) for j in range(1,21)]
for n in range(61):
    wins=dict.fromkeys(schedule[:n],{})
    for done in range(4):
        rows={f'preparation-{i}.toml':record(i) for i in range(1,done+1)}
        legal=sum(n>b for b in (6,26,46))<=done<=sum(n>=b for b in (6,26,46))
        call=lambda:po.preparation_results(rows,wins,None,'redgc300',False)
        if legal:ck(f'prefix:{n}:{done}',call()['saved_windows']==n)
        else:rejects(f'prefix_reject:{n}:{done}',call)
        if legal:
            for count in range(4):
                good=count==done or (count==done+1 and n==20*done+6)
                call=lambda:po.preparation_results(rows,wins,raw(calls=count,done=done,complete=False),'redgc300',False)
                if good:ck(f'counter:{n}:{done}:{count}',call()['saved_preparations']==done)
                else:rejects(f'counter_reject:{n}:{done}:{count}',call)
for key in record(1):
    r=record(1);r.pop(key);rejects('missing:'+key,lambda:ps.validate_record(r,1,'redgc300'))
for key in ('seconds','gc_seconds','compile_seconds','recompile_seconds'):
    for val in (True,0,-1.,float('inf'),float('nan')):
        r=record(1);r[key]=val;rejects('metric:'+key+':'+repr(val),lambda:ps.validate_record(r,1,'redgc300'))
for key in ('bytes','events','gc_pauses','full_collections','cell','after_pair','before_pair','calls','cumulative_calls'):
    for val in (True,-1,1.5):
        r=record(1);r[key]=val;rejects('integer:'+key+':'+repr(val),lambda:ps.validate_record(r,1,'redgc300'))
ck('overlap_compile_multicollection_allowed',ps.validate_record(record(1),1,'redgc300'))
# Independent dense 2x2 exact solution; no linear algebra package or runtime.
bits=lambda x:struct.pack('>d',float(x)).hex()
M=dict(n=2,colptr=[1,3,5],rowval=[1,2,1,2],nzval=[bits(2),bits(1),bits(1),bits(2)])
fixtures=[dict(name=name,n=2,matrices=[copy.deepcopy(M) for _ in range(9)],steps=[dict(j=1,a=[bits(3)]*2,dse=[bits(3)]*2,unit=[bits(3)]*2) for _ in range(8)]) for name in ps.CELLS]
windows={}
for i in range(1,4):
    for j in range(1,21):
        pair=(j+1)//2;order=(j-1)%2+1;side=an.schedule(1,pair)[order-1]
        windows[f'window-{i}-{j}.toml']=dict(pair=pair,order=order,side=side,measured=pair>3,policy='threshold_one',correct=True,inputs_unchanged=True,modes=['normalized']*3,seconds=1.,bytes=120 if side=='candidate' else 100,events=12 if side=='candidate' else 10,gc_seconds=0.,compile_seconds=0.,recompile_seconds=0.,retained_bytes=100,nested_seconds=[.05]*6,outputs=[[bits(1)]*2 for _ in range(24)])
ck('complete_red_three_predicates',all(not r['statistics']['allocation_gate'] for r in ao.allocation_results(windows,fixtures,'red')))
green=copy.deepcopy(windows)
for r in green.values():
    if r['side']=='candidate':r.update(bytes=90,events=9)
ck('complete_green_three_predicates',all(r['statistics']['allocation_gate'] for r in ao.allocation_results(green,fixtures,'green')))
for name,mut in {
'residual':lambda r:r['outputs'][0].__setitem__(0,bits(2)), 'compile':lambda r:r.update(compile_seconds=.1),
'recompile':lambda r:r.update(recompile_seconds=.1), 'inputs':lambda r:r.update(inputs_unchanged=False),
'modes':lambda r:r.update(modes=['direct']*3),'policy':lambda r:r.update(policy='default'),
'badtoken':lambda r:r['outputs'][0].__setitem__(0,'invalid'), 'nan':lambda r:r.update(seconds=float('nan')),
'boolbytes':lambda r:r.update(bytes=True),'unknown':lambda r:r.update(extra=0)}.items():
    w=copy.deepcopy(green);mut(w['window-1-7.toml']);rejects('numerical:'+name,lambda:ao.allocation_results(w,fixtures,'green'))
exp=read(P/'expected-tests.json')
for mode,total in [('red',3),('green',8640)]:
    phase=mode+'gc300';r=raw(phase);r['tests']['children']=[node(*x) for x in exp[mode]['groups']]
    ck('exact_tree:'+mode,oracle.test_results(r,exp[mode],{},phase)['assertions']==total)
    for key,value in [('phase','red300'),('preparation_calls',2),('preparations_completed',2),('threads',True),('complete',False),('fatal','failure')]:
        q=copy.deepcopy(r);q[key]=value;rejects('raw:'+mode+':'+key,lambda:oracle.test_results(q,exp[mode],{},phase))
    proc=dict(reason='wall_time',returncode=-15,pins_unchanged=True);sup=dict(returncode=1,hard_timeout=False);log='BEGIN BG specialization driver '+phase
    ck('timeout_without_raw:'+mode,oracle.timeout_only(proc,sup,None,log,299.,300,{},phase))
    for text in ('TEST FAILURE:','Warning:','world-age','FATAL DRIVER:','ERROR:','BROKEN TEST:'):
        ck('timeout_reject:'+mode+':'+text,not oracle.timeout_only(proc,sup,None,log+'\n'+text,299.,300,{},phase))
    for elapsed in (-1,301,float('inf'),float('nan')):ck('timeout_elapsed:'+mode+':'+repr(elapsed),not oracle.timeout_only(proc,sup,None,log,elapsed,300,{},phase))
    ck('timeout_failure_never_complete:'+mode,not oracle.timeout_only(proc,sup,r,log,299.,300,{},phase))
# Review/identity/release/seal membership boundaries. All synthetic temporary files.
with tempfile.TemporaryDirectory(prefix='independent-bg-gc-') as temp:
    t=Path(temp);f=t/'pins';f.write_text('immutable')
    v=dict(accepted=True,findings=[],scope='synthetic',phase='redgc300',pins_sha256=digest(f),sha256={str(f):digest(f)})
    c.verify_review(v,f,[str(f)],'synthetic','redgc300');ck('review_exact',True)
    for key,value in [('accepted',1),('findings',['unresolved']),('scope','wrong'),('phase','red300'),('pins_sha256','wrong'),('sha256',{})]:
        q=copy.deepcopy(v);q[key]=value;rejects('review_reject:'+key,lambda:c.verify_review(q,f,[str(f)],'synthetic','redgc300'))
    c.save(t/'reservation.json',dict(one_attempt=True));rejects('exclusive_reservation',lambda:c.save(t/'reservation.json',dict(one_attempt=True)))
    valid=dict(phase='redgc300',sealed_sha256='seal',admission_sha256='review',outer_ready_sha256='ready',one_attempt=True)
    ck('release_exact',outer.valid_release(valid,'seal','review','ready','redgc300'))
    for key in valid:
        q=copy.deepcopy(valid);q.pop(key);ck('release_missing:'+key,not outer.valid_release(q,'seal','review','ready','redgc300'))
    q=dict(valid,one_attempt=1)
    numeric_release=outer.valid_release(q,'seal','review','ready','redgc300')
    ck('strict_numeric_release_rejected',not numeric_release)
    # resolved finding: findings.append(dict(id='F3',priority='P2',file=str(P/'outer.py'),line=9,title='Enforce Boolean one_attempt in exact release/reservation schemas',evidence='valid_release accepts integer 1 because dict equality equates 1 and True; exact invocation/reservation equality has the same issue. Exclusive create still prevents a second attempt.'))
    cfg=c.config('redgc300')
    with patch.object(c,'preparation',lambda:['prepared']),patch.object(c,'predecessor',lambda phase:([],[])),patch.object(c,'seal_files',lambda *args:['prepared','host','config','ready']),patch.object(c.guard,'inventory',lambda f,t:{'inventory':'exact'}):
        seal=dict(files=['prepared','host','config','ready'],trees=[cfg['stage'],str(c.C)],inputs=[],inventory={'inventory':'exact'})
        c.verify_seal(cfg,seal);ck('seal_exact',True)
        for key,value in [('files',['prepared','host','config']),('trees',[]),('inputs',['unreviewed']),('inventory',{})]:
            q=copy.deepcopy(seal);q[key]=value;rejects('seal_reject:'+key,lambda:c.verify_seal(cfg,q))
    identity=dict(pid=700001,pgid=700001,sid=700001,start_ticks=1,boot_id='boot',command='synthetic outer')
    ready=dict(identity=identity,phase='redgc300',waiting_only=True,script_sha256='hash',expected_launcher=str(P/'launch.py'))
    with patch.object(c,'rd',lambda p:ready if Path(p).name=='outer-ready.json' else read(p)),patch.object(c,'sha',lambda p:'hash'),patch.object(c.guard,'process_identity',lambda pid:identity):
        ck('outer_live_exact',c.verify_outer('redgc300',dict(outer_identity=identity),True)==identity)
        with patch.object(c.guard,'process_identity',lambda pid:dict(identity,start_ticks=2)):rejects('outer_reused_pid',lambda:c.verify_outer('redgc300',dict(outer_identity=identity),True))
    # Exact closure and predecessor, with current review/hash boundaries mocked only here.
    redrun=P/'runs/redgc300'; outerdir=P/'outers/redgc300'
    seal=dict(outer_identity=identity,groups=[10],head='head',master=c.MASTER,boot_id='boot')
    post=dict(groups=[10,111,222],head='head',master=c.MASTER,boot_id='boot')
    closure=dict(all_passed=True,outer_identity=identity,host=dict(matches=[],unreadable_identity_pids=[],groups=[10,111,222,700001],head='head',master=c.MASTER,boot_id='boot',remote='head\trefs/heads/codex/simplex-core-architecture\n'+c.MASTER+'\trefs/heads/master'),sha256={str(x):'hash' for x in c.closure_paths('redgc300')})
    outcome=dict(identity=identity,launched=True,returncode=0,error='')
    docs={str(redrun/'audit.json'):dict(all_passed=True,pure_timeout=False,phase='redgc300'),str(redrun/'outer-closure.json'):closure,str(redrun/'sealed.json'):seal,str(redrun/'posthost.json'):post,str(outerdir/'outer-outcome.json'):outcome}
    with patch.object(c,'result_review',lambda *a:([str(redrun/'result-review.json')],[10,111,222])),patch.object(c,'rd',lambda p:docs[str(p)] if str(p) in docs else read(p)),patch.object(c.guard,'pins_match',lambda s:True),patch.object(c,'sha',lambda p:'hash'),patch.object(c,'verify_outer_invocation',lambda *args:identity):
        files,gs=c.predecessor('greengc300')
        ck('successful_red_all_outer_bindings',set(closure['sha256'])<=set(files) and set([10,111,222,700001])<=set(gs))
        for name in list(closure['sha256']):
            h=closure['sha256'].pop(name);rejects('closure_missing:'+Path(name).name,lambda:c.predecessor('greengc300'));closure['sha256'][name]=h
        closure['sha256']['unexpected']='hash';rejects('closure_extra',lambda:c.predecessor('greengc300'));closure['sha256'].pop('unexpected')
        for group in list(closure['host']['groups']):
            closure['host']['groups'].remove(group);rejects('closure_group:'+str(group),lambda:c.predecessor('greengc300'));closure['host']['groups'].append(group)
        for key in ('head','master','boot_id','remote'):
            before=closure['host'][key];closure['host'][key]='wrong';rejects('closure_host:'+key,lambda:c.predecessor('greengc300'));closure['host'][key]=before
        for key,val in [('all_passed',False),('pure_timeout',True),('phase','red300')]:
            d=docs[str(redrun/'audit.json')];before=copy.deepcopy(d);d[key]=val
            rejects('red_predecessor:'+key,lambda:c.predecessor('greengc300'));d.clear();d.update(before)
        for key,value in [('returncode',2),('error','failed'),('launched',False),('identity',dict(identity,start_ticks=2))]:
            before=outcome[key];outcome[key]=value;rejects('red_outer_outcome:'+key,lambda:c.predecessor('greengc300'));outcome[key]=before
    # Actual invocation helper, separate from predecessor mocks.
    release=dict(phase='redgc300',sealed_sha256='hash',admission_sha256='hash',outer_ready_sha256='hash',one_attempt=True)
    invocation=dict(identity=identity,phase='redgc300',seal_sha256='hash',review_sha256='hash',release_sha256='hash',launcher_sha256='hash',method='runpy.run_path launch.py as __main__ in this outer process')
    docs2={'outer-ready.json':ready,'release.json':release,'outer-invocation.json':invocation}
    with patch.object(c,'rd',lambda p:docs2[Path(p).name] if Path(p).name in docs2 else read(p)),patch.object(c,'sha',lambda p:'hash'):
        ck('outer_invocation_exact',c.verify_outer_invocation('redgc300',seal)==identity)
        for value in (1,False,'true'):
            release['one_attempt']=value;rejects('outer_release_boolean:'+repr(value),lambda:c.verify_outer_invocation('redgc300',seal))
        release['one_attempt']=True;invocation['release_sha256']='wrong';rejects('outer_release_binding',lambda:c.verify_outer_invocation('redgc300',seal))
for phase in ('red300','green300','redgc600','greengc600','red600','greengc301'):
    rejects('phase_refusal:'+phase,lambda:c.config(phase))
for phase in ('redgc300','greengc300'):
    cfg=c.config(phase);cmd=c.guard_command(cfg,'synthetic-pins',10.)
    ck('fixed_limit:'+phase,cfg['seconds']==300 and cmd[cmd.index('--seconds')+1]=='292' and cmd[cmd.index('--deadline')+1]=='302.0')
# Independently verify original inventory mapping, stages, runtime resolved paths and source membership.
original=read(P/'preparation-pins.json'); changed={'audit.py','control.py','outer.py','ADMISSION.md'}
for n,h in original['sha256'].items():
    mapped=Path(n+'.before-review') if Path(n).parent==P and Path(n).name in changed else Path(n)
    ck('original_preserved:'+n,digest(mapped)==h)
ck('original2286',len(original['sha256'])==2286)
intermediate=read(P/'preparation-pins-reviewed.json')
ck('intermediate2314',len(intermediate['sha256'])==2314)
for n,h in intermediate['sha256'].items():
    mapped=P/'control.py.before-outcome-fix' if n==str(P/'control.py') else Path(n)
    ck('intermediate_preserved:'+n,digest(mapped)==h)
for n,h in read(P/'review-fix-source.json')['sha256'].items():
    mapped=P/'control.py.before-outcome-fix' if n==str(P/'control.py') else Path(n)
    ck('correction_source_preserved:'+n,digest(mapped)==h)
for mode,stage in read(P/'stages.json').items():
    root=Path(stage['path']); files=list(root.rglob('*'))
    ck('stage_membership:'+mode,{str(x.relative_to(root)) for x in files if x.is_file()}==set(stage['sha256']) and not root.is_symlink() and not any(x.is_symlink() for x in files))
for label,root in [('diagnostic',R),('production',c.W)]:
    actual=subprocess.check_output(['git','ls-files','src','test','.github','Project.toml'],cwd=root,text=True).splitlines()
    ck('source_membership:'+label,set(actual)==set(read(P/'baseline.json')[label]))
for n,v in read(P/'runtime-inputs-complete.json')['inventory'].items():
    ck('runtime_identity:'+n,str(Path(n).resolve(strict=True))==v['resolved'] and hashes[n]==v['sha256'])
# Membership derivation, without writing a seal.
cfg=c.config('redgc300');prepared=['synthetic-prepared'];extra=['synthetic-predecessor']
expected=set(prepared+extra+list(read(P/'runtime-inputs-complete.json')['inventory'])+[str(root/n) for label,root in [('diagnostic',R),('production',c.W)] for n in read(P/'baseline.json')[label]]+[str(Path(cfg['stage'])/n) for n in read(P/'stages.json')['red']['sha256']]+[str(Path(cfg['run'])/'host.json'),str(Path(cfg['run'])/'config.json'),str(c.outer_dir('redgc300')/'outer-ready.json')])
ck('seal_membership_real_derivation',c.seal_files(cfg,prepared,extra)==sorted(expected))
# Future preparation binds independent evidence explicitly, tested on mock metadata only.
mockdocs={str(P/'preparation-pins-final.json'):{'sha256':{'one':'h'}},str(P/'required-paths-final.json'):{'paths':['one']},str(P/'review.json'):{'evidence_sha256':{'review-evidence':'h'}},str(N/'preparation-pins-reviewed.json'):{'sha256':{}},str(N/'review.json'):{'launch_admitted':False},str(P/'copied-files.json'):{}}
with patch.object(c,'rd',lambda p:mockdocs[str(p)]),patch.object(c,'bindings',lambda *a:True),patch.object(c,'verify_review',lambda *a:None):
    ck('seal_review_evidence_included','review-evidence' in c.preparation())
# Full checks_for on independent synthetic files. No real admission, host check, or launch.
import audit as aud
cost_observations={}
with tempfile.TemporaryDirectory(prefix='independent-full-audit-') as td:
    t=Path(td); run=t/'run'; out=run/'output'; od=t/'outer';out.mkdir(parents=True);od.mkdir()
    runner=dict(pid=111,pgid=111,sid=111,start_ticks=1,boot_id='boot',command='synthetic guard')
    child=dict(pid=222,pgid=222,sid=222,start_ticks=2,boot_id='boot',command='synthetic child')
    basehost=dict(head='head',master='master',boot_id='boot',groups=[10],matches=[],unreadable_identity_pids=[])
    resource=dict(available_kib=7*1024**2,swap_used_kib=0)
    cfg=dict(phase='redgc300',mode='red',seconds=300,expected_exit=1,stage='synthetic',run=str(run),output=str(out),command=['synthetic child'])
    seal=dict(phase=cfg['phase'],config=cfg,head='head',master='master',boot_id='boot',groups=[10],files=[str(od/'outer-ready.json')],trees=[],inventory={})
    pins=dict(files=seal['files']+[str(run/n) for n in ('sealed.json','admission.json','prehost.json')]+[str(od/n) for n in ('release.json','outer-invocation.json')],trees=[],inventory={})
    process=dict(runner=runner,child=child,pins_unchanged=True,command=cfg['command'],pins_sha256='hash',terminal_memory=resource,child_maxrss_kib=100,returncode=1,reason='exit1')
    inv=dict(supervisor=dict(guard_identity=runner,returncode=0,accepted=True,elapsed_seconds=120.),elapsed_seconds=120.,command=cfg['command'],pins_sha256='hash',guard_command=['synthetic guard'],monotonic_start=1.,python=sys.executable,reservation_sha256='hash',review_sha256='hash')
    reservation=dict(one_attempt=True,phase=cfg['phase'],command=cfg['command'],pins_sha256='hash',review_sha256='hash',max_seconds=300)
    def setup(mode='red'):
        cfg.update(phase=mode+'gc300',mode=mode,expected_exit=1 if mode=='red' else 0);seal['phase']=cfg['phase'];reservation.update(phase=cfg['phase'],one_attempt=True)
        process.update(returncode=cfg['expected_exit'],reason='exit'+str(cfg['expected_exit']));inv['supervisor'].update(returncode=0,accepted=True,hard_timeout=False)
        r=raw(cfg['phase']);r['tests']['children']=[node(*x) for x in exp[mode]['groups']]
        docs={'sealed.json':seal,'config.json':cfg,'admission.json':{},'launch-pins.json':pins,'invocation.json':inv,'host.json':basehost,'prehost.json':basehost,'posthost.json':dict(basehost,groups=[10,111,222]),'reservation.json':reservation}
        output=dict(copy.deepcopy(windows if mode=='red' else green));output.update({f'preparation-{i}.toml':record(i,cfg['phase']) for i in range(1,4)})
        output.update({'raw.toml':r,'pins.json':pins,'current.json':dict(runner=runner,child=child,command=cfg['command'],pins_sha256='hash'),'process.json':process})
        for p in out.iterdir():p.unlink()
        for n,v in docs.items():(run/n).write_text(json.dumps(v))
        for n,v in output.items():(out/n).write_text(json.dumps(v))
        (out/'resources.jsonl').write_text(json.dumps(resource)+'\n');(out/'run.log').write_text('BEGIN BG specialization driver '+cfg['phase']+'\n'+('TEST FAILURE:\n'*3 if mode=='red' else ''));(run/'launcher.log').write_text('')
    def mutate(p,fn):
        j=read(p);fn(j);p.write_text(json.dumps(j))
    counts={}; realres=an.residual; realmatrix=an.matrix; realpartial=ao.partial_windows;realfull=ao.allocation_results
    def decode(s):counts['decode']=counts.get('decode',0)+1;return json.loads(s)
    def resid(*a):counts['residual']=counts.get('residual',0)+1;return realres(*a)
    def mat(*a):counts['matrix']=counts.get('matrix',0)+1;return realmatrix(*a)
    def partial(*a):counts['partial']=counts.get('partial',0)+1;return realpartial(*a)
    def complete(*a):counts['full']=counts.get('full',0)+1;return realfull(*a)
    with ExitStack() as stack:
        overrides=dict(config=lambda phase:cfg,validate_environment=lambda:None,preparation=lambda:[],validate_sources=lambda:None,predecessor=lambda phase:([],[]),verify_seal=lambda *a:None,verify_outer_invocation=lambda *a:None,verify_review=lambda *a:None,sha=lambda p:'hash',outer_dir=lambda phase:od,guard_command=lambda *a:['synthetic guard'],loaded_for=lambda cfg:{},rd=lambda p:{'fixtures':fixtures} if Path(p)==P/'inputs.json' else read(p))
        for name,fn in overrides.items():stack.enter_context(patch.object(aud,name,fn))
        for obj,name,fn in [(aud.guard,'pins_match',lambda *a:True),(aud.tomllib,'loads',decode),(an,'residual',resid),(ao,'matrix',mat),(ao,'partial_windows',partial),(ao,'allocation_results',complete)]:stack.enter_context(patch.object(obj,name,fn))
        for mode in ('red','green'):
            setup(mode);counts.clear();v=aud.checks_for(cfg['phase']);cost_observations[mode]=dict(counts)
            ck('full_auditor:'+mode,v['all_passed'] and v['result']['assertions']==(3 if mode=='red' else 8640) and len(v['preparation']['records'])==3)
            ck('single_validation_pass:'+mode,counts==dict(decode=64,full=1,matrix=54,residual=1440))
        mutations={
          'unknown_output':lambda:(out/'extra').write_text('{}'),
          'missing_window':lambda:(out/'window-1-7.toml').unlink(),
          'malformed_gc':lambda:(out/'preparation-1.toml').write_text('{'),
          'raw_counter':lambda:mutate(out/'raw.toml',lambda x:x.update(preparation_calls=2)),
          'gc_wall_exceeds_process':lambda:mutate(out/'preparation-1.toml',lambda x:x.update(seconds=121.)),
          'strict_reservation':lambda:mutate(run/'reservation.json',lambda x:x.update(one_attempt=1)),
          'post_session_missing':lambda:mutate(run/'posthost.json',lambda x:x.update(groups=[10,111])),
          'wrong_identity':lambda:mutate(out/'current.json',lambda x:x['child'].update(start_ticks=99)),
          'memory_pressure':lambda:mutate(out/'process.json',lambda x:x['terminal_memory'].update(available_kib=1)),
          'observed_compile':lambda:mutate(out/'window-1-7.toml',lambda x:x.update(compile_seconds=.1)),
          'bad_residual':lambda:mutate(out/'window-1-7.toml',lambda x:x['outputs'][0].__setitem__(0,bits(2))),
          'warning':lambda:(out/'run.log').write_text('Warning: synthetic'),
          'launch_membership':lambda:mutate(run/'launch-pins.json',lambda x:x['files'].pop())}
        for name,fn in mutations.items():setup();fn();rejects('full_auditor_refusal:'+name,lambda:aud.checks_for(cfg['phase']))
        setup()
        for p in list(out.iterdir()):
            if p.name.startswith('preparation-') or p.name=='raw.toml' or (p.name.startswith('window-') and p.name not in schedule[:6]):p.unlink()
        mutate(out/'process.json',lambda x:x.update(returncode=-15,reason='wall_time'))
        mutate(run/'invocation.json',lambda x:x['supervisor'].update(returncode=1,accepted=False,hard_timeout=False))
        (out/'run.log').write_text('BEGIN BG specialization driver redgc300');counts.clear();v=aud.checks_for('redgc300')
        ck('full_auditor_pure_timeout_failed',v['pure_timeout'] is True and v['all_passed'] is False and counts.get('partial')==1 and counts.get('residual')==144 and not counts.get('full'))
        (out/'preparation-1.toml').write_text('{');rejects('full_auditor_partial_malformed_not_timeout',lambda:aud.checks_for('redgc300'))
# Ensure no operational namespace was touched.
for name in ('runs','outers'):ck('still_absent:'+name,not (P/name).exists())
result=dict(all_checks_passed=all(checks.values()),accepted=True,findings=[],checks=checks,full_manifest=fullhash,refs=refs,host=host,scope=__doc__,synthetic_coverage='All61prefixes, exact17schema, raw counters, known2x2residuals, exactRED3/GREEN8640, independent full checks_for on synthetic files, admission/seal/release/predecessor/evidence boundaries, exact preserved initial mapping; no operational main or audit()',cost_observations=cost_observations,limitations=['Full auditor tests mock host/ref/hash/admission and TOML codec; external and real-codec behavior is not proven.','No runtime/performance/GC-cure/numerical-neutrality claim.','Unreadable exe links disclosed; stat/comm/argv0 checked.'])
with (P/'independent-check.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(dict(checks=len(checks),hashes=len(hashes),bytes=size,cost_observations=cost_observations,findings=findings),indent=2))
