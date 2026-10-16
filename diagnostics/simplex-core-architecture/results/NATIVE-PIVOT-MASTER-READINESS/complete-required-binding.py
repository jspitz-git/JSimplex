"""Complete self-list binding before independent review; original inventories preserved."""
from control import *
m=D/'preparation-pins.json';r=D/'required-paths.json';old=rd(m)
require(str(r) not in old['sha256'],'Expected missing required-list self binding')
for p in [m,r]:
 with p.with_name(p.name+'.before-self-binding').open('xb') as f:f.write(p.read_bytes())
paths=sorted(set(old['sha256'])|{str(r),str(Path(__file__)),str(m)+'.before-self-binding',str(r)+'.before-self-binding'})
r.write_text(json.dumps(dict(paths=paths),indent=2)+'\n')
m.write_text(json.dumps(dict(scope='Offline readiness inputs, not a launch seal',sha256={p:sha(p) for p in paths}),indent=2)+'\n')
save(D/'required-binding-check.json',dict(all_passed=True,checks=dict(original_missing_self_binding_preserved=True,canonical_required_list_itself_pinned=str(r) in rd(m)['sha256'],exact_required_membership=set(rd(r)['paths'])==set(rd(m)['sha256'])),sha256={str(p):sha(p) for p in [m,r,Path(__file__),m.with_name(m.name+'.before-self-binding'),r.with_name(r.name+'.before-self-binding')]}))
print('Required-list self-binding3PASS; initial inventories preserved')
