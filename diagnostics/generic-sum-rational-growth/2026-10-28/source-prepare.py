from pathlib import Path
import sys,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-sum-rational-growth/2026-10-28');sys.path.insert(0,str(D));import common as c
c.put('source-host.json',c.host());s=(D/'baseline/src/dual_simplex.jl').read_text();f=(D/'baseline/src/factorization.jl').read_text();r=(D/'baseline/src/refactorization_policy.jl').read_text()
def reg(text,a,b):return text[text.index(a):text.index(b,text.index(a))]
interval=reg(s,'function _primal_sum_bounds(left::T, right::T) where {T<:Rational}','function _original_reduced_cost_bounds')
sumbf=reg(s,'function _primal_sum_bounds(left::BigFloat','_primal_difference_bounds(left::T')
needle='isfinite(left) && precision(right) == precision(T) && left == -right &&'
c.need(sumbf.count(needle)==1,'unique cancellation guard')
newsum=sumbf.replace(needle,'isfinite(left) && precision(right) == precision(T) &&\n        signbit(left) != signbit(right) && left == -right &&')
cert=reg(s,'function _infeasibility_certified(workspace::SimplexWorkspace{T},','function _floating_infeasibility_certified')
newcert=cert.replace('workspace::SimplexWorkspace{T},','workspace::SimplexWorkspace{Rational{BigInt}},',1).replace('rho::Vector{T}, below::Bool) where {T<:Rational}','rho::Vector{Rational{BigInt}}, below::Bool)\n    T = Rational{BigInt}',1)
newcert=newcert.replace('        orientation = below ? one(T) : -one(T)\n','')
newcert=newcert.replace('orientation*rho[A.rowval[position]]*A.nzval[position]','(below ? rho[A.rowval[position]] : -rho[A.rowval[position]])*A.nzval[position]')
newcert=newcert.replace('coefficient = -orientation*rho[index-n]','coefficient = below ? -rho[index-n] : rho[index-n]')
growth=reg(f,'_factor_growth_measure(factor::PFIFactorization{T})','_backend_dimension')
newgrowth='''function _factor_growth_measure(factor::PFIFactorization{BigFloat})
    unit = one(BigFloat)
    return maximum(eta -> maximum(_primal_direction_magnitude,eta.values;init=unit),
                   factor.updates;init=unit)
end

'''
refresh=reg(r,'function _refresh_refactor_metrics!','function _record_refactor_quality!')
scheduled=reg(r,'function _scheduled_refactor_reason','_refactor_event(reason')
imports='''using JSimplex: SimplexWorkspace,LinearProblem,Bound,bound_value,PFIFactorization,_is_exact,_primal_nearest_rounding,_primal_direction_magnitude,_infeasibility_bound_allowance,_factor_storage_count,_with_recovery_precision,refactor_reason
using SparseArrays
'''
forward='''_refined_primal_rows_feasible(args...) = JSimplex._refined_primal_rows_feasible(args...)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},b::Bool) where {T<:AbstractFloat} = JSimplex._infeasibility_certified(w,rho,b)
_factor_growth_measure(factor) = JSimplex._factor_growth_measure(factor)
'''
for arm in ['Reference','A','B','C']:
 body=(interval.replace(sumbf,newsum) if arm=='A' else interval)+cert+(newcert if arm=='B' else '')+growth+(newgrowth if arm=='C' else '')+refresh+scheduled
 (D/(arm+'.jl')).write_text('module SRG'+arm+'\nimport JSimplex\n'+imports+forward+body+'\nend\n')
