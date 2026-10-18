"""Process-local pinned PATH entry. Does not relax any original gate."""
from pathlib import Path
import os,json,subprocess,sys
Q=Path(__file__).resolve().parent
E=Q.parent/'DIRECT-BG-BLOCK-COST-PREPARATION'
if len(sys.argv)!=2 or sys.argv[1] not in ('seal','launch'):
 raise SystemExit('Expected explicit seal or launch')
expected=json.loads((E/'environment.json').read_text())
env=os.environ.copy()
for k,v in expected.items():
 if k!='PATH' and env.get(k)!=v:raise RuntimeError('Non-PATH environment drift: '+k)
env['PATH']=expected['PATH']
cmd=['/usr/bin/python3','-B',str(E/(sys.argv[1]+'.py')),'cost1-300']
with (Q/(sys.argv[1]+'-scoped.log')).open('x') as log:
 result=subprocess.run(cmd,env=env,stdout=log,stderr=subprocess.STDOUT)
raise SystemExit(result.returncode)
