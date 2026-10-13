"""Exclusive S5-S offline preparation; no Julia invocation or old script execution."""
from common import *
import subprocess
prior=H.parent/'S5-R';q=H.parent/'S5-Q';checks={}
for name,key,count in [('evidence.json','sha256',199),('pins.json','sha256',194),('field-fix.json','sha256',4),('independent.json','sha256',6),('closure.json','sha256',24)]:
 d=read(prior/name);v=d[key];checks[name]=len(v)==count and all(sha(p)==x for p,x in v.items())
for name,count in [('evidence.json',19),('field-fix.json',4),('independent.json',8),('closure.json',14),('publication-check.json',6)]:
 d=read(prior/name);checks['gates_'+name]=len(d['checks'])==count and all(v is True for v in d['checks'].values()) and d['all_passed'] is True
for name,count in [('evidence.json',178),('independent.json',5),('closure.json',19)]:
 v=read(q/name)['sha256'];checks['Q_'+name]=len(v)==count and all(sha(prior/(Path(p).name+'.before-R') if p in (str(R/'diagnostics/simplex-core-architecture/STATUS.md'),str(R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md')) else p)==x for p,x in v.items())
assert all(checks.values()),checks
host=absent();assert not host['matches'];host['user_hashes']=read(prior/'host-before.json')['user_hashes'];assert all(sha(p)==x for p,x in host['user_hashes'].items())
host['refs']=subprocess.check_output(['git','rev-parse','HEAD','master'],text=True).splitlines();assert host['refs']==['5339da900d945c23f420ac0e2c60876f8622aa7b','35a6a9f4bb61e204b0c61ec9effe96cd9d2de3ab']
host['remote']=subprocess.check_output(['git','ls-remote','origin','refs/heads/master','refs/heads/codex/simplex-core-architecture'],text=True);assert all(x in host['remote'] for x in host['refs'])
assert not subprocess.check_output(['git','diff','master','--','src','test','.github']);dump(H/'host-before.json',host)
dump(H/'entry-checks.json',dict(checks=checks,all_passed=True))
work=dict(ftran=2,btran=2,factor=1,iterations=0,refactors=1,checkpoint=1,initial=1,other=1,correction=0,attempt=0,events=3,last='refactor_other',phase=1,history=0)
observations=dict(caught_type='str',sentinel_type='str',guard_exception_type='str',returned='bool',callbacks='int',stop_calls='int',throws='int',stage='int',start_ns='str',scalar='str',update='str',backend='str')
values=dict(caught_type='ErrorException',sentinel_type='ErrorException',guard_exception_type='ErrorException',returned=False,callbacks=4,stop_calls=2,throws=1,stage=4,scalar='Float64',update='pfi',backend='native')
dump(H/'schema.json',dict(checks=read(prior/'provenance.json')['predicate_names'],work=work,observations=observations,observation_values=values,candidate_sha256=EXPECTED))
dump(H/'command.json',dict(command=command()))
