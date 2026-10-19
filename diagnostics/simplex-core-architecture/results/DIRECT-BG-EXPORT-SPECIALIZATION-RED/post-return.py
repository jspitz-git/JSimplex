"""Separate post-return outer process closure; never rerun numerical audit."""
from pathlib import Path
import sys,json,time
R=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl');D=R/'diagnostics/simplex-core-architecture/results/DIRECT-BG-EXPORT-SPECIALIZATION-DRIVER';Q=D.with_name('DIRECT-BG-EXPORT-SPECIALIZATION-RED');RUN=D/'runs/red300'
sys.path.insert(0,str(D));import control as c
outcome=c.rd(Q/'outer-outcome.json');ready=c.rd(Q/'outer-ready.json');outer=ready['identity']
c.require(outcome['identity']==outer,'Outer identity mismatch')
groups=c.rd(D/'host-closure.json')['groups']+[outer['pgid'],outer['sid']]
for p in [RUN/'posthost.json']:
 if p.exists():groups+=c.rd(p)['groups']
for p in [RUN/'output/current.json',RUN/'output/process.json']:
 if p.exists():
  for role in ['runner','child']:
   z=c.rd(p)[role];groups += [z['pgid'],z['sid']]
h=c.full_host(groups);h['memory']=c.guard.memory();h['remote']=c.git('ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture')
c.require(c.host_safe(h),'Outer/inner groups still live or unknown identity')
c.require(h['head']=='e780e6158ea5365adf5cde36dceaa8032a34fe9c' and h['master']==c.MASTER,'Refs changed')
c.require(h['head']+'\trefs/heads/codex/simplex-core-architecture' in h['remote'] and c.MASTER+'\trefs/heads/master' in h['remote'],'Remote refs changed')
c.require(h['boot_id']==outer['boot_id'],'Boot changed')
record=dict(all_passed=True,outer_identity=outer,host=h,scope='Separate after-return closure includes actual outer+all prior+new guard/child PGIDs AND SIDs; not in-process self-closure',sha256={str(p):c.sha(p) for p in [Q/'outer.py',Q/'outer-ready.json',Q/'outer-invocation.json',Q/'outer-outcome.json',Q/'release.json',RUN/'sealed.json',RUN/'admission.json',RUN/'posthost.json'] if p.exists()})
c.save(Q/'outer-closure.json',record)
a=c.rd(RUN/'audit.json') if (RUN/'audit.json').exists() else None
c.save(Q/'post-summary.json',dict(outer_outcome=outcome,audit_all_passed=None if a is None else a['all_passed'],pure_timeout=None if a is None else a['pure_timeout'],audit_error=None if a is None else a.get('error'),sha256={} if a is None else {str(RUN/'audit.json'):c.sha(RUN/'audit.json')},scope='Read saved audit; no auditor or numerical rerun'))
print(json.dumps(dict(outer_closed=True,groups=len(h['groups']),audit_all_passed=None if a is None else a['all_passed'],pure_timeout=None if a is None else a['pure_timeout'],error=None if a is None else a.get('error'),memory=h['memory'])))
