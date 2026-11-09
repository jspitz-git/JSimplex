"""One serialized, pinned experiment. No retries of started jobs."""
import csv,fcntl,hashlib,json,os,subprocess,time,tomllib
from contextlib import ExitStack
from pathlib import Path
from acceptance import valid_outcome
suite=Path(__file__).resolve().parents[1]; root=suite.parents[1]; out=suite/'results'
predecessor=root/'diagnostics/legacy-pricing-check-reuse/results'
model=Path('/home/jspitz/mps/runtime.mps')
expected_sha='d0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'
profiles=['huangfu_hall-production','forrest_tomlin-production'];arms=['off','passive','active']
core_keys=('profile','pricing','mode','input_sha','options','status','original_feasible','primal_sha',
    'objective_bits','iterations','refactors','mode_initial','mode_refactors','steps','entries',
    'certificate_calls','certificate_true','certificate_last')
own_keys=core_keys+('arm','quality_observed','quality_counts')
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p): return tomllib.loads(Path(p).read_text())
def read_json(p): return json.loads(Path(p).read_text())
def create(p,d):
    with Path(p).open('x') as f: json.dump(d,f,indent=2);f.write('\n')
def status(**kw):
    p=out/'status.tmp';p.write_text(json.dumps(dict(updated=time.time(),**kw),indent=2)+'\n');p.replace(out/'status.json')
def schedule():
    for p in profiles:
        yield p,'unit','off-unit'
        yield p,'unit','active-unit'
    for inp in ('afiro','sc50a'):
        for p in profiles:
            for a in arms: yield p,inp,a+'-audit'
    for p in profiles:
        for a in arms: yield p,'runtime',a+'-audit'
    first=[(p,'runtime',a+'.1') for p in profiles for a in arms]
    yield from first
    for p,inp,a in reversed(first): yield p,inp,a[:-1]+'2'
def input_path(inp): return model if inp=='runtime' else suite/'reproduce'/(inp+'.mps')
def final_check(d,inp):
    assert d['arch']=='aarch64' and d['threads']==d['blas_threads']==1
    assert d['input_sha']==digest(input_path(inp))
    assert d['mode']=='production' and d['mode_initial']>=1 and d['mode_refactors']==d['refactors']
    return valid_outcome(d)
def compare(folder,name):
    d=load(folder/(name+'.toml'));a=name.split('-')[0].split('.')[0]
    if name.endswith('-audit'):
        evidence=load(folder/(name+'.toml.audit.toml'))
        assert len(evidence['modes'])==d['mode_initial']+d['mode_refactors']
        assert evidence['quality_counts']==d['quality_counts']
        if a=='passive':
            off=load(folder/'off-audit.toml');orig=load(folder/'off-audit.toml.audit.toml')
            assert all(d[k]==off[k] for k in core_keys)
            assert all(evidence[k]==orig[k] for k in ('sha256','counts','modes','sampled_transitions'))
            return dict(exact_off_endpoint=True,exact_off_trace=True,report_sha=digest(folder/(name+'.toml')))
        return dict(accepted=True,report_sha=digest(folder/(name+'.toml')),trace_sha=evidence['sha256'])
    audit=load(folder/(a+'-audit.toml'))
    assert all(d[k]==audit[k] for k in own_keys)
    return dict(exact_own_audit=True,report_sha=digest(folder/(name+'.toml')))
def verify_pins():
    for manifest in ('sources.json','references.json'):
        assert all(digest(k)==v for k,v in read_json(out/manifest).items())
    assert digest(model)==expected_sha

def predecessor_ready(state): return state.get("state")=="finished"

def acquire_predecessors(paths):
    while True:
        stack=ExitStack()
        try:
            state=read_json(predecessor/'status.json')
            if not predecessor_ready(state): raise BlockingIOError('predecessor '+state.get('state','unknown'))
            fs=[]
            for p in paths:
                f=stack.enter_context(Path(p).open());fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fs.append(f.fileno())
            if not predecessor_ready(read_json(predecessor/'status.json')): raise BlockingIOError('predecessor changed')
            return stack,fs
        except BlockingIOError as e:
            stack.close();status(state='waiting_for_previous_measurements',reason=str(e));time.sleep(10)
        except BaseException:
            stack.close();raise

