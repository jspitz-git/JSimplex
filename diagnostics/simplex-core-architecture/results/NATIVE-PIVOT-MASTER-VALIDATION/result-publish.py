"""Publish this independent result acceptance after rechecking all explicit bindings."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;D=E.parent/'NATIVE-PIVOT-MASTER-READINESS';R=D.parents[3];A=D/'runs/master300'
def rd(p):return json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
s=rd(A/'sealed.json');check=rd(E/'result-checks.json');extra=rd(E/'result-final-checks.json')
assert check['all_passed'] and extra['all_passed'] and check['check_count']==53708 and extra['exact_working_git_blob_checks']==3533
bindings={}
for n,v in s['inventory'].items():
 assert str(Path(n).resolve(strict=True))==v['resolved'] and sha(n)==v['sha256'],n
 bindings[n]=v['sha256']
files={p for root in [D,E] for p in root.rglob('*') if p.is_file() and p!=E/'result-review.json'}
files.add(R/'docs/superpowers/plans/2026-10-16-native-pivot-production-integration.md')
for p in files:bindings[str(p.relative_to(R))]=sha(p)
evidence={str(p.relative_to(R)):sha(p) for p in [E/'result-check.py',E/'result-checks.json',E/'result-host.json',E/'result-final-check.py',E/'result-final-checks.json',E/'result-publish.py']}
assert all(str(p.relative_to(R)) in bindings for p in A.rglob('*') if p.is_file())
record=dict(scope='actual-master result',phase='master300',accepted=True,findings=[],production_commit=check['master'],diagnostic_head=check['diagnostic_head'],pins_sha256=sha(A/'sealed.json'),launch_pins_sha256=sha(A/'launch-pins.json'),sha256=bindings,evidence_sha256=evidence,verification=dict(independent_predicates=53708,additional_exact_git_blobs=3533,sealed_inventory_entries=4926,launch_inventory_entries=4929,exact_admission_entries=4927,attempt_files=len(check['attempt_files']),assertions=6956,resource_samples=124,full_inventory_resolved_paths_checked=True),work_memory_assessment='No unnecessary new production work or retained-memory cost found; byte-identical accepted source, constant intent/private controls only; previous sparse96 +15 U entries/+48 reported numeric bytes retained, no universal speedup or fresh benchmark.',limitations=['Focused permanent tests only; not full suite or complete native work budget','No new instrumentation or benchmark; prior work/cost evidence reused','Inaccessible system executable links remain a visibility limit','Separate PASS closure, ordinary publication and remote/source verification remain required'],review='diagnostics/simplex-core-architecture/results/NATIVE-PIVOT-MASTER-VALIDATION/result-review.md')
with (E/'result-review.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print('Accepted actual-master result;',len(bindings),'SHA bindings;',len(evidence),'supplementary evidence bindings;',len(check['attempt_files']),'complete attempt files')
