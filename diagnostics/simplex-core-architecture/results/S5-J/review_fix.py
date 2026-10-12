"""One exclusive offline wording amendment; original pinned report/plan preserved."""
from pathlib import Path
import hashlib,json
R=Path.cwd();D=R/'diagnostics/simplex-core-architecture';J=D/'results/S5-J';report=D/'S5-DUAL-AUXILIARY-HANDOFF-OWNERSHIP.md';plan=R/'docs/superpowers/plans/2026-10-13-dual-auxiliary-pending-observer-oracle.md'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old={str(p.relative_to(R)):sha(p) for p in (report,plan)}
for p in (report,plan):
 with (J/(p.name+'.before-review')).open('xb') as f:f.write(p.read_bytes())
a=report.read_text();b=plan.read_text();definition='''Here "original-bound" means the live working bounds after entry restoration, as
opposed to the auxiliary box. It does NOT assert equality to authoritative problem
bounds for arbitrary caller-altered buffers. In particular, phase_one=false does
not normalize every unowned working cost/bound buffer. The trial feasibility tests
refer to those live working buffers; original-model certification remains separate.

'''
red={'report_missing_scope':definition not in a,'plan_missing_scope':'pre-auxiliary LIVE working bounds' not in b}
assert all(red.values())
a=a.replace('## Source ownership and publication contract\n\n','## Source ownership and publication contract\n\n'+definition)
b=b.replace('No new fixture mathematics,', 'No new fixture mathematics,') if False else b
needle='selected ownership/state, direct DiagnosticObserverFailure/cause identity, consumed\n'
replacement='''selected ownership/state, direct DiagnosticObserverFailure/cause identity, consumed
'''
assert needle in b
b=b.replace('No\nwhole-function rollback, observer-neutrality, auxiliary certificate transfer or\n', 'No\nwhole-function rollback, observer-neutrality, auxiliary certificate transfer or\n')
b+='''
Terminology: original-bound means pre-auxiliary LIVE working bounds after entry
restoration, not blanket equality to the problem's authoritative bounds for every
caller. phase_one=false need not normalize unowned cost/bound alterations. The
oracle must state its existing fixture's authoritative/live relationship explicitly;
do not infer original-model certification from successful trial feasibility checks.
'''
report.write_text(a);plan.write_text(b)
green={'report_definition':definition in a,'unowned_buffers_explicit':'not normalize every unowned working cost/bound buffer' in a,'certificate_separate':'original-model certification remains separate' in a,'plan_live_scope':'pre-auxiliary LIVE working bounds' in b,'before_copies_match':all(sha(J/(Path(p).name+'.before-review'))==v for p,v in old.items())}
x={'reviewer_severity':'Minor','author_disposition':'Important for avoiding an overbroad original-model contract; fixed once offline before acceptance','RED':red,'GREEN':green,'all_passed':all(red.values()) and all(green.values()),'before_sha256':old,'after_sha256':{str(p.relative_to(R)):sha(p) for p in (report,plan)},'script_sha256':sha(__file__),'no_numerics_or_old_audit_rerun':True}
with (J/'review-fix.json').open('x') as f:json.dump(x,f,indent=2);f.write('\n')
print(json.dumps(x));assert x['all_passed']
