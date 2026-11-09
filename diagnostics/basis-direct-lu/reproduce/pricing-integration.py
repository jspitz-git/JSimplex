"""Invoked under the root integration lock launcher; inherit all locked FDs."""
from pathlib import Path
import subprocess,os,json,time,hashlib
root=Path(__file__).resolve().parents[3]
out=root/'diagnostics/basis-direct-lu/results/pricing-check-integration'
for mode in ('direct','normalized'):
    start=time.time()
    cmd=['julia','--startup-file=no','--compiled-modules=existing','--project='+str(root),str(root/'diagnostics/basis-direct-lu/reproduce/check-reuse.jl'),mode]
    with (out/(mode+'.log')).open('x') as f:
        r=subprocess.run(cmd,cwd=root,close_fds=False,stdout=f,stderr=subprocess.STDOUT)
    (out/(mode+'.process.json')).write_text(json.dumps(dict(start=start,end=time.time(),exit=r.returncode,mode=mode,log_sha256=hashlib.sha256((out/(mode+'.log')).read_bytes()).hexdigest()),indent=2)+'\n')
    if r.returncode:raise SystemExit(r.returncode)
