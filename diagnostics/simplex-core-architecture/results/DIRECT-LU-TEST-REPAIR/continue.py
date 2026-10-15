"""Update continuation only after offline acceptance, preserving exact old bytes."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
review=json.loads((D/'review.json').read_text())
if review.get('accepted') is not True or review.get('findings')!=[]:raise SystemExit('Review has not accepted repair')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
if status.read_bytes()!=(D/'STATUS.md.before-repair').read_bytes() or roadmap.read_bytes()!=(D/'roadmap.md.before-repair').read_bytes():raise SystemExit('Continuation moved')
old='''Next concrete work: a separate offline test-only repair preserving the original
fixtures/checks: copy the CSC and scale private nzval while retaining its stored
pattern for backend refactor. Bind/check that pattern contract explicitly and
independently review any driver binding-access warning cleanup. Never rewrite the
frozen candidate/tests/driver, outputs or admissions in place. A subsequent short
attempt needs a separate exact reviewed admission/output reservation; standing
user permission is sufficient. Tasks3–4 remain gated on accepted correctness.'''
new='''Separate OFFLINE test repair is independently accepted; see
DIRECT-LU-TEST-REPAIR.md and results/DIRECT-LU-TEST-REPAIR/review.md/json.
Owned CSC copy + nzval scaling preserves stored zeros; five checks on each of
six native nonempty fixtures add30 assertions (exports130, total19,557).
Driver latest-world closures move binding lookup inside invokelatest. Exact
whole-file inverses preserve every other test/driver byte.17text checks passed,
136frozen artifacts and514baseline files unchanged. No Julia was executed;
original failed GREEN remains failed, and runtime correctness is unqualified.
No production work/memory change; cold test copy/scans explicitly accounted.

Next concrete work: NEW GREEN-only offline admission/control/overlay preparation
with corrected files/counts, unchanged focused slices and fresh output paths.
Reuse immutable accepted RED evidence; do not rerun RED or old failed GREEN.
Then fresh host/seal and independent exact-run admission before one <=90s GREEN.
Standing permission covers short runs; no new permission question is needed.
Tasks3–4 remain gated on accepted full correctness. Original artifacts frozen.
Previous correctness review/closure/publication current STATUS/roadmap bindings
map ONLY to DIRECT-LU-TEST-REPAIR/STATUS.md.before-repair and roadmap.md.before-repair
(six exact mappings); all older mappings remain unchanged.'''
s=status.read_text()
if s.count(old)!=1:raise SystemExit('Unique next-step block missing')
status.write_text(s.replace(old,new))
with roadmap.open('a') as f:f.write('''
## 2026-10-15: separate direct-LU test repair accepted offline

See DIRECT-LU-TEST-REPAIR.md and results/DIRECT-LU-TEST-REPAIR/review.md/json.
The native export-ownership test now privately copies CSC and scales nzval,
preserving explicit stored zeros for the existing source-backend refactor.
Five checks times six cases add30 prospective assertions: exports130, total19,557.
All original oracles/fixtures/candidate source remain byte-identical by exact
inverse; separate driver changes count and latest-world binding access only.
17offline checks passed; fresh independent review accepts this preparation.
No Julia or new numerical attempt; original RED accepted, failed GREEN unchanged.
Production work/memory unchanged; O(n+stored-nnz) cold copy/check work charged.

Next prepare NEW GREEN-only admission/overlay/controls/output reservation paths,
copying corrected files and unchanged focused slices. Accepted RED is immutable
predecessor evidence, never rerun. Fresh host/seal and exact independent admission
are required before one <=90s process under existing guards/standing permission.
Tasks3–4 remain gated; no runtime acceptance, performance claim or promotion.
The six correctness review/closure/publication current continuation bindings map
ONLY to this repair's STATUS.md.before-repair and roadmap.md.before-repair;
all older artifacts/mappings unchanged. Master6f68e24/CIoff/HHdisabled/
automationpaused; broader plan remains open.
''')
ledger=R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md'
with ledger.open('a') as f:f.write('''
- Correctness result review accepted diagnostic failure (62checks), not GREEN.
  New separate offline test repair: owned CSC/nzval, five checks*6native cases;
  exports130/total19557 prospective. Driver latest-world binding cleanup separate.
 17source checksPASS, independent offline review accepted; noJulia. Original
 production/fixtures/oldraw/scripts frozen. Next NEW GREEN-only admission with
 immutableRED reuse, freshhost/seal/review, one90s limit; Tasks3–4 still gated.
''')
print('Continuation updated after independent offline acceptance')
