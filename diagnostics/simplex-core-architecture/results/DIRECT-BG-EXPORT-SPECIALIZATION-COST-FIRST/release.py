"""One explicit release after independent exact admission; no direct Julia launch."""
from pathlib import Path
import sys,json
Q=Path(__file__).resolve().parent;P=Q.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-COST');sys.path.insert(0,str(P));import control as c
phase='cost1-300';run=P/'runs'/phase;o=P/'outers'/phase;sp=run/'sealed.json';rp=run/'admission.json';s=c.rd(sp)
c.verify_review(c.rd(rp),sp,s['files']+[str(sp)],'BG specialized export cost admission',phase)
c.verify_outer(phase,s,live=True);c.validate_environment();c.require(c.guard.pins_match(s),'Sealed bytes changed')
h=c.full_host(s['groups']);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
c.require(c.host_safe(h) and not c.guard.pressure(h['memory']) and all(h[k]==s[k] for k in ['head','master','boot_id']),'Fresh final host refusal')
c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'Remote refs changed')
c.require(not (run/'reservation.json').exists() and not (run/'output').exists() and not (o/'release.json').exists(),'Attempt already reserved/released')
c.save(Q/'release-host.json',h)
c.save(o/'release.json',dict(phase=phase,sealed_sha256=c.sha(sp),admission_sha256=c.sha(rp),outer_ready_sha256=c.sha(o/'outer-ready.json'),one_attempt=True))
print('Released exactly one independently admitted cost1-300 attempt.')
