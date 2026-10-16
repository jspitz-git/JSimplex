"""One separate OFFLINE documentation correction; preserve original rejected evidence."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;R=D.parents[3]
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,z):
 with p.open('x') as f:json.dump(z,f,indent=2);f.write('\n')
def write(p,b):
 with p.open('xb') as f:f.write(b)
def require(x,m):
 if not x:raise RuntimeError(m)
old=rd(D/'preparation-pins.json');rejected=rd(D/'review.json');require(rejected['accepted'] is False and len(rejected['findings'])==1,'Initial finding')
work=D/'WORK-AND-ADMISSION.md';before=work.read_text();require('Per public case seven input snapshots:' in before and 'nine buffers; seven copied objects.' in before,'RED wrong ledger counts absent')
protected=[D/'native_pivot_integration_tests.jl',D/'observer-seams.json',D/'overlay-manifest.json',D/'candidate/test/runtests.jl',D/'source-check.json',D/'author-check.json',D/'review.json',D/'review.md',D/'reviewer-checks.json',D/'preparation-pins.json']
pre={str(p.relative_to(R)):sha(p) for p in protected}
write(D/'WORK-AND-ADMISSION.md.before-review',work.read_bytes())
work.write_text(before.replace('Per public case seven input snapshots:','Per public case six input snapshots:').replace('nine buffers; seven copied objects.','eight buffers; six copied objects.'))
cont=D/'continuation-text.md';write(D/'continuation-text.md.before-review',cont.read_bytes());require(cont.read_text().count('review.json/review.md')==1,'Continuation review anchor')
cont.write_text(cont.read_text().replace('review.json/review.md','review-final.json/review-final.md'))
# Original unexecuted finalizer draft is preserved; only final review/manifest names change.
f=(D/'finalize.py').read_text();require(f.count("D/'review.json'")==1 and f.count("D/'preparation-pins.json'")==3,'Finalizer anchors')
f=f.replace("D/'review.json'","D/'review-final.json'").replace("D/'preparation-pins.json'","D/'preparation-pins-reviewed.json'")
write(D/'finalize-final.py',f.encode())
checks=dict(initial_rejected=rejected['accepted'] is False,red_wrong_counts='seven input snapshots' in before and 'nine buffers; seven copied' in before,green_correct_counts='six input snapshots' in work.read_text() and 'eight buffers; six copied' in work.read_text(),entries_unchanged='23 entries' in work.read_text() and '184 copied entries' in work.read_text(),exact_work_inverse=work.read_text().replace('Per public case six input snapshots:','Per public case seven input snapshots:').replace('eight buffers; six copied objects.','nine buffers; seven copied objects.')==before,protected_unchanged=all(sha(R/n)==h for n,h in pre.items()),finalizer_name_inverse=f.replace("D/'review-final.json'","D/'review.json'").replace("D/'preparation-pins-reviewed.json'","D/'preparation-pins.json'")==(D/'finalize.py').read_text())
save(D/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,protected_sha256=pre,sha256={str(p.relative_to(R)):sha(p) for p in [D/'review-fix.py',work,D/'WORK-AND-ADMISSION.md.before-review',cont,D/'continuation-text.md.before-review',D/'finalize.py',D/'finalize-final.py']},scope='Documentation count correction only; source/test/observer/evidence unchanged; old review remains rejected.'))
require(all(checks.values()),'Fix failed: preserve')
mapping={'record':str((D/'preparation-pins.json').relative_to(R)),'pointer':['sha256',str(work.relative_to(R))],'sha256':old['sha256'][str(work.relative_to(R))],'preserved_path':str((D/'WORK-AND-ADMISSION.md.before-review').relative_to(R))}
require(mapping['sha256']==sha(D/'WORK-AND-ADMISSION.md.before-review'),'Original manifest mapping');save(D/'review-mapping.json',mapping)
files={R/n for n in old['sha256'] if n!=str(work.relative_to(R))}|{D/'WORK-AND-ADMISSION.md.before-review'}
files|={p for p in D.rglob('*') if p.is_file()}
for n,h in old['sha256'].items():require(sha(D/'WORK-AND-ADMISSION.md.before-review' if n==str(work.relative_to(R)) else R/n)==h,'Original833 changed '+n)
save(D/'preparation-pins-reviewed.json',dict(sha256={str(p.relative_to(R)):sha(p) for p in sorted(files)},scope='Fresh offline corrected preparation. Original833 binds preserved before-review ledger for its exact digest; no retroactive old pin edits.'))
print(dict(checks=len(checks),pins=len(files),old_preserved=len(old['sha256'])))
