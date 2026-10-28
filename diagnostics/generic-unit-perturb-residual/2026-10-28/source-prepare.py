from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-unit-perturb-residual/2026-10-28');O=D.parents[1]/'generic-residual-pivot-crash/2026-10-28';sys.path.insert(0,str(D));import common as c
c.put('source-host.json',c.host())
def region(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
p=(D/'baseline/src/primal_simplex.jl').read_text();q=(D/'baseline/src/simplex_perturbation.jl').read_text();l=(D/'baseline/src/lp_refinement.jl').read_text()
score=region(p,'function _primal_weighted_score(reduced_cost::T,','_primal_dantzig_score(reduced_cost::T)')
newscore='''function _primal_weighted_score(reduced_cost::Rational{BigInt}, weight::Rational{BigInt})
    squared = big(reduced_cost)^2
    # Preserve the original square and its exceptions before inspecting weight.
    return isfinite(reduced_cost) && isone(weight) ? squared : squared / big(weight)
end

'''
enter=region(p,'function _primal_entering(workspace::SimplexWorkspace{T},','function _primal_update_devex!')
dual=region(q,'function perturb_dual_costs!','# Automatic shifts')
dualcore=region(dual,'function _perturb_dual_costs_precise!','\nend\n')+'\nend\n'
newdual=dualcore.replace('journal::PerturbationJournal{T},','journal::PerturbationJournal{BigFloat},',1).replace('policy,stop_requested)::Int where T','policy,stop_requested)::Int\n    T = BigFloat',1).replace('        local_scale = one(T)+min(abs(old_cost),one(T))','        unit = one(T)\n        local_scale = unit+min(abs(old_cost),unit)')
primal=region(q,'function perturb_primal_bounds!','_adaptive_primal_perturbation_enabled(policy)')
expanded=region(primal,'function _expanded_basic_bound','function _perturb_primal_bounds_precise!')
newexpanded=expanded.replace('original::Bound{T},current::Bound{T},value::T,','original::Bound{BigFloat},current::Bound{BigFloat},value::BigFloat,',1).replace('direction::T,tolerance::T,cap::T,level::Int,index::Int) where T','direction::BigFloat,tolerance::BigFloat,cap::BigFloat,level::Int,index::Int)\n    T = BigFloat',1).replace('    scale = one(T)+min(abs(original.value),one(T))','    unit = one(T)\n    scale = unit+min(abs(original.value),unit)')
residual=region(l,'function _lp_residual_values','_lp_power_of_two')
newresidual=residual.replace('primal = copy(v[n+1:end])','primal = v[n+1:end]').replace('vcat(_copy_working_values(R, ws.problem.objective), copy(y))','vcat(_copy_working_values(R, ws.problem.objective), y)')
imports='''using SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,Bound,bound_value,PerturbationJournal,BoundPerturbationState,StagnationMonitor,LPResiduals,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,
    _is_exact,_is_fixed,_primal_direction_magnitude,_prepare_auto_pricing!,_partial_pricing_enabled,_select_workspace_pool!,_effective_pricing,_primal_initialize_steepest!,_primal_steepest_weight!,_primal_dantzig_score,_record_full_pricing!,
    _check_perturbation_owner,_perturbation_stopped,_with_recovery_precision,_finite_workspace,dual_infeasibility,primal_infeasibility,_invalidate_basis_checkpoints!,_reset_workspace_stagnation!,_simplex_event!,_copy_working_values,_working_value_bits,_lp_residual_bits
'''
for arm in ['Reference','A','B','C']:
 body=score+(newscore if arm=='A' else '')+enter+dual+(newdual if arm=='B' else '')+primal+(newexpanded if arm=='B' else '')+(newresidual if arm=='C' else residual)
 (D/(arm+'.jl')).write_text('module UPR'+arm+'\nimport JSimplex\n'+imports+body+'\nend\n')
c.need(newdual!=dualcore and newexpanded!=expanded and newresidual!=residual,'exact changes')
c.put('changes.json',[dict(variant='A',file='src/primal_simplex.jl',old=score,new=score+newscore),dict(variant='B',file='src/simplex_perturbation.jl',old=dualcore,new=dualcore+newdual),dict(variant='B',file='src/simplex_perturbation.jl',old=expanded,new=expanded+newexpanded),dict(variant='C',file='src/lp_refinement.jl',old=residual,new=newresidual)])
c.put('source-clones.json',{a:c.sha(D/(a+'.jl')) for a in ['Reference','A','B','C']});shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'))
(D/'common.py').write_text((D/'common.py').read_text().replace('contract-final.json','contract.json').replace('pins-final.json','pins.json'))
(D/'launch.py').write_text((O/'launch-final.py').read_text().replace('common_final','common').replace('contract-final.json','contract.json').replace('pins-final.json','pins.json').replace('admission-final.json','admission.json'))
(D/'DESIGN.md').write_text('''# Unit-weight exact score, private perturbation unit and residual containers
The human chose all three proposals for short complete-function correctness/time/allocations and autonomous accepted production integration with all safeguards and independent review.
A only Rational{BigInt} weighted score computes the same original square first, then skips division only for finite cost and exactly unit weight. Nonunit/nonfinite cases keep the original division; all other Rational methods unchanged. GMP multiplication creates fresh numerator/denominator owners even at zero/unit; verify returned score fresh from inputs and across calls. Whole _primal_entering includes original eligibility/scans/ties/counters/negative tolerance; explicit devex and cached-steepest cover one/mixed/nonunit weights. No partial-pool performance claim; helper is used there but original pool flow is not cloned or bypassed.
B only BigFloat core dual-cost perturbation and expanded-bound calculation use one fresh local unit where original expression makes two. No shared numeric cache across callbacks/iterations/calls; original abs and all arithmetic/order, zero checks, cap, representability, counts/publication/journal/owner/cancellation/exception behavior stay. Generic native/exact methods unchanged. Whole public dual/primal handlers include owner/type/policy/monitor/cooldown guards, finite/feasibility scans, copies, loops, final stop and publication/reset/events. Exact types are unchanged early-return controls; active floating cases must actually shift and compare full state.
C removes outer copy around an already fresh values slice, and redundant copy(y) passed to vcat. Whole _lp_residual_values and outer _lp_residuals preserve initial independently owned input copies/conversions, all finite/dimension checks, term order, output vector independence and original scalar sharing relationships. Only two temporary vectors of length m and their copies disappear. No numerical copy/guard/recompute omission or new views/cache. Test direct and actual outer precision wrapper, native/exact controls and stored512 values.
Alternatives excluded: persistent perturbation constants need callback/precision invalidation; raw division removal for nonunit weights changes mathematics; streaming LP-scale filter can add zero scans and is not this task. No tolerance/precision/policy/coefficients/arithmetic reassociation changes.
''')
(D/'PLAN.md').write_text('''# Unit perturbation residual implementation plan
> For agentic workers: superpowers:executing-plans inline; independent concrete admission/result and production reviews.
**Goal:** Short paired comparison of all3 private candidates, integrate only independently accepted whole-call improvements.
**Architecture:** Existing isolated diagnostics worktree with private exact Reference/A/B/C and baseline actual85f8275b; ordinary Test, fixed3warm/9alternating measured pairs. Production only after meaningful original allocation RED.
**Tech Stack:** Julia1.13 installed, Test/LinearAlgebra/SparseArrays/TOML, existing guarded single Julia process.
**Spec:** DESIGN.md and direct user request.
## Constraints
Fresh refs+boot/start_ticks/command/full667groups ANDsessions/noJulia before pinned work. Preserve all old/user files/indexes/worktrees/raw/rejections; sole exact WSL identity allowance. Julia/BLAS1 GC1,0 heap2GiB AS8GiB RAMavailable>=6GiB swap<=1GiB compiled-modules existing. Short comparison900s; focused GREEN/actualMASTER67previous+new+affected perturbation/LP wholefiles with3600s each. No multi-hour attempt. CIoff automationpaused HHreuse disabled, broader/fullsuite/x64/native retentionOPEN. PlainTest, no custom recorder/manual stack. No new dependency or repeated frozen scripts/numericaltuning.
## Review focus
Unit/nonunit/zero/infinite rational weights/costs and fresh result owners; BigFloat64/128/256 five rounding modes/stored512; actual shifted/unshiftable/earlyreturn perturbations with active journals/stop/callbackprecision/exception rollback; residual empty/dimension/nonfinite/alias/source-vs-output scalar owners and exact dyadic reference. Each must have ordinary tests and correct bounded work ledger.
## Task1
- [ ] Fixed sparse/dense n16/64(m8/32), sign/weight controls, real public handlers and outer residual precision calls. Separate fixture/cold/warm/reset/validation/GC/consumption; whole-call compilezero/allGC/outliers retained.
- [ ] Independent immutable source/grid/driver/guard/auditor admission before one900s process; full raw/type/context/source/resource audit and independent pervariant decision. No benchmark rerun-to-pass.
## Task2
- [ ] Permanent ordinary correctness and supported fixed3pair allocation regressions, exact originalRED fails only intendedcostgates before production stage.
- [ ] Acceptedsource inverse and independent numerical/work/memory review; GREEN old67+new+neededwholefiles, then privateindex exactcommit review/ff-only/localMASTERsamefiles/frozentotal3600s/independent result/normalpush remoteverify. Preserve all original tests/thresholds, no old release exception.
## Task3
- [ ] Exact continuation beforeimages, actual finalreport/review, one PASS closure then exact staged+committed bloblist before failfast diagnosticcommit/push/remoteverify. Prepublication records state their temporal scope; no prematureclosure outcome. No cleanup/newautomaticexperiment.
''')
(D/'WORK-MEMORY.md').write_text('''# Work/memory ledger
A per eligible rational candidate under devex/cached steepest: identical square, one extra finite/isone predicate and removed GMP rational division at unit weight. Nonunit has predicate cost plus original division. Same whole eligibility/weight/scans/ties/output. No new vector/solve/cache; scalar ownership remains fresh. Ordinary Dantzig does not use this score.
B per reached BigFloat cost/bound scale: two one constructors become one invocation-local one; same abs/min/add, all later multiplications/checks/publications. Whole interventions retain copied costs/prices/bounds/owner and feasibility scans, callback counts and recovery precision. Extra2cold specialization methods; no shared mutable numeric owner/retention/invalidation work. This is triggered stagnation work, not each ordinary iteration.
C per LP residual evaluation with mrows: two temporary Vector{R}(m) allocations and2m elementcopy work removed, no scalar-copy/conversion change. Original output containers and scalar-owner sharing relations unchanged. CSC O(nnzA) arithmetic and precision scans remain; no extra pass/solve/cache. LP refinement setup only. No end-to-end/general nativefree/coldmetadata retention proof; preparation and per-call costs measured explicitly.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1: fresh667groups baseline543files/protectedstate, private candidates prepared noJulia.\nRuling: user approved all3 and autonomous integration; no extra approval menu. Reuse existing isolatedworktree, preserve workspaces/frozen records, stagedproduction onlyafteroriginalRED.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('UPR private candidates, plan and work ledger ready; noJulia')
