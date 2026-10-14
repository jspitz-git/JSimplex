"""Separate post-run host closure, before continuation changes; no numerical work."""
from pathlib import Path
import json,sys
D=Path(__file__).resolve().parent;A=D.parent/'DIRECT-LU-ADMISSION'
sys.path.insert(0,str(A))
from control_reviewed import host,req,save
previous=json.loads((A/'green-posthost.json').read_text())
current=host(previous['groups'])
save(D/'final-host.json',current)
req(current['matches']==[] and len(current['groups'])==200,'Prior group/session or Julia remains')
req(all(current[k]==previous[k] for k in ('head','master','boot_id')),'Host refs/boot changed')
print(json.dumps(dict(groups=len(current['groups']),matches=current['matches'],head=current['head'],master=current['master'],boot_id=current['boot_id'])))
