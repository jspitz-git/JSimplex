"""One separate source/design amendment; initial review and all numerical evidence stay frozen."""
from common import *
import shutil
spec=R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md';plan=R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md';ct=Q/'continuation-text.md'
require(rd(Q/'review.json')['accepted'] is False,'Expected preserved initial rejection')
require(bindings(rd(Q/'review.json')),'Initial review bindings changed')
require(bindings(rd(Q/'source-evidence.json')),'Initial source evidence changed')
maps={}
for live,before in [(spec,Q/'spec.before-review.md'),(plan,Q/'plan.before-review.md'),(ct,Q/'continuation.before-review.md')]:
 require(not before.exists(),'Before copy already exists');shutil.copyfile(live,before);maps[str(live)]={'sha256':sha(live),'preserved':str(before)}
def replace_once(text,a,b):
 require(text.count(a)==1,'Expected one exact amendment anchor');return text.replace(a,b)
s=spec.read_text();s=replace_once(s,'It affects only an actual Float64\nnative UMFPACK factor.','It affects managed Float64\nUMFPACKBackend basis factors constructed through the policy-aware factory.')
insert='''## Auxiliary safeguard boundary

This is a **managed basis-backend policy**, not a global override for every
native LU in a solve. Four raw auxiliary paths in `src/dual_simplex.jl` keep their
original `lu(B)` behavior and controls: `_try_refine_dual_prices!` (line102),
`_small_dual_refinement_factor` (line176, native/general branch),
`_try_refine_dual_direction!` (line949) and `_try_refine_dual_pivot!` (line1012).
The existing Markowitz-specific small-pivot helper stays unchanged too.
These temporary refinement/stabilization factors are not UMFPACKBackend objects
and are explicitly outside this option's scope. A threshold-one solve may thus
use threshold-one managed basis factors together with default auxiliary factors.
Existing higher-precision arithmetic inside safeguards remains unchanged.

Fresh managed recovery via `_recovery_trial` still uses preserved SolverOptions
and must receive the selected policy. This distinction is tested/documented;
it is not a promise that all recovery arithmetic or raw auxiliary LU receives
threshold-one. Preserve `src/dual_simplex.jl` byte-for-byte in the candidate.
No new auxiliary policy routing, removal of safeguards or complete native-work
claim follows. Future comparisons must disclose this mixed scope on both sides.

'''
s=replace_once(s,'## Direct prototypes and comparison boundary\n',insert+'## Direct prototypes and comparison boundary\n');spec.write_text(s)
s=plan.read_text();s=replace_once(s,'## Review focus\n','- Policy scope is managed UMFPACKBackend basis factors only. The four raw auxiliary LU safeguard paths named in the spec remain byte-identical and use original controls; threshold-one does not mean every native LU in a solve.\n\n## Review focus\n')
s=replace_once(s,'Existing singular-wrapper tests remain intact.','Existing singular-wrapper tests remain intact. Require whole-file identity of `src/dual_simplex.jl`; explicitly classify its four raw auxiliary LU paths as outside the policy. Document that those default-control safeguards can coexist with threshold-one managed basis factors.')
s=replace_once(s,'Exact component totals88constructions+176refactors+4224solves;','Exact component totals88constructions+176refactors+4224solves; the specified fresh/no-spare then private-spare path implies176fresh native LU and88lu! attempts, not264fresh LU. These source-derived native entry counts are not a complete native-internal operation trace;')
s=replace_once(s,'Add one fixed tiny PFI threshold-one recovery-trial test using the existing checkpoint/recovery test setup and real `_recovery_trial`, plus copied phase/remaining/auxiliary/precision option assertions.','Add one fixed PFI Float64 threshold-one recovery-trial test from `test/basis_recovery_tests.jl`, testset "Basis checkpoints own working data and preserve consumed work", Float64 setup: `LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])`, options `verbose=false,native_pivot_policy=:threshold_one`, then initialize and `checkpoint_basis`. Call `_recovery_trial(w,c,_guard_stop_callback(()->false))` once; require a non-nothing trial, the new private managed factor policy and unchanged live factor/controls, allowing the existing consumed refactor counter to advance. Add copied phase/remaining/auxiliary/precision option assertions.')
plan.write_text(s)
s=ct.read_text();s=replace_once(s,'constant enum per native backend, private controls only on fresh Float64 LU.','constant enum per managed native basis backend, private controls on its fresh\nFloat64 LU. Four raw auxiliary dual-refinement/stabilization lu(B) paths retain\noriginal default controls; this is not a global native-LU override.');ct.write_text(s)
dual=R/'src/dual_simplex.jl';recovery=R/'test/basis_recovery_tests.jl'
checks=dict(initial_rejection_preserved=rd(Q/'review.json')['accepted'] is False,three_before_copies=len(maps)==3 and all(sha(z['preserved'])==z['sha256'] for z in maps.values()),managed_scope='managed basis-backend policy' in spec.read_text(),four_auxiliary_paths=all(n in spec.read_text() for n in ['_try_refine_dual_prices!','_small_dual_refinement_factor','_try_refine_dual_direction!','_try_refine_dual_pivot!']),dual_source_unchanged=sha(dual)==rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'].get('src/dual_simplex.jl',rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'].get(str(dual))),recovery_fixture='Basis checkpoints own working data and preserve consumed work' in recovery.read_text() and 'test/basis_recovery_tests.jl' in plan.read_text(),native_entry_ledger='176fresh native LU and88lu! attempts' in plan.read_text(),continuation_scope='not a global native-LU override' in ct.read_text())
paths=[Path(__file__),spec,plan,ct,dual,recovery,*[Path(z['preserved']) for z in maps.values()],Q/'review.md',Q/'review.json',Q/'reviewer-check.py',Q/'reviewer-check.json']
save(Q/'review-fix.json',dict(all_passed=all(checks.values()),checks=checks,mappings=maps,sha256={str(p):sha(p) for p in paths},scope='Separate text-only scope/recovery-fixture/native-entry clarification; no Julia or old script rerun. Initial reviewer checker case-sensitive false is preserved and not a plan defect.'))
require(all(checks.values()),'Review fix failed; preserve');print(dict(all_passed=True,checks=len(checks),bindings=len(paths)))
