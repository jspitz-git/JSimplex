"""Serialized legacy pricing experiment. Interrupted started jobs require explicit recovery."""
import csv
import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import tomllib
from contextlib import ExitStack
from pathlib import Path

suite = Path(__file__).resolve().parents[1]
root = suite.parents[1]
out = suite/'results'
model = Path('/home/jspitz/mps/runtime.mps')
profiles = [m+'-production' for m in ('huangfu_hall','forrest_tomlin','suhl_suhl','bartels_golub','pfi')]
profiles += [m+'-'+r for m in ('forrest_tomlin','suhl_suhl','bartels_golub') for r in ('direct','normalized')]
combinations = [(p,q) for p in profiles for q in ('dantzig','steepest_edge')]
final_keys = ('profile','pricing','mode','input_sha','options','status','original_feasible','primal_sha',
              'objective_bits','iterations','refactors','mode_initial','mode_refactors','steps','entries')
expected_sha = 'd0ac16e1a52a7d3411cbac28616bba9d3beb0c0edbdb2d72ab0477ce075f6c68'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path):
    return tomllib.loads(path.read_text())

def create(path, data):
    with path.open('x') as f:
        json.dump(data,f,indent=2)
        f.write('\n')

def status(**fields):
    p=out/'status.tmp'
    p.write_text(json.dumps(dict(updated=time.time(),**fields),indent=2)+'\n')
    p.replace(out/'status.json')

def final_check(d):
    assert d['input_sha']==expected_sha and d['arch']=='aarch64'
    assert d['threads']==d['blas_threads']==1
    assert math.isfinite(d['seconds']) and d['seconds']>0 and 0<d['loop']<=d['seconds']
    assert d['mode_initial']>=1 and d['mode_refactors']==d['refactors']
    assert d['status']!='OPTIMAL' or d['original_feasible'] is True

def compare(folder,name):
    d=load(folder/(name+'.toml'))
    final_check(d)
    if name=='reference-audit':
        return dict(final_valid=True)
    ref=load(folder/'reference-audit.toml')
    assert all(d[k]==ref[k] for k in final_keys)
    result=dict(exact_endpoint=True,report_sha256=digest(folder/(name+'.toml')))
    if name=='shadow':
        a,b=[load(folder/(n+'.toml.audit.toml')) for n in ('reference-audit','shadow')]
        assert a['sha256']==b['sha256'] and a['modes']==b['modes'] and a['switches']==b['switches']
        assert all(b['counts'].get(k)==v for k,v in a['counts'].items())
        assert all(b['pricing_counts'].get(k)==v for k,v in a['pricing_counts'].items())
        assert len(a['modes'])==d['mode_initial']+d['mode_refactors']
        result.update(exact_trace=True,exact_modes=True,exact_switches=True,trace_sha256=b['sha256'],
            counts=b['counts'],pricing_counts=b['pricing_counts'],switches=b['switches'])
    return result

def schedule():
    for p in profiles:
        yield p,'steepest_edge','unit'
    for p,q in combinations:
        for name in ('reference-audit','shadow'):
            yield p,q,name
    first=[(p,q,a) for p,q in combinations for a in ('reference','candidate')]
    for i,order in ((1,first),(2,list(reversed(first)))):
        for p,q,a in order:
            yield p,q,a+'.'+str(i)

def execute(p,q,name,locks,pins):
    folder=out/p/q
    folder.mkdir(parents=True,exist_ok=True)
    report=folder/(name+'.toml')
    start=time.time()
    create(folder/(name+'.started.json'),dict(start=start,profile=p,pricing=q,job=name))
    file='unit.jl' if name=='unit' else 'worker.jl'
    cmd=['julia','--startup-file=no','--compiled-modules=existing','--project='+str(suite/'snapshot'),
         str(suite/'reproduce'/file),p,q,name.split('.')[0],str(model),str(report)]
    with (folder/(name+'.log')).open('x') as log, (folder/(name+'.cpu.csv')).open('x') as cpu:
        child=subprocess.Popen(cmd,cwd=root,env=dict(os.environ,JULIA_NUM_THREADS='1',
            OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),pass_fds=locks,stdout=log,stderr=subprocess.STDOUT)
        w=csv.writer(cpu,lineterminator='\n')
        w.writerow(('unix_time','user_ticks','system_ticks','last_vcpu','major_faults','minor_faults','running_ns','waiting_ns'))
        while True:
            status(state='running',profile=p,pricing=q,job=name,start=start,pid=child.pid)
            try:
                code=child.wait(timeout=10)
                break
            except subprocess.TimeoutExpired:
                try:
                    t=Path('/proc')/str(child.pid)
                    s=(t/'stat').read_text().rsplit(') ',1)[1].split()
                    sched=(t/'schedstat').read_text().split()
                    w.writerow([time.time(),s[11],s[12],s[36],s[9],s[7],*sched[:2]])
                    cpu.flush()
                except (FileNotFoundError,ProcessLookupError):
                    pass
    create(folder/(name+'.process.json'),dict(start=start,end=time.time(),exit=code,locks=len(locks),
        report_sha256=digest(report) if report.exists() else None))
    assert all(digest(Path(k))==v for k,v in pins.items())
    if code:
        raise RuntimeError(f'{p}/{q}/{name}: child exit {code}')
    if name=='unit':
        assert load(report)['passed']
        return None
    if Path(str(report)+'.warmup-failure.toml').exists():
        return dict(job=name,reason='warmup_failure',report=str(report)+'.warmup-failure.toml')
    d=load(report)
    final_check(d)
    if d['status']!='OPTIMAL':
        return dict(job=name,reason='nonoptimal',status=d['status'],message=d['message'],report=str(report))
    create(folder/(name+'.comparison.json'),compare(folder,name))
    return None

def main():
    out.mkdir(exist_ok=True)
    (out/'suite.lock').touch(exist_ok=True)
    skipped=[]; excluded={}
    with ExitStack() as stack:
        locks=[]
        for p in sorted((root/'diagnostics').rglob('suite.lock')):
            if p.parent.name=='results' and 'results' not in p.parent.parent.relative_to(root).parts:
                f=stack.enter_context(p.open())
                fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                locks.append(f.fileno())
        assert digest(model)==expected_sha
        files=[p for where in (suite/'reproduce',suite/'snapshot') for p in sorted(where.rglob('*'))
               if p.is_file() and '__pycache__' not in p.parts]
        files += [suite/'PLAN.md',suite/'README.md',out/'source-provenance.json']
        pins={str(p):digest(p) for p in files}
        create(out/'sources.json',pins)
        create(out/'plan.json',dict(jobs=list(schedule()),input_sha=expected_sha,profiles=profiles,pricing=['dantzig','steepest_edge']))
        try:
            for p,q,name in schedule():
                assert all(digest(Path(k))==v for k,v in pins.items())
                if (p,q) in excluded:
                    skipped.append(dict(profile=p,pricing=q,job=name,**excluded[p,q]))
                    (out/'skipped.json').write_text(json.dumps(skipped,indent=2)+'\n')
                    continue
                reason=execute(p,q,name,locks,pins)
                if reason:
                    excluded[p,q]={'cause':reason}
            (out/'skipped.json').write_text(json.dumps(skipped,indent=2)+'\n')
            status(state='finished',completed_plan=True,excluded=[dict(profile=p,pricing=q,**v) for (p,q),v in excluded.items()])
        except BaseException as e:
            status(state='failed',exception=repr(e))
            raise
if __name__=='__main__':
    main()