# Owned definitions (including short-form) are never imported or defined on JSimplex.
c.put('changes.json',[dict(variant='A',file='src/dual_simplex.jl',old=sumbf,new=newsum),dict(variant='B',file='src/dual_simplex.jl',old=cert,new=cert+newcert),dict(variant='C',file='src/factorization.jl',old=growth,new=growth+newgrowth)])
c.put('source-clones.json',{a:c.sha(D/(a+'.jl')) for a in ['Reference','A','B','C']})
O=D.parents[1]/'generic-bounds-norm-infeasibility/2026-10-27';shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'));(D/'launch.py').write_text((O/'launch.py').read_text().replace('592','892').replace('600','900'))
(D/'DESIGN.md').write_text('''# Sum, exact-certificate and PFI-growth scalar savings
The human selected all three source-derived proposals for short whole-function correctness/time/allocation comparisons and autonomous accepted integration with all safeguards and independent review.
A: BigFloat sum-bound exact-cancellation test first excludes nonzero same-sign operands. Retain original zero shortcuts, finite/precision guard order, opposite-sign negation/equality, addition, FastTwoSum, underflow tests and widened enclosures. Both original zero outputs remain separately constructed. Measure scalar sum, entire row-interval computation and original-model primal feasibility.
B: Only Rational{BigInt} certificate replaces unit-orientation multiplication by a read-only rho value for +1 or ordinary unary negation for -1. Each remaining matrix multiply and accumulation stays in original CSC order. Slack sign, all zero comparisons/allowances/bound checks and exception handling remain. No oriented-rho array, extra pass, writable shared scalar or fixed-width rational change. Measure complete certificate in both orientations, finite/one-sided/zero-tolerance and invalid controls.
C: Only BigFloat PFI growth measurement uses one fresh invocation-local immutable binding to a read-only unit across original nested maxima and the already qualified conditional magnitude. Retain reduction order, output value/precision/owner category, NaN/Inf/ties, factor arrays and update-chain lifetime. Measure full growth function, forced metric refresh (including original storage scans/recovery precision) and scheduled reason including existing cache/age gates. No new cross-call cache or trigger changes.
Alternatives rejected for this task: oriented-rho vectors/persistent growth caches move work or add lifetime invalidation; unit-multiplication removal in BigFloat can change rounding and is excluded. Original scalar/array ownership requirements and native/fixed-rational paths remain.
''')
(D/'PLAN.md').write_text('''# Sum, Rational Certificate and PFI Growth Implementation Plan

> For agentic workers: use superpowers:executing-plans inline; preserve this case ledger and all earlier evidence.

**Goal:** Measure all three approved private candidates and autonomously integrate only independently accepted variants.
**Architecture:** Exact private Reference/A/B/C fragments, ordinary Test and fixed paired whole-call measurements, then original RED before production staging. Reuse the existing diagnostics worktree; actual master ce5d4a74 is the baseline, never its stale src directory.
**Tech Stack:** Julia1.13 installed runtime, standard Test/@timed/TOML, existing guarded single-process launcher; no dependencies or CI changes.
**Spec:** DESIGN.md in this directory and the direct human request.

## Global constraints
Preserve user files/env/indexes/worktrees and frozen older artifacts. New host refs+boot+start_ticks+command+full649groups ANDsessions/noJulia first, exact unrelated WSL identity-only allowance. One Julia/BLAS1, GC1,0, heap2GiB/AS8GiB, availableRAM6GiB/swap1GiB, compiled-modules existing. No huge LP, tolerance/precision increases or safeguard removal; ordinary tests, no custom recorder/manual Test stacks. CIoff/automationpaused/HHreuse disabled; broader/fullsuite/x64/native-retention OPEN.

## Review focus
Same-sign, opposite-sign exact cancellation and signedzero/NaN/Inf; stored512/ambient64/128/256 under all five rounding modes; exact-rational ±Inf/zero DivideError and fixed-width overflow; fresh-vs-input scalar owner patterns through maxima ties/empty updates; real refactor state/precision restoration and scheduled cache/age/priority gates. Each has an ordinary behavioral assertion, independent exact-dyadic or hand-derived outcome where applicable, and input snapshots.

## Task1: short comparison
- [ ] Prepare private source fragments with exact inverse and no imported owned definitions, plus complete function fixtures/tests and source work ledger.
- [ ] Seal exact fixed cases/3warm+9alternating pairs/compilezero/fixture-view-reset-cold-warm-validation-GC preparation. Sparse/dense, positive/negative/mixed and native/exact controls; B RationalBigInt small+wide numerators.
- [ ] Independently review concrete manifest/driver/guard and numerical/work/memory scope before one guarded900s process. Expected: complete ordinary tests and all frozen windows; preserve all GC/outliers and rejected records. No tuning/repeat-to-pass; timeout-only needs separately reviewed longer concrete allowance.
- [ ] Audit raw command/source/types/grid/outputs/context/resources/pins and independently decide A/B/C by whole-call correctness and cost, not inner helper only.

## Task2: accepted production only
- [ ] Ordinary permanent correctness and fixed3pair lowerEvents/lowerMedianBytes gates; observe expected original allocation RED before staging production.
- [ ] Exact source inverse/old tests unchanged; fresh whole-production numerical/work/memory review. GREEN existing51wholefiles+new regression+refactor affected wholefiles as needed, shared3000s (recent51 required1929s). No old exception or threshold weakening.
- [ ] Private-index commit, independent actual-commit check, ff-only local integration, freshly admitted same-files/frozen-total actualMASTER3000s, independent result, normal nonforce push/remote verification.

## Task3: closure/publication
- [ ] Fresh complete noJulia host, exact old continuation bytes/maps, final report+independent review. Separate PASS closure and exact staged/committed names/blobs before failfast diagnostics commit/push/remote verification. Preserve all old and current failed evidence. No automatic next experiment or cleanup.
''')
(D/'WORK-MEMORY.md').write_text('''# Work and memory budget
A adds at most two signbit loads/comparison at an existing reached cancellation gate, removes one unused BigFloat negation per eligible same-sign nonzero sum. Same CSC scans, products/additions/enclosure checks and output ownership; O(1) local state, no new buffers/caches.
B removes one GMP rational unit multiplication per reached matrix nonzero and substitutes unary negation only for negative orientation; slack ±unit arithmetic also becomes direct sign selection. Same remaining products/sums, bound/tolerance/allowance work and input reads, no O(m) oriented vector or extra pass. Boolean output exposes no coefficient temporary; exact BigInt owners are read-only. Fixed-width rationals unchanged.
C changes L+1 fresh unit constructors to one per call and removes discarded positive-value negations over P packed entries. The two nested maximum reductions remain O(L+P), same order/inputs, one captured read-only seed whose closure cost is included in whole-call measurements. All storage-count, recovery-precision scans and age/trigger rules remain; no retained numerical memory or cross-call cache. Active adaptive metrics are normally refreshed at age1/every8/nearinterval, not every ordinary legacy iteration; fixed rational policy skips this growth calculation.
Cold specialization metadata is additional; exact method count and any closure allocations are reviewed against concrete fragments before production. Constructor counts are source work only, not allocation measurements/native memory or end-to-end speedup evidence.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1: baseline541files and fresh649groups verified; private candidates and design/plan/work ledger prepared, noJulia.\nRuling: reuse existing isolated diagnostics checkout and private snapshots; preserve all workspaces instead of cleanup under standing user instruction. Baseline testing will be this newly admitted ordinary comparison/originalRED, not reruns of frozen old scripts.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('private SRG Reference/A/B/C prepared; noJulia')
