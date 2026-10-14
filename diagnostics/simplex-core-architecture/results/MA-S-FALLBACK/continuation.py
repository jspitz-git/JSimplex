from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-S-FALLBACK'
for x in json.loads((D/'continuation-map.json').read_text())['old_bindings']:
 if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256'] or hashlib.sha256(Path(x['preserved']).read_bytes()).hexdigest()!=x['sha256']:raise SystemExit('Continuation changed')
block='''MA-S-FALLBACK bounded SOURCE/STORED-EVIDENCE analysis completed without Julia or
new measurements. All336measured control pairs analyzed: BigFloat scoped42pairs
have invariant+128bytes/+8events per4calls, bothorders/directions/processes; extra
present scoped rounding lookup is leading source-supported suspect, exact emitted
objects/cause UNPROVEN. Rational42pairs:21positive/19negative/2zero byte deltas,
all event deltas0; immediate type fallback bypasses rounding/MA/scratch. Native
usable-size accounting compatible, not captured causal proof. Same-binary S4-O
instruction evidence reused, no new objdump/loading. Side-median difference is not
median pair difference; frozen gates unchanged, no filtering or harmless-noise claim.
Entry13PASS/analysis21checks24readtimehashes(12launch-pinned),source514/protected6,
full166groups ANDsessions/noJulia. See MA-DENSELU-FALLBACK-ALLOCATION-ANALYSIS.md
and results/MA-S-FALLBACK/review.md/json. No candidate/driver/production changes.
MA-S-2 remains consumed/rejected48/52; all36targets pass but fourfallback controls
block Task3. No rerun/tuning/threshold change. Next useful direction is a separate
bounded design for scoped-lookup attribution/avoidance preserving rounding; exact
runtime attribution needs its own accepted admission. No new numerical plan here.
Six S-2 current result-review/closure/publication continuation hashes map ONLY to
MA-S-FALLBACK beforecopies via continuation-map.json; all older maps unchanged.
Standing short-run permission persists, broader plan OPEN; no automatic retry.
Master6f68e24/source/test/userenv unchanged; CIoff/HHdisabled/automationpaused.
'''
p=R/'diagnostics/simplex-core-architecture/STATUS.md';s=p.read_text();a=s.index('## Exact next action\n');b=s.index('\n## Previous MA-S admission preparation',a);p.write_text(s[:a]+'## Exact next action\n\n'+block+s[b:])
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';p.write_text(p.read_text().rstrip()+'\n\n## MA-S-FALLBACK stored allocation/source analysis (2026-10-14)\n\n'+block)
print('Current continuation updated; six prior bindings preserved')
