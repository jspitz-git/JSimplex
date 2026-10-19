"""Release exactly one independently accepted RED2; never creates admission or retries."""
from pathlib import Path
import sys
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');H=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-BLOCKED-UPDATE-RED2-HARNESS';D=H.with_name('DIRECT-BG-BLOCKED-UPDATE-RED2');sys.path.insert(0,str(H));import control as c
phase='red300';run=H/'runs'/phase;o=c.outer_dir(phase);sp=run/'sealed.json';rp=run/'admission.json';s=c.rd(sp)
c.verify_review(c.rd(rp),sp,s['files']+[str(sp)],'BG blocked U RED2 exact-stage admission',phase)
c.verify_seal(c.config(phase),s);c.validate_environment();c.validate_sources();c.verify_outer(phase,s,live=True)
h=c.full_host(s['groups']);h['memory']=c.guard.memory();c.require(c.host_safe(h) and not c.guard.pressure(h['memory']) and all(h[k]==s[k] for k in ['head','master','boot_id']),'Release host drift')
c.require(not c.git('diff','HEAD','--name-only'),'Tracked changes')
c.require(not (run/'reservation.json').exists() and not Path(s['config']['output']).exists() and not (o/'release.json').exists(),'Attempt already used')
c.save(D/'release-preflight.json',dict(all_passed=True,host=h,sha256={str(sp):c.sha(sp),str(rp):c.sha(rp),str(o/'outer-ready.json'):c.sha(o/'outer-ready.json')},scope=__doc__))
c.save(o/'release.json',dict(phase=phase,sealed_sha256=c.sha(sp),admission_sha256=c.sha(rp),outer_ready_sha256=c.sha(o/'outer-ready.json'),one_attempt=True))
print('Released one independently admitted RED2, inclusive300s')
