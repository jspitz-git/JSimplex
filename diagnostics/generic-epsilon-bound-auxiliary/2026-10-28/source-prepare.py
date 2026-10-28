from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-epsilon-bound-auxiliary/2026-10-28');O=D.parents[1]/'generic-unit-perturb-residual/2026-10-28';sys.path.insert(0,str(D));import common as c
source=(D/'baseline/src/dual_simplex.jl').read_text();a=source[source.index('function _dual_direction_residual_ok!('):source.index('# The entering direction can be accurate')]
bf=a[a.index('function _dual_direction_residual_ok!(workspace::SimplexWorkspace{T},\n                                      direction::Vector{T}, pivot::T) where {T<:BigFloat}'):]
needle='    roundoff = T(256) * eps(one(T))\n    pivot_tolerance = sqrt(eps(one(T))) * _primal_direction_magnitude(pivot)'
c.need(bf.count(needle)==1,'exact BF epsilon site')
newbf=bf.replace(needle,'    roundoff_multiplier = T(256)\n    epsilon = eps(one(T))\n    roundoff = roundoff_multiplier * epsilon\n    pivot_tolerance = sqrt(epsilon) * _primal_direction_magnitude(pivot)')
source=(D/'baseline/src/lp_refinement_driver.jl').read_text();b=source[source.index('function _lp_errors('):source.index('function _lp_improves(')]
newb=b.replace('function _lp_errors(ws,residuals::LPResiduals{R}) where R','function _lp_errors(ws,residuals::LPResiduals{R}) where {R<:Union{BigFloat,Rational{BigInt}}}').replace('lo = has_lower ? R(bound_value(lower)) : zero(R)','lo = has_lower ? R(bound_value(lower)) : value').replace('hi = has_upper ? R(bound_value(upper)) : zero(R)','hi = has_upper ? R(bound_value(upper)) : value')
d=source[source.index('function _lp_auxiliary_run(ws,'):source.index('function _lp_auxiliary_run_at_working_precision(')]
wrapper=source[source.index('function _lp_auxiliary_run_at_working_precision('):source.index('function _lp_errors(')]
oldbasis='Basis(copy(ws.basis.basic_indices),vcat(ws.basis.states,fill(AT_LOWER,length(map.fixed_activities))))'
c.need(d.count(oldbasis)==1,'exact double-copy site')
newd=d.replace('function _lp_auxiliary_run(ws,','function _lp_auxiliary_run(ws::SimplexWorkspace,').replace(oldbasis,oldbasis[:-1]+',Val(:owned))')
changes=[dict(variant='A',file='src/dual_simplex.jl',old=bf,new=newbf),dict(variant='B',file='src/lp_refinement_driver.jl',old=b,new=b+newb),dict(variant='C',file='src/lp_refinement_driver.jl',old=d,new=d+newd)]
c.put('changes.json',changes)
imports='''import JSimplex
using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,LPResiduals,Basis,AT_LOWER,OPTIMAL,
 _pipeline_changed!,_primal_direction_magnitude,bound_value,_is_fixed,
 _lp_child_diagnostics,_lp_auxiliary_options,SimplexProgressContext,_lp_auxiliary_policy,
 _lp_workspace,_precision_current_bits,_simplex_event!,_dispatch_lp_auxiliary,
 _original_dual_witness,_sync_run_budget!,_merge_lp_diagnostics!,_with_transfer_precision
'''
for arm in ['Reference','A','B','C']:
 body=a+b+d+wrapper
 if arm=='A':body=body.replace(bf,newbf)
 if arm=='B':body=body.replace(b,b+newb)
 if arm=='C':body=body.replace(d,d+newd)
 (D/(arm+'.jl')).write_text('module EBA'+arm+'\n'+imports+body+'\nend\n')
shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(D/'launch.py').write_text((O/'launch-qualified.py').read_text().replace('from common_qualified import','from common import').replace('contract-qualified.json','contract.json').replace('pins-qualified.json','pins.json').replace('admission-qualified.json','admission.json'))
(D/'DESIGN.md').write_text('''# Epsilon, unused bound values and owned auxiliary basis
The human selected all three source proposals for short whole-function correctness/time/allocation measurements and autonomous accepted integration with independent review.
A: BigFloat _dual_direction_residual_ok! computes the SAME eps(one(T)) expression once at its first original site, after constructing T(256) as before. Private epsilon is read by multiplication and sqrt; neither mutates it or returns it. No cross-call/context cache; all scratch updates, arithmetic/term order, bounds, finite checks and tolerances stay.
B: only LPResiduals{BigFloat}/LPResiduals{Rational{BigInt}} _lp_errors: use already-read value as the UNUSED lo/hi placeholder for absent bounds. Each numerical read remains dominated by has_lower/has_upper. Finite bound conversions/order and all returned-metric constructors/magnitudes stay. Do not share abs between returned metrics or change their scalar alias graph. Generic/native/fixed types unchanged.
C: only actual SimplexWorkspace _lp_auxiliary_run: transfer its existing fresh copy(indices) and fresh vcat(states,suffix) into existing Basis(...,Val(:owned)). Remove constructor's duplicate Int.(...) and collect(states), retaining all caller isolation and later _lp_workspace independent Basis copy. Public two-argument Basis and generic nonworkspace route stay original. Factorization, solves, stops, witnesses, budget finally/merge and observers remain real and ordered.
Alternatives: eps(T) substitution changes the expression rather than just sharing it; global constants need precision/callback invalidation; sharing abs could change returned owners; removing _lp_workspace basis copies would change caller isolation. Those are excluded.
''')
(D/'PLAN.md').write_text('''# Epsilon, bound placeholders and auxiliary basis implementation plan
> For agentic workers: superpowers:executing-plans inline; independent numerical admissions/results and final production review.
**Goal:** Measure all three complete-call variants and integrate only independently accepted changes.
**Architecture:** Existing diagnostic worktree, immutable actual master235eedf baseline, private Reference/A/B/C snippets with no production overwrite; ordinary Test.
**Tech Stack:** Installed Julia1.13, Test/SparseArrays/LinearAlgebra/TOML; existing guarded single-process launcher.
**Spec:** DESIGN.md and explicit human request.
## Global constraints
Fresh boot/start_ticks/command/675groups ANDsessions/noJulia and local/live refs verified. Preserve every older raw/rejection/script/worktree/userfile/index and beforeimage; do not rerun frozen artifacts. Julia/BLAS1 GC1,0 heap2GiB VM8GiB RAMavailable>=6GiB swap<=1GiB compiled-modules existing. One short900s comparison. Ordinary RED/GREEN/actualMASTER use4500s shared/4492guard each (longer regression allowance avoids timeout-only repetitions; no multi-hour process). CIoff automationpaused HHreuse disabled; broader/fullsuite/x64/native-retentionOPEN. No new dependency, tolerance, precision or pivot-policy change.
## Review focus
Stored512 vs ambient64/128/256 and5rounding modes; source-order T(256) before epsilon; nonfinite/zero/dimension/index residual checks; absent/fixed/finite bounds with original metric scalar aliases; actual auxiliary solve/counters/stops/observer exception and independent basis buffers. Native/exact controls remain original for A/B; C applies all precisions through concrete Basis arrays. Whole C includes actual constructor/factor/recompute/solver/witness/merge, not a stub.
## Task1 — private comparison
- [ ] Prepare tests/fixtures and fixed3warm/9alternating pairs on sparse/dense small/medium fixtures. Real C auxiliary calls have zero objective, valid transferred basis and optimum0; finite shared work/clock/stop remains. Count exact planned calls and source-derived backend entries separately, no complete PREforward/native/import proof.
- [ ] Seal actual source/runtime/driver/auditor/grid; independent admission before ONE900s process; full raw/type/source/resources audit and per-variant result review. Separate fixture/reset/cold/warm/validation/GC/consumption; retain slower/GC/all byte outliers, distinguish per-cell medians from individual pairs.
## Task2 — production qualification
- [ ] Permanent ordinary correctness and supported3-pair allocation gates; run original RED before applying production changes.
- [ ] Accepted exact source inverses, independent review, GREEN prior82files+new test (plus concrete missing affected files only); private-index commit/actualcommit review/ff-only actualMASTERsamefiles/frozenGREENtotal; normal push after accepted actualMASTER. No threshold relaxation/release exception.
## Task3 — publication
- [ ] Preserve exact continuation/index/source beforeimages/maps; truthful current report; independent actual artifacts review, one PASS closure then exactnames/blobs staged/committed and normal diagnostic push/remote verification. No cleanup/automatic next experiment.
''')
(D/'WORK-MEMORY.md').write_text('''# Work and memory
A, each reached BigFloat direction residual check: two identical eps(one(T)) evaluations become one. Existing T(256) construction remains first; same multiplications/sqrt/absolute values/scans/scratch/guards. Local read-only scalar lives one invocation, no retained cache. Constant scalar work saving, unchanged O(nnz(B)+m) core, actual whole-call result must be measured.
B, LP initial residual metrics and every correction candidate reaching _lp_errors: remove one zero constructor for each absent endpoint (0..2 per variable). No new numerical operation, conversion, array pass, persistent field or output alias; value was already read. Separate specialized union method adds cold metadata. Output zeros/abs and finite bound conversions retained. Native/fixed cases original.
C, each auxiliary correction run reaching setup: remove two duplicate arrays and copies of m Int indices plus m+n+k VariableState entries (k appended fixed activities). Existing first index copy, suffix fill, state concatenation and all later _lp_workspace copies remain. No factor/solve/refactor/callback/budget omission; no input aliases. One concrete workspace specialization adds cold metadata. Numeric/native retention and end-to-end benefit unqualified. Full auxiliary solve/setup cost may dwarf these copies.
''')
(D/'progress.md').write_text('# Ledger — plan: '+str(D/'PLAN.md')+'\nTask0: complete; fresh675groups/sessions, baseline544files, noJulia.\nRuling: preserve separate read-only snippet candidates; production is untouched until original RED.\nRuling: 4500s regression limit selected before admission based on prior54minute82file suite and the human preference for longer tests rather than timeout retries.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('three private source candidates and bounded plan prepared; noJulia')