def execute(p,inp,name,locks):
    verify_pins();folder=out/p/inp;folder.mkdir(parents=True,exist_ok=True)
    report=folder/(name+'.toml');start=time.time()
    create(folder/(name+'.started.json'),dict(start=start,profile=p,input=inp,job=name))
    script='unit.jl' if inp=='unit' else 'worker.jl'
    arg=name.split('.')[0]
    target=model if inp=='unit' else input_path(inp)
    cmd=['julia','--startup-file=no','--compiled-modules=existing','--project='+str(suite/'snapshot'),
        str(suite/'reproduce'/script),p,'devex',arg,str(target),str(report)]
    with (folder/(name+'.log')).open('x') as log,(folder/(name+'.cpu.csv')).open('x') as cpu:
        child=subprocess.Popen(cmd,cwd=root,env=dict(os.environ,JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),
            pass_fds=locks,stdout=log,stderr=subprocess.STDOUT)
        w=csv.writer(cpu);w.writerow(('time','user_ticks','system_ticks','running_ns','waiting_ns'))
        while True:
            status(state='running',profile=p,input=inp,job=name,start=start,pid=child.pid)
            try:
                code=child.wait(timeout=10);break
            except subprocess.TimeoutExpired:
                try:
                    proc=Path('/proc')/str(child.pid);s=(proc/'stat').read_text().rsplit(') ',1)[1].split()
                    sched=(proc/'schedstat').read_text().split();w.writerow((time.time(),s[11],s[12],*sched[:2]));cpu.flush()
                except (FileNotFoundError,ProcessLookupError): pass
    process=dict(start=start,end=time.time(),exit=code,locks=len(locks),report_sha=digest(report) if report.exists() else None)
    create(folder/(name+'.process.json'),process)
    verify_pins()
    if inp=='unit':
        d=load(report)
        if name=='off-unit':
            log=(folder/(name+'.log')).read_text()
            assert code==1 and d['expected_original_failure'] is True and d['passed'] is False
            assert d['ordinary_pivot_completed'] is True and d['iterations']==1
            assert 'Test Failed' in log and 'Error During Test' not in log
        else:
            assert code==0 and d['passed'] is True
        return None
    assert code==0,process
    warm=Path(str(report)+'.warmup-failure.toml')
    if warm.exists(): return dict(reason='warmup_failure',report=str(warm))
    d=load(report)
    if not final_check(d,inp):
        return dict(reason='nonoptimal',status=d['status'],message=d['message'],report=str(report))
    create(folder/(name+'.comparison.json'),compare(folder,name))
    return None

def main():
    (out/'suite.lock').touch(exist_ok=True)
    sources={str(p):digest(p) for where in (suite/'snapshot',suite/'reproduce') for p in sorted(where.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
    for p in (suite/'PLAN.md',suite/'README.md',out/'source-provenance.json'): sources[str(p)]=digest(p)
    references={str(predecessor/'sources.json'):digest(predecessor/'sources.json'),**read_json(predecessor/'sources.json')}
    locks=[predecessor/'suite.lock']+[p for p in sorted((root/'diagnostics').rglob('suite.lock'))
        if p.parent.name=='results' and 'results' not in p.parent.parent.relative_to(root).parts and p not in (out/'suite.lock',predecessor/'suite.lock')]
    create(out/'sources.json',sources);create(out/'references.json',references)
    create(out/'plan.json',dict(jobs=list(schedule()),predecessor_locks=list(map(str,locks)),threshold_squared_ratio=9,input_sha=expected_sha))
    blocked={};skipped=[]
    with (out/'suite.lock').open() as own:
        fcntl.flock(own,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            held,fds=acquire_predecessors(locks)
            with held:
                verify_pins()
                for p,inp,name in schedule():
                    a=name.split('-')[0].split('.')[0]
                    reason=blocked.get((p,'*')) or blocked.get((p,a))
                    if inp=='runtime' and reason:
                        skipped.append(dict(profile=p,input=inp,job=name,cause=reason))
                    else:
                        cause=execute(p,inp,name,tuple([own.fileno(),*fds]))
                        if cause:
                            create(out/p/inp/(name+'.outcome.json'),cause)
                            if inp!='runtime' or a=='passive': raise RuntimeError(f'{p}/{inp}/{name}: {cause}')
                            blocked[p,'*' if a=='off' else a]=cause
                    (out/'skipped.json').write_text(json.dumps(skipped,indent=2)+'\n')
                status(state='finished',completed_plan=True,excluded=[dict(profile=p,arm=a,cause=r) for (p,a),r in blocked.items()])
        except BaseException as e:
            status(state='failed',exception=repr(e));raise
if __name__=='__main__': main()
