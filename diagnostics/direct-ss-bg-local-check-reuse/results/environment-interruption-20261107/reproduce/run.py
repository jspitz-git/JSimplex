"""Serial comparison of direct and normalized FT, preserving completed jobs and mode/audit evidence."""
import fcntl, json, os, subprocess, time, tomllib
from contextlib import ExitStack
from hashlib import sha256
from pathlib import Path
suite=Path(__file__).resolve().parents[1]
root=suite.parents[1]
out=suite/'results'
managers=tuple(f'{m}_{mode}' for m in ('suhl_suhl','bartels_golub') for mode in ('direct','normalized'))
model=Path('/home/jspitz/mps/runtime.mps')
old=root/'diagnostics/runtime-full-chain-comparison/ss-bg-breakdown/results'
def prior(m): return old/f'jsimplex-{m}-160-repeat1.toml'
def sha(p): return sha256(p.read_bytes()).hexdigest()
def read(p): return tomllib.loads(p.read_text())
def create(p,d):
    with p.open('x') as f: json.dump(d,f,indent=2)
def jobs():
    for m in managers: yield m,'unit','unit'
    for m in managers:
        for a in ('reference-audit','shadow'): yield m,a,a
    first=[(m,a) for m in managers for a in ('reference','candidate')]
    for i,order in ((1,first),(2,reversed(first))):
        for m,a in order: yield m,a,f'{a}.{i}'

def verify(folder,m,name):
    if name=='unit': return {}
    d=read(folder/(name+'.toml'))
    e=read(prior(m))
    mode=m.rsplit('_',1)[1]
    from struct import pack
    archive_keys={'input_sha':'input_sha256','iterations':'iterations','refactors':'refactorizations','original_feasible':'original_primal_feasible'}
    assert all(d[k]==e[v] for k,v in archive_keys.items())
    assert int(d['objective_bits'],16)==int.from_bytes(pack('>d',e['objective']),'big')
    assert d['status']==e['status']=='OPTIMAL' and d['original_feasible'] and 0<d['loop']<=d['seconds']
    assert d['threads']==d['blas_threads']==1 and d['arch']=='aarch64' and 0<d['steps']<=d['iterations']
    assert d['variant']==m and d['mode']==mode and d['mode_initial']+d['mode_refactors']==1+d['refactors']==e['factory_modes'][mode]
    if name in ('reference-audit','shadow'):
        audit=read(folder/(name+'.toml.audit.toml')); modes=audit['modes']
        assert len(modes)==1+d['refactors'] and modes[0]['site']=='initial'
        for site,count in [('initial',d['mode_initial']),('refactor',d['mode_refactors'])]:
            assert sum(r['site']==site for r in modes)==count
        assert all(r['mode']==mode and r['dimension']>0 and (mode!='normalized' or r['unit_upper']) for r in modes)
    if name=='shadow':
        baseline=read(folder/'reference-audit.toml.audit.toml')
        assert audit['sha256']==baseline['sha256'] and modes==baseline['modes']
        assert all(audit['counts'].get(k)==v for k,v in baseline['counts'].items())
        assert all(audit['counts'][k]>0 for k in ('row_reused','finite_reused','from_last_pivot','driver_entry'))
    if name!='reference-audit':
        ref=read(folder/'reference-audit.toml')
        assert all(d[k]==ref[k] for k in ('input_sha','primal_sha','objective_bits','original_feasible','status','iterations','steps','entries','refactors','mode_initial','mode_refactors','mode','options'))
    return d

def main():
    with ExitStack() as stack:
        (out/'suite.lock').touch(exist_ok=True)
        locks=[]
        for p in sorted((root/'diagnostics').rglob('suite.lock')):
            if p.parent.name=='results' and 'results' not in p.parent.parent.relative_to(root).parts:
                f=stack.enter_context(p.open());fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f)
        files=[*sorted((root/'src').rglob('*.jl')),Path(__file__).resolve(),suite/'reproduce/worker.jl',
               root/'Project.toml',root/'Manifest.toml',root/'diagnostics/ft-local-incidence/reproduce/afiro.mps',
               root/'diagnostics/hh-local-check-reuse/reproduce/audit.jl',
               root/'diagnostics/runtime-full-chain-comparison/ss-bg-breakdown/reproduce/direct.jl',*(prior(m) for m in managers)]
        pins={str(p.relative_to(root)):sha(p) for p in files}
        assert sha(model)==read(prior(managers[0]))['input_sha256']
        create(out/'pins.json',pins)
        for manager,arm,name in jobs():
            folder=out/manager;folder.mkdir(exist_ok=True)
            assert all(sha(root/k)==v for k,v in pins.items())
            start=time.time()
            create(folder/(name+'.started.json'),dict(manager=manager,arm=arm,job=name,start=start))
            report=folder/(name+'.toml')
            with (folder/(name+'.log')).open('x') as log:
                p=subprocess.run(['julia','--startup-file=no','--compiled-modules=existing','--project='+str(root),
                    str(suite/'reproduce/worker.jl'),manager,arm,str(model),str(report)],cwd=root,
                    env=dict(os.environ,JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'),
                    stdout=log,stderr=subprocess.STDOUT,pass_fds=tuple(f.fileno() for f in locks))
            create(folder/(name+'.process.json'),dict(start=start,end=time.time(),exit=p.returncode,locks=len(locks),
                sha=sha(report) if report.exists() else None))
            p.check_returncode()
            verify(folder,manager,name)
            assert all(sha(root/k)==v for k,v in pins.items())
if __name__=='__main__': main()
