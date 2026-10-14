from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-U'
for x in json.loads((D/'continuation-map.json').read_text())['old_bindings']:
 if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256']:raise SystemExit('Continuation drift')
b='''MA-U OFFLINE candidate/test preparation completed for MA-T Task1. Exact original
candidate inverse: one Bool helper plus one final eligibility expression only;
all12MA product sites/arithmetic/fallback/storage/n16 rules unchanged. Five original
reference/test/fixture/instrumentation/license copies byte-identical. Source19checks
34bindings; fresh entry15checks/source514/protected6/full166groups ANDsessions/noJulia.
New unexecuted tests:270predicate +25transition +optional1no-scope records;840whole
cases/844backend entries per original-new-instrumented side,2532total plus840setups
including4PFI constructors/copies. Source counts are not runtime/allocation proof.
One author text correction preserved before tests and original source-red mapping;
see MA-ROUNDING-GUARD-PREPARATION.md and MA-U/review.md/json. No Julia, numerical
measurement, driver/launcher or production edit. Candidate remains UNQUALIFIED.
Next MA-V prepares its own immutable driver/admission and independent review before
any short run; exactcalls/load/world-age/raw/anti-hoisting gates still required.
No MA-V launch from this step. Planned2x90seconds/180total, one attempt, standing
human short-run permission persists. MA-S-2 remains rejected48/52; Rational controls
unresolved, whole-candidate promotion blocked. No old rerun/tuning/gate changes.
Eight MA-T current final-review/fix/closure/publication continuation bindings map
ONLY to MA-U beforecopies via continuation-map.json. MA-T original plan mappings
and all older mappings preserved. Master6f68e24/source/test/userenv unchanged;
CIoff/HHdisabled/automationpaused; broader plan OPEN. Accepted MA-U records frozen.
'''
p=R/'diagnostics/simplex-core-architecture/STATUS.md';s=p.read_text();a=s.index('## Exact next action\n');z=s.index('\n## Previous MA-S admission preparation',a);p.write_text(s[:a]+'## Exact next action\n\n'+b+s[z:])
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';p.write_text(p.read_text().rstrip()+'\n\n## MA-U rounding guard offline preparation (2026-10-14)\n\n'+b)
print('Updated continuation; eight prior bindings preserved')
