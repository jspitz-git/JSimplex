"""One-shot new amendment inventory; old pins and all old scripts remain frozen."""
from control_reviewed import *
import guard
old=rd(D/'preparation-pins.json')
req(guard.pins_match(old),'Initial inventory changed')
paths={str(p) for p in D.rglob('*') if p.is_file()}
required=sorted(set(rd(D/'required.json'))|paths)
save(D/'required-reviewed.json',required)
files=sorted(set(old['files'])|paths|{str(D/'required-reviewed.json')})
pins=dict(files=files,trees=old['trees'],inventory=guard.inventory(files,old['trees']),inputs=[],created=time.time(),scope='Revised offline preparation; not stage admission')
save(D/'preparation-pins-reviewed.json',pins)
print(json.dumps(dict(pins=len(pins['inventory']),required=len(required))))
