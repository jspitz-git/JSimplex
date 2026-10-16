"""One-shot offline canonical inventory. Does not create a phase seal or launch."""
from control import *
A=D.parent/'DIRECT-LU-POLICY-ADAPTER-PREPARATION'
validate_environment();validate_sources();require(rd(D/'offline-tests.json')['all_passed'],'Offline predicates')
require(not (D/'runs').exists(),'Unexpected attempted run')
maps=[]
for record in ['closure.json','publication.json']:
 old=rd(A/record)
 for n,h in old['sha256'].items():
  target=R/n
  if n=='diagnostics/simplex-core-architecture/STATUS.md':target=D/'STATUS.md.before-driver'
  if n=='docs/superpowers/plans/2026-10-11-simplex-core-architecture.md':target=D/'roadmap.md.before-driver'
  require(sha(target)==h,'Accepted candidate lineage drift '+n)
  if target!=R/n:maps.append(dict(record=str(A/record),original=n,sha256=h,preserved=str(target)))
require(len(maps)==4,'Prior maps')
save(D/'lineage-check.json',dict(all_passed=True,prior_maps=maps,master=MASTER,candidate_commit=ENTRY,canonical_runtime='runtime-inputs-complete.json',julia_executed=False))
files={str(p) for p in D.iterdir() if p.is_file()}|{str(p) for p in C.iterdir() if p.is_file()}|{str(p) for p in A.iterdir() if p.is_file()}
files|={str(R/'docs/superpowers'/kind/'2026-10-16-direct-lu-policy-adapters.md') for kind in ['plans','specs']}
files.add(str(D/'required-paths.json'));files.discard(str(D/'preparation-pins.json'))
paths=sorted(files);save(D/'required-paths.json',dict(paths=paths))
save(D/'preparation-pins.json',dict(scope='OFFLINE driver preparation, not phase/launch admission',sha256={n:sha(n) for n in paths}))
require(bindings(rd(D/'preparation-pins.json')),'Inventory drift')
print('Offline canonical preparation',len(paths),'pins; no phase seal/reservation/output')
