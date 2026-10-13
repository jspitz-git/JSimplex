"""One offline S5-O admission binding amendment; preserve original813 and source."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent
common=(H/'common.py').read_text()
old="def accepted(name):\n a=read(H/name);assert a['accepted'] is True and a['unresolved_findings']==[]\n assert all(sha(p)==v for p,v in a['reviewed_sha256'].items())\n return a\n"
new="""def accepted(name,required):
 a=read(H/name);assert a['accepted'] is True and a['unresolved_findings']==[]
 bindings=a['reviewed_sha256']
 assert isinstance(bindings,dict) and bindings
 assert {str(Path(p)) for p in required}.issubset(bindings)
 assert all(isinstance(v,str) and len(v)==64 and sha(p)==v for p,v in bindings.items())
 return a
"""
assert common.count(old)==1
with (H/'common_reviewed.py').open('x') as f:f.write(common.replace(old,new))
s=(H/'launcher.py').read_text().replace('from common import *','from common_reviewed import *')
s=s.replace("B.mkdir(parents=True,exist_ok=True);pins=B/(label+'-pins.json');s=read(H/'schema.json')", """B.mkdir(parents=True,exist_ok=True)
ADMISSION=B/'admission-reviewed-pins.json'
pins=ADMISSION if label=='admission' else B/(label+'-pins.json');s=read(H/'schema.json')
PRE_REQUIRED=[ADMISSION,H/'prelaunch-final-review.md',H/'driver.jl',H/'launcher-reviewed.py',H/'common_reviewed.py',H/'common.py',H/'audit.py',H/'postcheck.py',H/'schema.json',H/'expected.toml',H/'insertions.toml']
GREEN_REQUIRED=[H/'green-review.md',H/'green-1-audit.json',H/'green-1-postcheck.json',B/'green-1/pins.json',B/'green-1/process.json',B/'green-1/raw/report.toml',B/'green-1/raw/case.toml']""")
s=s.replace("files.add(Path('/home", "files.add(B/'admission-pins.json')\n files.add(Path('/home")
s=s.replace("accepted('prelaunch-acceptance.json')", "accepted('prelaunch-acceptance.json',PRE_REQUIRED)")
s=s.replace("accepted('green-acceptance.json')", "accepted('green-acceptance.json',GREEN_REQUIRED)")
s=s.replace("read(B/'admission-pins.json')",'read(ADMISSION)').replace("files.add(B/'admission-pins.json')\n  if", "files.add(ADMISSION)\n  if")
s=s.replace("accepted(label+'-launch-binding.json')", "accepted(label+'-launch-binding.json',[pins,H/'prelaunch-acceptance.json',H/'prelaunch-final-review.md',H/'launcher-reviewed.py']+([H/'green-acceptance.json',H/'green-review.md'] if label=='master-1' else []))")
with (H/'launcher-reviewed.py').open('x') as f:f.write(s)
print('New reviewed launcher/common written; original813 files untouched. No Julia.')
