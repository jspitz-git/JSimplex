"""Exclusive S5-S freeze/admission and ONE guarded exact-candidate attempt."""
from common import *
import subprocess,sys
mode,=sys.argv[1:]
B.mkdir(parents=True,exist_ok=True)
assert sha(C)==EXPECTED
assert not absent()['matches']
if mode in ('freeze-admission','freeze-launch'):
 files=set(required())|{str(H/'required-paths.json')}
 if mode=='freeze-launch':
  accepted();assert inventory_ok(read(H/'admission-pins.json'))
  files|={str(H/n) for n in ('admission-pins.json','prelaunch-review.md','prelaunch-acceptance.json')}
 pins=H/('admission-pins.json' if mode=='freeze-admission' else 'launch-pins.json')
 cmd=[sys.executable,str(G),'freeze',str(pins),'--tree',str(R/'src'),'--tree',str(R/'test')]
 for p in sorted(files):cmd+=['--file',p]
 # No MPS input is admitted; the candidate's only model is its frozen construction.
 subprocess.run(cmd,check=True)
 assert inventory_ok(read(pins))
elif mode=='run':
 accepted();pins=H/'launch-pins.json';assert inventory_ok(read(pins))
 inv=read(pins)['inventory'];assert {str(H/n) for n in ('admission-pins.json','prelaunch-review.md','prelaunch-acceptance.json')}.issubset(inv)
 binding=read(H/'launch-binding.json');assert binding['accepted'] is True
 assert {str(pins),str(H/'prelaunch-acceptance.json'),str(H/'prelaunch-review.md'),str(H/'launcher.py')}.issubset(binding['sha256'])
 assert all(sha(p)==v for p,v in binding['sha256'].items())
 assert not O.exists();dump(H/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(),pins_sha256=sha(pins)))
 raise SystemExit(subprocess.call([sys.executable,str(G),'run',str(pins),str(O),'--seconds','120','--',*command()],cwd=R))
else:raise ValueError(mode)
