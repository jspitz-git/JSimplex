from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parents[3]
raw=root/'.superpowers/time-budget'
for case in ('medium-dual','medium-primal','cleanup-dual','cleanup-primal'):
 out=raw/(case+'-1')
 (raw/'current.json').write_text(json.dumps({'case':case,'output':str(out)}))
 command=[sys.executable,str(Path(__file__).with_name('run.py')),str(out),'1800',str(Path(__file__).with_name('measure.jl')),case,str(out)]
 result=subprocess.run(command,cwd=root)
 if result.returncode:sys.exit(result.returncode)
(raw/'complete.json').write_text(json.dumps({'complete':True}))
