"""Exclusive stage admissions and at most one guarded attempt for GREEN/master."""
from common_reviewed import *
import subprocess
mode=sys.argv[1];stage=None if mode=='freeze-admission' else sys.argv[2]
assert sha(C)==EXPECTED and not absent()['matches']
if mode in ('freeze-admission','freeze-launch'):
 files=set(required(stage))|{str(H/'required-reviewed-paths.json')}
 if stage:
  accepted();assert sha(root(stage)/REL)==EXPECTED
  h=stage_files(stage);h.mkdir(exist_ok=True)
  files|={str(H/n) for n in ('admission-reviewed-pins.json','admission-accepted-review.md','admission-acceptance-reviewed.json')}
  files|={str(h/'stage-acceptance.json')};stage_accepted(stage)
  if stage=='master':
   assert read(H/'green/audit.json')['all_passed'] is True
   assert 'ACCEPTED' in (H/'green/review.md').read_text() and 'Unresolved findings: []' in (H/'green/review.md').read_text()
   files|={str(H/'green'/n) for n in ('audit.json','review.md','postcheck.json')}
 pins=H/'admission-reviewed-pins.json' if stage is None else stage_files(stage)/'pins.json'
 cmd=[sys.executable,str(G),'freeze',str(pins)]
 for p in (R,M):
  for d in ('src','test'):cmd+=['--tree',str(p/d)]
 for f in sorted(files):cmd+=['--file',f]
 subprocess.run(cmd,check=True);assert inventory_ok(read(pins),stage)
elif mode=='run':
 accepted();h=stage_files(stage);pins=h/'pins.json';assert inventory_ok(read(pins),stage)
 launch_accepted(stage)
 assert not out(stage).exists();dump(h/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(stage),pins_sha256=sha(pins)))
 inv=dict(command=[sys.executable,str(G),'run',str(pins),str(out(stage)),'--seconds','120','--',*command(stage)],started_ns=time.time_ns(),host=absent(),returncode=None)
 try:
  with (h/'guard-output.log').open('x') as log:
   result=subprocess.run(inv['command'],cwd=root(stage),stdout=log,stderr=subprocess.STDOUT);inv['returncode']=result.returncode
 except BaseException as e:inv['error']=repr(e)
 finally:
  inv['ended_ns']=time.time_ns();dump(h/'guard-invocation.json',inv)
 raise SystemExit(0 if type(inv['returncode']) is int and inv['returncode']==0 and 'error' not in inv else 1)
else:raise ValueError(mode)
