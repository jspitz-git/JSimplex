"""Targeted Julia checks with inherited locks; no full runtime solves."""
import fcntl,subprocess,os,sys
from pathlib import Path
from contextlib import ExitStack
root=Path(__file__).resolve().parents[2]
with ExitStack() as stack:
    locks=[]
    for p in sorted((root/'diagnostics').rglob('suite.lock')):
        if p.parent.name=='results' and 'results' not in p.parent.parent.relative_to(root).parts:
            f=stack.enter_context(p.open());fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);locks.append(f.fileno())
    child=subprocess.run(sys.argv[1:],cwd=root,pass_fds=locks,env=dict(os.environ,JULIA_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
    sys.exit(child.returncode)
