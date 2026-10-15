"""Fresh offline inventory, no old execution or historical launch-pin rewriting."""
from control import *
import guard
A=D.parent/'DIRECT-LU-ADMISSION';P=D.parent/'DIRECT-LU-TEST-REPAIR'
old=rd(A/'green-launch-pins.json')
req(guard.pins_match(old),'Historical launch inputs changed')
base=rd(D.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256']
req(len(base)==514 and all(sha(R/n)==h for n,h in base.items()),'Baseline changed')
report=R/'diagnostics/simplex-core-architecture/DIRECT-LU-GREEN-ADMISSION.md'
frozen=rd(P/'frozen-inputs.json')['sha256'];req(all(sha(R/n)==h for n,h in frozen.items()),'Old artifacts changed')
authored=[p for p in D.rglob('*') if p.is_file()]
deps=[p for p in P.iterdir() if p.is_file()]+[R/n for n in frozen]+[report]
required=sorted(set(str(p) for p in authored+deps));save(D/'required.json',required)
files=sorted(set(old['files'])|set(required)|{str(D/'required.json')}|{str(R/n) for n in base})
trees=sorted(set(old['trees'])|{rd(D/'staging.json')['root']})
pins=dict(files=files,trees=trees,inventory=guard.inventory(files,trees),inputs=[],created=time.time(),scope='Fresh offline corrected GREEN preparation; no stage admission')
save(D/'preparation-pins.json',pins)
print(json.dumps(dict(files=len(files),inventory=len(pins['inventory']),required=len(required),trees=len(trees))))
