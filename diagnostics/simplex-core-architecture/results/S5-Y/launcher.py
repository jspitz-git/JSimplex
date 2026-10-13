"""One S5-Y attempt; no retry. Imports only new local Python support."""
from common import *
mode=sys.argv[1]
assert sha(C)==EXPECTED and refs()==REFS and not absent()['matches']
if mode in ('freeze-admission','freeze-launch'):
 files=set(required())|{str(H/'required-paths.json')}
 if mode=='freeze-launch':
  assert accepted();files|={str(H/n) for n in ('acceptance.json','admission-review.md','admission-pins.json')}
 pins=H/('admission-pins.json' if mode=='freeze-admission' else 'pins.json')
 cmd=[sys.executable,str(G),'freeze',str(pins)]
 for t in sorted(TREES):cmd+=['--tree',t]
 for f in sorted(files):cmd+=['--file',f]
 subprocess.run(cmd,check=True);assert inventory_ok(read(pins))
elif mode=='run':
 assert inventory_ok(read(H/'pins.json')) and launch_ok() and not B.exists()
 dump(H/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(),output=str(B),pins_sha256=sha(H/'pins.json'),launch_binding_sha256=sha(H/'launch-binding.json')))
 inv=invoke(guard_command(),H/'guard-output.log',H/'guard-invocation.json',R,absent())
 raise SystemExit(0 if type(inv['returncode']) is int and inv['returncode']==0 and 'error' not in inv else 1)
else:raise ValueError(mode)
