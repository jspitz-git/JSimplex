"""One new offline preparation inventory; never seals a numerical stage."""
from control import *
from evidence import validate_predecessor
import guard
extra=validate_predecessor('probe');A=D.parent/'DIRECT-LU-COST-PREPARATION'
old=rd(A/'cost1-launch-pins.json');req(guard.pins_match(old),'Frozen inputs drift')
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];req(all(sha(R/n)==h for n,h in base.items()),'Production drift')
report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-BACKEND-PREPARATION.md'
required=sorted({str(p) for p in D.iterdir() if p.is_file()}|{str(report)}|{str(p) for p in extra}|set(rd(D/'source-check.json')['sha256']))
save(D/'required.json',required)
files=sorted(set(old['files'])|set(required)|{str(D/'required.json')}|{str(R/n) for n in base})
pins=dict(files=files,trees=old['trees'],inventory=guard.inventory(files,old['trees']),inputs=[],created=time.time(),scope='Offline reference backend preparation, NOT numerical stage admission')
save(D/'preparation-pins.json',pins)
print(json.dumps(dict(required=len(required),files=len(files),inventory=len(pins['inventory']))))
