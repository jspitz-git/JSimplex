"""One-shot restart recovery record and concrete offline configuration; no Julia."""
from common import *
from control import config
h=host();verify_host(h)
z=rd(Q/'source-check.json');require(bindings(z),'Saved source bindings changed')
require(not Path(config('integration')['stage']).exists() and not (Q/'runs').exists(),'Unexpected stage/run')
save(Q/'restart-recovery.json',dict(host=h,same_linux_boot=True,saved_bindings=len(z['sha256']),all_bindings_match=True,no_stage_or_run=True,reported_by_user='Computer restarted again',cause='Unknown; Linux boot ID unchanged; no Windows reboot/cause inference'))
save(Q/'config-preview.json',config('integration'))
P=Q.parent/'NATIVE-PIVOT-INTEGRATION-PREPARATION';maps=[]
for record in ['closure.json','publication.json']:
 z=rd(P/record)
 for name,preserved in [(STATUS,Q/'STATUS.md.before-driver'),(ROAD,Q/'roadmap.md.before-driver')]:
  key=str(name.relative_to(R));require(z['sha256'][key]==sha(preserved),'Preimage mismatch')
  maps.append(dict(record=str((P/record).relative_to(R)),pointer=['sha256',key],preserved_path=str(preserved.relative_to(R)),sha256=sha(preserved)))
save(Q/'continuation-mappings.json',dict(mappings=maps,scope='Only current predecessor continuation bindings; all older mappings unchanged'))
print(dict(recovery=True,groups=len(h['groups']),bindings=len(rd(Q/'source-check.json')['sha256']),mappings=len(maps)))
