import fcntl,json,os,subprocess,tomllib
from pathlib import Path
from contextlib import ExitStack
suite=Path(__file__).resolve().parents[1]
root=suite.parents[1]
out=suite/'results/probe'
out.mkdir(exist_ok=True)
with ExitStack() as stack:
    locks=[]
    for p in sorted((root/'diagnostics').rglob('suite.lock')):
        if p.parent.name=='results' and 'results' not in p.parent.parent.relative_to(root).parts:
            f=stack.enter_context(p.open());fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f.fileno())
    for pricing in ('dantzig','steepest_edge'):
        for arm in ('reference-audit','shadow'):
            p=out/(pricing+'-'+arm+'.toml')
            assert not p.exists()
            with p.with_suffix('.log').open('x') as log:
                subprocess.run(['julia','--startup-file=no','--compiled-modules=existing','--project='+str(suite/'snapshot'),
                    str(suite/'reproduce/worker.jl'),'huangfu_hall-production',pricing,arm,
                    str(suite/'reproduce/afiro.mps'),str(p)],check=True,cwd=root,
                    env=dict(os.environ,JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),pass_fds=locks,
                    stdout=log,stderr=subprocess.STDOUT)
        a,b=[tomllib.loads((out/(pricing+'-'+arm+'.toml')).read_text()) for arm in ('reference-audit','shadow')]
        for k in ('primal_sha','objective_bits','status','iterations','refactors','original_feasible'):
            assert a[k]==b[k]
        a,b=[tomllib.loads((out/(pricing+'-'+arm+'.toml.audit.toml')).read_text()) for arm in ('reference-audit','shadow')]
        assert a['sha256']==b['sha256'] and a['modes']==b['modes'] and a['switches']==b['switches']
        assert all(b['counts'][k]==v for k,v in a['counts'].items())
        assert all(b['pricing_counts'][k]==v for k,v in a['pricing_counts'].items())
        print(pricing,'exact smoke audit passed',flush=True)
