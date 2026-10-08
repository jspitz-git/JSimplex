"""Run the selected regressions serially without changing pinned solver sources."""
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[3]
out = Path(sys.argv[1]).resolve()
out.mkdir(parents=True, exist_ok=False)
guard = '/home/jspitz/JSimplex.jl/.worktrees/primal-direction-prices/.superpowers/primal-prices/guard.py'
wrapper = '/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/diagnostics/basis-memory/reproduce/julia.sh'
def digest():
    h = hashlib.sha256()
    for p in sorted([root/'Project.toml', *(root/'src').rglob('*.jl')], key=lambda p:str(p.relative_to(root))):
        h.update(str(p.relative_to(root)).encode()+b'\0'+p.read_bytes())
    return h.hexdigest()
def save(name, data):
    (out/name).write_text(json.dumps(data, indent=2)+'\n')

jobs = [
    ('targeted', 600, ['diagnostics/numerical-guard-repair/reproduce/dual_targeted.jl']),
    ('semantic', 600, ['--compile=min', 'diagnostics/primal-row-memory/reproduce/semantic.jl']),
    ('greenbea', 600, ['diagnostics/numerical-guard-repair/reproduce/capture.jl',
        '/home/jspitz/NetLib/greenbea.mps', 'bartels_golub', 'native', str(out/'greenbea')]),
    ('runtime', 2100, ['diagnostics/native-certificate-recovery/reproduce/runtime.jl', str(out/'runtime.toml')]),
]
with (out/'runner.lock').open('w') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    pinned = digest()
    save('source.json', {'source_sha256': pinned})
    for name, seconds, args in jobs:
        assert subprocess.run(['pgrep', '-x', 'julia'], stdout=subprocess.DEVNULL).returncode == 1
        assert digest() == pinned, 'Solver sources changed'
        save('current.json', {'job': name, 'state': 'running', 'started': time.time()})
        command = ['/usr/bin/time', '-v', 'python3', guard, '--seconds', str(seconds),
            'bash', wrapper, '--heap-size-hint=2G', '--project=.', '-g0', '-O1', *args]
        started = time.monotonic()
        with (out/(name+'.log')).open('w') as log:
            result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        unchanged = digest() == pinned
        save(name+'-process.json', {'exit_code': result.returncode,
            'seconds': time.monotonic()-started, 'source_sha256': pinned, 'source_unchanged': unchanged})
        print(name, result.returncode, flush=True)
        if result.returncode or not unchanged:
            save('current.json', {'job': name, 'state': 'failed'})
            raise SystemExit(1)
    save('current.json', {'state': 'finished'})
