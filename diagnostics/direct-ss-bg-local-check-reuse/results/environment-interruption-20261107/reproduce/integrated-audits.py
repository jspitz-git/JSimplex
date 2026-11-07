"""Replay the six shadow oracles on the integrated runtime, one locked process at a time."""
import fcntl
import hashlib
import json
import os
import subprocess
import time
import tomllib
from contextlib import ExitStack
from pathlib import Path

suite = Path(__file__).resolve().parents[1]
root = suite.parents[1]
out = suite / 'results/integration'
model = Path('/home/jspitz/mps/runtime.mps')
env = dict(os.environ, JULIA_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
stable = ('options', 'input_sha', 'status', 'original_feasible', 'objective_bits', 'primal_sha',
          'iterations', 'steps', 'entries', 'refactors', 'mode', 'mode_initial', 'mode_refactors')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_new(path, data):
    with path.open('x') as f:
        json.dump(data, f, indent=2)
        f.write('\n')

def main():
    out.mkdir(exist_ok=True)
    files = [*sorted((root/'src').rglob('*.jl')), root/'Project.toml', root/'Manifest.toml',
             root/'diagnostics/basis-direct-lu/reproduce/direct.jl', root/'diagnostics/hh-local-check-reuse/reproduce/audit.jl',
             root/'diagnostics/ft-local-incidence/reproduce/afiro.mps', model, Path(__file__).resolve(),
             suite/'reproduce/integrated-shadow.jl', suite/'reproduce/worker.jl',
             root/'diagnostics/direct-ft-local-check-reuse/reproduce/worker.jl']
    pins = {str(p): digest(p) for p in files}
    result = {}
    with ExitStack() as stack:
        locks = []
        for path in sorted((root/'diagnostics').rglob('suite.lock')):
            if path.parent.name == 'results' and 'results' not in path.parent.parent.relative_to(root).parts:
                fd = stack.enter_context(path.open())
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                locks.append(fd.fileno())
        write_new(out/'sources.json', pins)
        for manager in ('forrest_tomlin', 'suhl_suhl', 'bartels_golub'):
            for mode in ('direct', 'normalized'):
                variant = manager+'_'+mode
                ft = manager == 'forrest_tomlin'
                prior = root/'diagnostics/direct-ft-local-check-reuse' if ft else suite
                arg = mode if ft else variant
                baseline = prior/'results'/arg/'shadow.toml'
                p = out/(variant+'.toml')
                assert all(digest(Path(k)) == v for k,v in pins.items())
                write_new(out/(variant+'.started.json'), {'start':time.time(),'locks':len(locks)})
                with (out/(variant+'.log')).open('x') as log:
                    child = subprocess.run(['julia','--startup-file=no','--compiled-modules=existing','--project='+str(root),
                        str(suite/'reproduce/integrated-shadow.jl'),arg,'shadow',str(model),str(p),
                        str(prior/'reproduce/worker.jl')], cwd=root, env=env, pass_fds=locks,
                        stdout=log, stderr=subprocess.STDOUT)
                write_new(out/(variant+'.process.json'), {'end':time.time(),'exit':child.returncode})
                child.check_returncode()
                actual, expected = (tomllib.loads(f.read_text()) for f in (p, baseline))
                a,b = (tomllib.loads(Path(str(f)+'.audit.toml').read_text()) for f in (p,baseline))
                assert all(actual[k] == expected[k] for k in stable)
                assert actual['status'] == 'OPTIMAL' and actual['original_feasible']
                assert a['counts'] == b['counts'] and a['sha256'] == b['sha256'] and a['modes'] == b['modes']
                assert all(digest(Path(k)) == v for k,v in pins.items())
                result[variant] = dict(endpoint={k:actual[k] for k in stable}, counts=a['counts'],
                    trace_sha256=a['sha256'], publications=len(a['modes']), report_sha256=digest(p),
                    audit_sha256=digest(Path(str(p)+'.audit.toml')), reference_sha256=digest(baseline),
                    reference_audit_sha256=digest(Path(str(baseline)+'.audit.toml')))
                write_new(out/(variant+'.comparison.json'), result[variant])
        write_new(out/'verification.json', result)
if __name__ == '__main__':
    main()
