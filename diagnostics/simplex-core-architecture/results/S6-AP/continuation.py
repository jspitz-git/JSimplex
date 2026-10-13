"""Exclusive continuation update, gated by final independent acceptance."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
assert all(t in (H/'finalreview.md').read_text() for t in ['Verdict: ACCEPTED','Unresolved findings: []'])
for x in json.loads((H/'before-texts.json').read_text())['mappings']:assert Path(x['original']).read_bytes()==Path(x['preserved']).read_bytes()
text='''S6-AP SOURCE/EVIDENCE ONLY provenance completed with an unresolved historical
failure. User log88807bytes/817lines SHA22da06e3955a94ffa25fc1f0a0630e933c124aa4a137a25e159b57877030e115
records inconclusive original-objective certificate at255115 and original-LP retry
Harris cutoff failure at aggregate256164/14814.7718616s. User subsequently supplied
test.mps C:\\tmp native-reader HH/native320 dual legacy steepest_edge Inf/1000000/
relax_integrality invocation, approximately01:00today2026-10-13/AMD/8BLASthreads.
These are user-reported, not a runtime configuration capture. Commit unknown;
no exact source/default-options/inputhash/witness linkage. Current Windows script
names runtime.mps; current Ctmp/test.mps and referenced capture script absent.
Linux test model hashf60dd96b matches S0/F11 dimensions, not a historical Windows
byte identity. Current-source messages interpreted conditionally; Harris guard
(!exhausted || !eligible_at_cutoff) does not prove all coefficients below cutoff.
No rejecting certificate subpredicate/backend cause/CI reproduction/repair claim.
293.240GiB is cumulative allocation traffic, not peak/live memory or speedup.
Entry15/1947pins, provenance17/21; author original3of4/false literal text gate
PRESERVED plus separate4PASS supplement, full1970 hashes matched. Fresh independent
gpt6astra initial13 checks/FULLnamedpins1977 physical files; user clarification
separate9checks8bindings, preserved initial report/plan/review, final bounded review
accepted/no unresolved C/I/M/no unnecessary NEW production work/memory.
No Julia/model parse/numerics/actualtest/production/env/cache/CI change; masterd02416c.
AC current closure33/exact36 and AP original current continuation hashes map ONLY
AP.before-AP; AP initial report/plan hashes map ONLY AP.before-user-reply when exact
hash matches. All earlier mappings/frozen failures remain unchanged. Next S6-AQ
2026-10-13-test-mps-original-run-linkage.md is conditional on genuinely NEW original
source/runtime/inputhash or saved certificate input; do not repeat answered script
question/search or infer commit from time. No new numerical allowance. All broader
gates/rejections/fullsuite/x64/CIoff/HHdisabled/deferred cleanup omission unchanged.
'''
p=D/'STATUS.md';s=p.read_text();old='**Current continuation: S5-AC cleanup omission deferred after independent design review; after separate closure/publication follow `docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md` (S6-AP, source/evidence only).**';assert old in s
s=s.replace(old,'**Current continuation: S6-AP provenance reconciled, historical failure unresolved. S6-AQ accepts only genuinely new original source/witness evidence under `docs/superpowers/plans/2026-10-13-test-mps-original-run-linkage.md`; no numerical allowance or repeated search.**\n\n'+text,1);p.write_text(s)
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';p.write_text(p.read_text()+'\n## S6-AP provenance and conditional S6-AQ linkage (2026-10-13)\n\n'+text)
p=D/'S6-TEST-MPS-FAILURE-PROVENANCE-REVIEW.md'
with p.open('x') as f:f.write('''# S6-AP independent review

Initial review and bounded review of the subsequent user clarification accepted
this source/evidence-only provenance record. See results/S6-AP/review.md,
finalreview.md, reviewer-check.json and reviewer-user-check.json.
No unresolved Critical/Important/Minor findings; no unnecessary new production
computational work or memory cost. No benchmark or numerical execution was needed.

The original author independent.json has three true checks and one false literal
plan-text check, exit1; it remains unchanged. independent-supplement.json adds four
passing checks against the actual prohibition without changing the initial plan.
The subsequent human clarification is separate user-linkage.json evidence, with
initial report/plan/review bytes preserved before updating provenance. The earlier
reviewer missing-source selector is recorded in reviewer-check.json; no Julia ran.

The failure remains unresolved. The confirmed script/settings/hardware statement
is user provenance; the original source commit/default options, input hash and
point/basis/witness are not captured. No blanket Harris-cutoff or backend-cause
claim is accepted. No existing safeguard or certificate contract changed.
''')
print('Continuation and companion written after final acceptance.')
