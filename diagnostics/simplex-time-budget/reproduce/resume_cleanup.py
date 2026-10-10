"""Finish cleanup with counters after the preserved sampling stall."""
from pathlib import Path
import subprocess,sys,json
root=Path(__file__).resolve().parents[3]
raw=root/'.superpowers/time-budget'
for case,attempt in (('cleanup-dual',2),('cleanup-primal',1)):
 out=raw/f'{case}-{attempt}'
 (raw/'current.json').write_text(json.dumps({'case':case,'output':str(out),'sampling':False}))
 command=[sys.executable,str(Path(__file__).with_name('run.py')),str(out),'1800',str(Path(__file__).with_name('measure_counted.jl')),case,str(out)]
 result=subprocess.run(command,cwd=root)
 if result.returncode:sys.exit(result.returncode)
out=raw/'metadata-1'
result=subprocess.run([sys.executable,str(Path(__file__).with_name('run.py')),str(out),'300',str(Path(__file__).with_name('metadata.jl')),str(out/'handoffs.toml')],cwd=root)
if result.returncode:sys.exit(result.returncode)
(raw/'complete.json').write_text(json.dumps({'complete':True,'cleanup_sampling':'unavailable; cleanup-dual-1 sampling stalled; preserved separately'}))
