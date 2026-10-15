"""One-shot new offline inventory, no numerical stage seal or reservation."""
from control import *
from evidence import validate_predecessor
import guard
extra=validate_predecessor('cost1');A=D.parent/'DIRECT-LU-GREEN-ADMISSION'
old=rd(A/'green-launch-pins.json');req(guard.pins_match(old),'Old qualified input drift')
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'];req(all(sha(R/n)==h for n,h in base.items()),'Production drift')
report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-COST-PREPARATION.md'
required=sorted({str(p) for p in D.iterdir() if p.is_file()}|{str(report)}|{str(p) for p in extra})
save(D/'required.json',required)
files=sorted(set(old['files'])|set(required)|{str(D/'required.json')}|{str(R/n) for n in base})
trees=old['trees'];pins=dict(files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[],created=time.time(),scope='Offline Task3 preparation, not stage admission')
save(D/'preparation-pins.json',pins)
print(json.dumps(dict(required=len(required),files=len(files),inventory=len(pins['inventory']))))
