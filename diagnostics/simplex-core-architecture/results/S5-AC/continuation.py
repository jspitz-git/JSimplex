"""Exclusive continuation, only after independent acceptance; preserve old bindings."""
from pathlib import Path
import json,hashlib
R=Path.cwd();H=Path(__file__).resolve().parent;D=H.parent.parent
review=(H/'review.md').read_text();assert 'Verdict: ACCEPTED' in review and 'Unresolved findings: []' in review
S=D/'STATUS.md';P=R/'docs/superpowers/plans/2026-10-11-simplex-core-architecture.md';maps=[]
for p in (S,P):
 q=H/(p.name+'.before-AC');b=p.read_bytes()
 with q.open('xb') as f:f.write(b)
 maps.append(dict(original=str(p),preserved=str(q),sha256=hashlib.sha256(b).hexdigest()))
with (H/'before-texts.json').open('x') as f:json.dump(dict(mappings=maps),f,indent=2);f.write('\n')
summary='''S5-AC SOURCE/DESIGN ONLY decision accepted: omission DEFERRED; the existing
native/no-observer/infinite-context flag gate is insufficient. Native constructor
profile permits explicit policy overrides; no observer still permits diagnostic
events/kernel counts; options and context clocks differ. Zero scratch/default
weights are not reconstructed state. Ordinary initialization failure reaches the
outer handler with workspace=nothing; strict ordinary recovery also returns its
numerical result, so this ownership distinction alone is NOT a demonstrated
changed recovery outcome. Default arithmetic failure equivalence and scratch/cache
initialization remain unproved even for a stricter diagnostics=nothing/infinite-
both-clocks/fixed-hardware subset. No impossibility or new failing fixture claim.
No hidden retry, duplicate work, swallowed logger/observer exception, changed
safeguard or working-to-original certificate transfer is permitted.
Entry20/full1910 hashes, source19/25pins and author8/full1917/6bindings PASS.
AB initial rejection and corrected O provenance, closure35/exact38, AA inventories,
source511/user6/full26groups AND sessions/local+remote refs preserved and verified.
Three read-only rg guessed-path failures preserved; no Julia/parser/import/compile/
native/numerics/executable candidate/driver/launcher/benchmark/test/production/env/
cache/CI change. Fresh independent gpt-6-astra numerical/work/memory review accepted;
no unresolved findings or unnecessary NEW production work/memory. No new saving:
source-derived target only one cold default FTRAN/BTRAN/pricing reconstruction;
constructor/factor/restored/projection/ordinary/certification remain. A184/B/C and
both old medium attributions reused; no equivalent census/current-master speedup.
AB-bound current STATUS/roadmap preserved ONLY in AC.before-AC; AB initial/read-time
mappings remain AB.before-AB and before-review; all older AA/Z/Y/X/W/V/U/T maps intact.
S5 initialization-reuse/end-to-end gate stays OPEN. Next S6-AP is ONE distinct
SOURCE/EVIDENCE ONLY provenance step for the parent's outstanding user test.mps
certificate/recovery failure, under 2026-10-13-test-mps-failure-provenance.md. No new
numerical allowance, replacement model or inferred backend cause. All old numerical
allowances consumed; all frozen evidence/scripts/rejections remain untouched.
CIoff/HHdisabled/fullsuite/x64cause/bootstrapcacheinit/wholecaps/native-retention/
QGCoutlier and all broader gates unchanged.
'''
s=S.read_text();old='**Current continuation: S5-AB reconciliation independently accepted; after separate closure/publication follow `docs/superpowers/plans/2026-10-13-cleanup-entry-reuse-design-decision.md` (S5-AC, source/design only).**';assert s.count(old)==1
s=s.replace(old,'**Current continuation: S5-AC cleanup omission deferred after independent design review; after separate closure/publication follow `docs/superpowers/plans/2026-10-13-test-mps-failure-provenance.md` (S6-AP, source/evidence only).**\n\n'+summary);S.write_text(s)
P.write_text(P.read_text()+'\n## S5-AC cleanup design decision and distinct S6-AP continuation (2026-10-13)\n\n'+summary)
comp=D/'S5-CLEANUP-ENTRY-REUSE-DECISION-REVIEW.md'
with comp.open('x') as f:f.write('''# S5-AC independent numerical/work/memory review

See the verbatim fresh gpt-6-astra review in results/S5-AC/review.md.
Verdict: ACCEPTED; unresolved findings: none. This accepts a bounded design
disposition, not an executable shortcut or a numerical qualification.

The existing native/no-observer/infinite-context description is insufficient;
stricter omission is deferred with explicit unproved failure/state obligations.
No universal impossibility, new numerical counterexample or recovery difference
from early workspace assignment alone is claimed. No unnecessary NEW production
work, allocations or retained memory were introduced. Existing cold reconstruction
work is described without treating it as universally dispensable. No benchmark is
needed for this documentation-only step. The next distinct S6-AP step is limited
to preserved test.mps failure provenance, without a numerical allowance.

All source/user/evidence preservation and publication closure are separate checks.
''')
with (H/'continuation.json').open('x') as f:json.dump(dict(all_passed=True,sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [S,P,comp,H/'review.md',Path(__file__),H/'before-texts.json']}),f,indent=2);f.write('\n')
print('S5-AC continuation written with exact before-texts.')
