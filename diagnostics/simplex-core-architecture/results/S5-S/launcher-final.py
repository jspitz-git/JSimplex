"""Exclusive S5-S freeze/admission and ONE guarded exact-candidate attempt."""
from common_final import *
import subprocess,sys
mode,=sys.argv[1:]
B.mkdir(parents=True,exist_ok=True)
assert sha(C)==EXPECTED
assert not absent()['matches']
if mode in ('freeze-admission','freeze-launch'):
 files=set(required())|{str(H/'required-final-paths.json')}
 if mode=='freeze-launch':
  accepted();assert inventory_ok(read(H/'admission-final-pins.json'))
  files|={str(H/n) for n in ('admission-final-pins.json','prelaunch-accepted-review.md','prelaunch-acceptance.json')}
 pins=H/('admission-final-pins.json' if mode=='freeze-admission' else 'launch-pins.json')
 cmd=[sys.executable,str(G),'freeze',str(pins),'--tree',str(R/'src'),'--tree',str(R/'test')]
 for p in sorted(files):cmd+=['--file',p]
 # No MPS input is admitted; the candidate's only model is its frozen construction.
 subprocess.run(cmd,check=True)
 assert inventory_ok(read(pins))
elif mode=='run':
 accepted();pins=H/'launch-pins.json';assert inventory_ok(read(pins))
 inv=read(pins)['inventory'];assert {str(H/n) for n in ('admission-final-pins.json','prelaunch-accepted-review.md','prelaunch-acceptance.json')}.issubset(inv)
 binding=read(H/'launch-binding.json');assert binding['accepted'] is True
 assert {str(pins),str(H/'prelaunch-acceptance.json'),str(H/'prelaunch-accepted-review.md'),str(H/'launcher-final.py')}.issubset(binding['sha256'])
 assert all(sha(p)==v for p,v in binding['sha256'].items())
 assert not O.exists();dump(H/'attempt-reserved.json',dict(time_ns=time.time_ns(),command=command(),pins_sha256=sha(pins)))
 invocation=dict(command=[sys.executable,str(G),'run',str(pins),str(O),'--seconds','120','--',*command()],started_ns=time.time_ns(),host=absent(),returncode=None)
 try:
  with (H/'guard-output.log').open('x') as log:
   result=subprocess.run(invocation['command'],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   invocation['returncode']=result.returncode
 except BaseException as error:
  invocation['error']=repr(error)
 finally:
  invocation['ended_ns']=time.time_ns()
  dump(H/'guard-invocation.json',invocation)
 raise SystemExit(0 if invocation['returncode']==0 and 'error' not in invocation else 1)
else:raise ValueError(mode)
