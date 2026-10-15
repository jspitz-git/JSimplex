"""One-shot continuation update after accepted offline preparation review."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[4];D=Path(__file__).resolve().parent
r=json.loads((D/'preparation-review.json').read_text())
if r.get('accepted') is not True or r.get('findings')!=[]:raise SystemExit('Preparation review not accepted')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';roadmap=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
if status.read_bytes()!=(D/'STATUS.md.before-green-admission').read_bytes() or roadmap.read_bytes()!=(D/'roadmap.md.before-green-admission').read_bytes():raise SystemExit('Continuation changed')
old='''Next concrete work: NEW GREEN-only offline admission/control/overlay preparation
with corrected files/counts, unchanged focused slices and fresh output paths.
Reuse immutable accepted RED evidence; do not rerun RED or old failed GREEN.
Then fresh host/seal and independent exact-run admission before one <=90s GREEN.
Standing permission covers short runs; no new permission question is needed.
Tasks3–4 remain gated on accepted full correctness. Original artifacts frozen.'''
new='''NEW GREEN-only offline admission is independently accepted; see
DIRECT-LU-GREEN-ADMISSION.md and results/DIRECT-LU-GREEN-ADMISSION.
72new helper checks PASS; fresh inventory4,611/required185 binds corrected exact
candidate overlay, repaired driver/test and unchanged six focused slices.
Only GREEN/90s/exit0/exact12groups/19,557assertions is accepted by config.
Both sealing and launch revalidate complete immutable RED and accepted repair.
No Julia, sealing, reservation or process was executed by this preparation.

Next concrete step: seal.py green in DIRECT-LU-GREEN-ADMISSION after fresh
host/pins/preparation review validation, then independent exact green-admission
review and one <=90s GREEN using launch.py green. Reuse accepted RED records;
never rerun RED or old failed GREEN. No extra human permission is needed.
Stop/preserve any unexpected failure; no retry/tuning/increased limit.
Tasks3–4 remain gated on full accepted correctness; no production promotion.
The repair closure/publication current continuation keys map ONLY to
DIRECT-LU-GREEN-ADMISSION/STATUS.md.before-green-admission and
roadmap.md.before-green-admission (four mappings); all older maps unchanged.'''
s=status.read_text()
if s.count(old)!=1:raise SystemExit('Next-step anchor missing')
status.write_text(s.replace(old,new))
with roadmap.open('a') as f:f.write('''
## 2026-10-15: corrected GREEN-only admission prepared

DIRECT-LU-GREEN-ADMISSION.md and its new result directory record independently
accepted OFFLINE controls/overlay.72helper tests PASS,4,611freshpins/185required
bindings; candidate overlay differs only in reviewed correctness.jl, driver is
exact repaired text and six focused slices unchanged. Expected12groups/19,557
assertions,90secondsinclusive. RED command is forbidden by config/phase gates;
full immutable RED evidence and repair acceptance are checked beforeseal/launch.
No Julia/sealer/reservation/numerical process ran. Original89PASS/1ERROR and false
audit remain frozen. Work schedule unchanged; coldrepaircopy/checkcostexplicit.

Next fresh seal.py green, independent exact green-admission review, then one
short launch.py green under retained limits. Standing permission sufficient;
any unexpected failure stops without retry/tuning. Tasks3–4/cost/publicsolver/
production remain gated. Four prior repair closure/publication continuation keys
map ONLY to this package's before-green-admission copies; all old mappings stay.
Master6f68e24 unchanged, CIoff/HHdisabled/automationpaused; broader plan open.
''')
with (R/'.superpowers/sdd/2026-10-14-direct-lu-markowitz/progress.md').open('a') as f:f.write('''
- New GREEN-only admission prepared and independently accepted offline:72helper
 checks,4611freshinventory,185requiredreviewbindings. Newoverlayonlycorrectness
 changed,driverexactrepair/sixfocusedslicesunchanged. PriorRED fullread-only
 validator andrepairbinding gates beforeseal/launch. NoJulia/seal/reservation.
 Next freshseal/exactindependentstageadmission/one90sGREEN; noREDretry.
 Ruling: preserve all old artifacts and plan workspace; never generic cleanup.
''')
print('Continuation updated after accepted preparation review')
