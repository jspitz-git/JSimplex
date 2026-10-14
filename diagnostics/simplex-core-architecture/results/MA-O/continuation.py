"""One-shot continuation update after independent MA-O result acceptance."""
from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-O'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
review=json.loads((D/'result-review.json').read_text())
if not review['accepted'] or review['findings'] or not all(review['checks'].values()) or not all(sha(p)==h for p,h in review['sha256'].items()):raise ValueError('result review missing or drift')
status=R/'diagnostics/simplex-core-architecture/STATUS.md';road=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md'
current="""MA-O completed the repaired bounded qualification. Correctness passed;
the exact performance proposal is NOT ACCEPTED and is not promoted.
Original RED8Pass/2expectedFail and candidateGREEN3787/3787 passed across222
fixtures. Three exit0 processes, stage audits16/14/14PASS,3924 launchpins/73trees.
Fresh independent admission27checks25bindings and separate result review accepted
the diagnostic/rejection decision; no performance promotion. See
MA-PRESOLVE-REPAIRED-QUALIFICATION.md and results/MA-O/result-review.md.

All76cases/4560windows/583680timedcalls completed; measuredcompile/recompile0.
All35GCwindows (27measured) retained. Aggregate accepted=false:20/24targets and
6/52controls pass every gate. Targets pooledratios0.840413–0.953667; alltarget
bytes/events lower, but fourfail faster-pair gates. Control failures overlap:
33bytes,31pooledtime,28processtime,1events. Some tiny fallback differences have
unproved cause; original strict gates remain unchanged. Material tail-zero
regression:ratio1.103281,+39920bytes/+1664events per128calls in everyprocess.
No general or whole-presolver speedup and no claim all MA approaches fail.

Three invocation durations17.752369/11.774218/11.750124s,total41.276710s are cap
evidence, not benchmark speedups. All3slots CONSUMED. No retry/tuning/threshold
change/case removal/automaticnewvariant. Postcheck28PASS independently recomputes
all76rows and checks all3924hashes; it is postexit, NOTretroactivelaunchpin.
Fresh full146groups ANDsessions absent/noJulia; process identities are recorded
in postcheck.json with boot/start_ticks/initialcommands.39resource samples,
minavailable22682096KiB,swap0. Candidate/input/oracle/sourcebytes unchanged.

This exact selective eight-term Rational{BigInt} candidate is stopped for
production admission. MA-O creates no integration plan because all76gates were
required. A different future approach needs its own concrete plan; do not create
an equivalent inventory or silently retune this measured candidate. Other already
authorized independent roadmap work may continue within its existing gates.
The broader performance plan remains OPEN; no automatic numerical continuation.

MA-N current STATUS/roadmap bindings in continuation-map, original+finalclosure
and original+finalpublication map ONLY to MA-O/STATUS.md.before-MA-O and
roadmap.md.before-MA-O (tenbindings). MA-N beforecopies still resolve sixMA-M
bindings; all older maps remain. Every MA-O/N/M and older script/pin/raw/review
is frozen, NEVER RERUN/rewrite. MA-N initialfalsepublication/twoexactwhitespace
supplement+finalPASS preserved. Master6f68e24/production/tests/env/CI unchanged;
CIoff,HHdisabled,automationpaused. Other rejections and broader gates unchanged.
"""
for p,before,start,end,hist in ((status,D/'STATUS.md.before-MA-O','## Exact next action\n\n','## Previous MA-M qualification (stopped)','## Previous MA-N preparation (completed)'),(road,D/'roadmap.md.before-MA-O','## Current continuation — 2026-10-14\n\n','### Previous MA-M qualification (stopped)','### Previous MA-N preparation (completed)')):
 if p.read_bytes()!=before.read_bytes():raise ValueError('before drift')
 prefix,rest=p.read_text().split(start,1);block,tail=rest.split(end,1);out=prefix+start+current+'\n'+hist+'\n\n'+block+end+tail
 if p==status:out=out.replace('MA-N offline harness repair accepted; next MA-O fresh admission and repaired qualification. GREEN/cost unexecuted; no promotion','MA-O correctness passed; selective proposal rejected by cost gates (26/76). No promotion or automatic retry')
 p.write_text(out)
paths=[status,road,D/'STATUS.md.before-MA-O',D/'roadmap.md.before-MA-O']
v=dict(mapping={str(status):str(paths[2]),str(road):str(paths[3])},applies_only_to='Ten MA-N current continuation-map/original+final closure/original+final publication bindings; older maps unchanged',sha256={str(p):sha(p) for p in paths})
with(D/'continuation-map.json').open('x') as f:json.dump(v,f,indent=2);f.write('\n')
print('MA-O continuation updated with rejection and ten exact previous bindings.')
