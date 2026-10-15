"""Separate fresh post-run full group/session scan before continuation changes."""
from pathlib import Path
import json,sys
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-GREEN-ADMISSION'
sys.path.insert(0,str(A));from control import host,req,save
previous=json.loads((A/'green-posthost.json').read_text());current=host(previous['groups'])
save(D/'final-host.json',current)
req(current['matches']==[] and set(current['groups'])==set(previous['groups']) and len(current['groups'])==202,'Group/session/Julia closure failed')
req(all(current[k]==previous[k] for k in ('head','master','boot_id')),'Host refs/boot changed')
print(json.dumps(dict(groups=len(current['groups']),matches=current['matches'],head=current['head'],master=current['master'],boot=current['boot_id'])))
