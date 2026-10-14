from pathlib import Path
import json,hashlib
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture/results/MA-T'
for x in json.loads((D/'continuation-map.json').read_text())['old_bindings']:
 if hashlib.sha256(Path(x['path']).read_bytes()).hexdigest()!=x['sha256']:raise SystemExit('Continuation drift')
b='''MA-T SOURCE/DESIGN plan prepares a local Bool rounding guard with call-site inline
of the existing KeyValue.get lookup, preserving exact scoped/global equality and
all earlier type/backend/shape/n16 gates. No direct HAMT clone/cache/global method
changes. Zero allocations remain a future measured gate, not an established fact.
See docs/superpowers/specs/2026-10-14-ma-rounding-guard-design.md and
2026-10-14-ma-rounding-guard.md plan; results/MA-T/review.md/json records independent
review. Current step has no Julia/candidate/driver/measurement or production edit.
Next is MA-U offline candidate/test preparation and independent review. Only then
MA-V may prepare its separate short immutable admission: two90second processes,
180seconds total maximum, one attempt, no automatic retry. Standing human short-run
permission remains; a numerical admission is still required. MA-S-2 stays rejected
48/52, Rational controls unresolved, full DenseLU promotion blocked. No old reruns,
threshold changes or substitution of this local guard result for complete gates.
Six MA-S-FALLBACK current continuation review/closure/publication bindings map ONLY
to MA-T beforecopies via continuation-map.json; all earlier mappings unchanged.
Master6f68e24/source/test/userenv unchanged; CIoff/HHdisabled/automationpaused;
broader plan OPEN. MA-T documents and accepted records freeze after publication.
'''
p=R/'diagnostics/simplex-core-architecture/STATUS.md';s=p.read_text();a=s.index('## Exact next action\n');z=s.index('\n## Previous MA-S admission preparation',a);p.write_text(s[:a]+'## Exact next action\n\n'+b+s[z:])
p=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';p.write_text(p.read_text().rstrip()+'\n\n## MA-T scoped rounding guard plan (2026-10-14)\n\n'+b)
print('Updated continuation with six exact predecessor mappings')
