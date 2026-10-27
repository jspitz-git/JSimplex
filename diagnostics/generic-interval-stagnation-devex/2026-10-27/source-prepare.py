from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-interval-stagnation-devex/2026-10-27');sys.path.insert(0,str(D));import common as c
M=c.M
P=(M/'src/primal_simplex.jl').read_text();S=(M/'src/simplex_stalling.jl').read_text();X=(M/'src/simplex.jl').read_text();U=(M/'src/dual_simplex.jl').read_text()
def section(s,a,b):c.need(s.count(a)==1 and s.count(b)==1,'unique exact source markers');return s[s.index(a):s.index(b)]
a1=section(U,'function _primal_sum_bounds(left::BigFloat','\n\n_primal_difference_bounds(')
a2=section(U,'function _primal_product_bounds(left::BigFloat','\n\nfunction _primal_product_bounds(left::T, right::T) where {T<:Rational}')
na1=a1.replace('abs(left), abs(right)','_primal_direction_magnitude(left), _primal_direction_magnitude(right)');na2=a2.replace('abs(value) >=','_primal_direction_magnitude(value) >=');c.need(na1!=a1 and na2!=a2,'two narrow magnitude edits')
new0=section(S,'function _new_workspace_stagnation(ws,key,algorithm)','\nfunction _workspace_stagnation_values(ws,state::WorkspaceStagnation{T,S}')
newb=new0.replace('function _new_workspace_stagnation(ws,key,algorithm)','function _new_workspace_stagnation(ws::SimplexWorkspace{BigFloat},key,algorithm)').replace('abs(S(value))','_primal_direction_magnitude(S(value))').replace('abs(S(bound_value(bound)))','_primal_direction_magnitude(S(bound_value(bound)))')
reb=section(S,'function _rebase_dual_stagnation_costs!(ws,state::WorkspaceStagnation{T,S},key)','\nfunction _observe_workspace_stagnation!')
rebn=reb.replace('function _rebase_dual_stagnation_costs!(ws,state::WorkspaceStagnation{T,S},key) where {T,S}','function _rebase_dual_stagnation_costs!(ws::SimplexWorkspace{BigFloat},state::WorkspaceStagnation{BigFloat,BigFloat},key)\n    S = BigFloat').replace('abs(S(x))','_primal_direction_magnitude(S(x))')
newb=newb.rstrip()+'\n\n'+rebn.rstrip()+'\n'
cnew='''function _primal_devex_leaving_weight(weight::BigFloat,pivot::BigFloat)
    unit = one(BigFloat)
    quotient = weight / _primal_direction_magnitude(pivot)
    clipped = isinf(quotient) && !signbit(quotient) ? floatmax(BigFloat) : quotient
    return max(unit,clipped)
end
'''
changes=[dict(variant='A',file='src/dual_simplex.jl',old=a1,new=na1),dict(variant='A',file='src/dual_simplex.jl',old=a2,new=na2),dict(variant='B',file='src/simplex.jl',old=X,new=X.rstrip()+'\n\n'+newb),dict(variant='C',file='src/primal_simplex.jl',old='_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:AbstractFloat} =\n    max(one(T), min(floatmax(T), weight / abs(pivot)))\n',new='_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:AbstractFloat} =\n    max(one(T), min(floatmax(T), weight / abs(pivot)))\n\n'+cnew)]
c.need(c.read('changes.json')==changes,'preserved exact changes')
# Exact source fragments, no changed methods in JSimplex and no core-type cloning.
cert=section(U,'function _primal_sum_bounds(left::T, right::T) where {T<:Rational}','_refined_primal_rows_feasible(::LinearProblem, ::Vector, tolerance, rows) = false')+section(U,'function _primal_feasible_with_bounds(problem::LinearProblem','function _original_dual_witness(')+section(U,'function _original_witness_certified(problem::LinearProblem','function _original_optimality_certified(')
monitor=section(S,'_stagnation_price_step(price,pivot)','function StagnationMonitor{T}')
metric=X[X.index('function _workspace_stagnation_values(ws::SimplexWorkspace{BigFloat}'):]
weights=section(P,'_primal_devex_leaving_weight(weight::T, pivot::T) where {T<:AbstractFloat}','function _primal_steepest_weight!')
devex=section(P,'function _primal_update_devex!(workspace::SimplexWorkspace{T}','\n_primal_relaxed_step(raw_step::T, tolerance::T, movement::T) where {T<:AbstractFloat}')
imports='''using JSimplex,SparseArrays,LinearAlgebra
using JSimplex: SimplexWorkspace,WorkspaceStagnation,StagnationMonitor,VariableState,
 BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,Bound,Basis,LinearProblem,SolverOptions,
 _is_fixed,bound_value,_primal_direction_magnitude,_finite_workspace,_with_recovery_precision,
 observe_progress!,reset_stagnation!,_simplex_event!,_is_exact,_primal_nearest_rounding,
 _refined_primal_rows_feasible,_native_basic_certificate_mode,_native_basic_column_interval,
 _native_basic_intersection,_pipeline_unit_rhs!,_checked_basis_solve!,price!
'''
for arm in ['Reference','A','B','C']:
 body=cert+monitor+metric+'\n'+weights+devex
 if arm=='A':
  for old,new in [(a1,na1),(a2,na2)]:c.need(body.count(old)==1,'one A clone inverse');body=body.replace(old,new)
 if arm=='B':body+='\n'+newb
 if arm=='C':body+='\n'+cnew
 (D/(arm+'.jl')).write_text('module ISD'+arm+'\n'+imports+body.rstrip()+'\nend\n')
c.put('source-clones.json',dict(fragments=dict(certification=cert,monitor=monitor,metric=metric,weights=weights,devex=devex),module_names=['ISDReference','ISDA','ISDB','ISDC'],no_JSimplex_method_overwrite=True,late_concrete_B_definition='src/simplex.jl EOF after SimplexWorkspace, before final precompile include'))
(D/'PLAN.md').write_text('''# Interval, stagnation setup and Devex scalar savings

Spec: human explicitly selects all3 whole-function correctness/time/bytes/events comparisons and autonomous usual integration of accepted variants. Authoritative master3d3787b2, linked diagnostics worktree reused; R/src stale. Authorized private exact-source namespace spikes first; production candidate only after witnessed ordinary RED. Preserve source/userenv/indexes/oldworktrees and all frozen raw/scripts/reviews. CIoff, automationpaused, HHreuse disabled, broader/fullsuite/x64/native-retention OPEN. No old HH/controller/import/DSE/cleanup route reopened.

A: only existing BigFloat interval sum/product specialized magnitude sites; conditional helper retains original guard/negative rounding/product/FMA/FastTwoSum/underflow/enclosure/zero-unit aliases. Up to2 unused nonnegative negations per reached sum, up to1 per reached product fallback guard. Same sparse/dense row/reduced-cost and full original witness certification scans and native/exact fallback. No changed tolerance/precision/arithorder/pivot.
B: concrete BF workspace new-monitor and cost-rebase specializations use conditional magnitude AFTER original S(value) conversion. Generic/arbitraryworkspace/native/exact routes retained; define new concrete signatures only after actual workspace type exists. One discarded negation per eligible nonnegative cost/primal/finite-bound value. All cost/context/finite/scaling/history/event/callback work retained, especially no metric reuse across rebase event. Measure whole setup, cold observer and real dual rebase observer. Same positive converted scalar owner, negative arithmetic, fresh monitor identity and ordinary within-call sharing.
C: BF leaving Devex only: fresh original unit first, same division and conditional pivot magnitude; create upper cap only at positive infinite quotient; retain max(unit,clipped) and all NaN/zero/sign/underflow/overflow/precision/owner behavior. Other types unchanged. Measure complete helper AND complete update with shared row and actual BTRAN+price, all loops/cache/output owners unchanged. No shared mutable constants.

Task1 prepare reference/A/B/C private fragments, strict bit/precision/sign/alias/exception/context/callback controls and independent exact enclosure/witness oracles. BF64/128/256xfive modes plus stored512/extremes and Float32/64/RationalBigInt/Int64 controls. Sparse/dense n16/64,m8/16, signpositive/negative/mixed. Fixed3warm+9alternatingpairs; all compilationzero required, retain everyGC/outlier. Record fixture/reset/snapshot/cold/warm/validation/GC preparation separately; no custom Test recorder/manual stack, plain finally raw publication. One independently admitted600s guarded measurement; proven harness-only failure may get separate corrected preparation, never oldrerun or tuning.
Task2 independent per-variant measured acceptance, permanent ordinary regression with data-supported allocation gates, witness originalRED before production-stage source edits. Stage only accepted variants; exact inverse and whole-branch independent review plus concrete GREEN admission. Same45affected oldwholefiles +newtest and required certification/precision coverage; freeze ordered files before launch.2400s or separately justified larger test limit, oneJulia and existing guards. Do not weaken old tests/thresholds or reuse historical exceptions. No duplicate runtime merely to write a ledger.
Task3 reviewed exactprivateindexcommit/localff/freshsamefiles/countactualMASTER/independentresult/normalnonforcepush+remoteverify, then freshhost/exactcontinuationbeforebytes/maps, independently reviewed final report, separatePASSclosure and exactall staged/committedblobs beforefailfast DIpublication. No permission menu/cleanup/automatic newexperiment. Fresh full619groups ANDsessions/boot/startticks/command/noJulia before everylaunch and continuation edit; exact old unrelatedWSLidentity-only allowance, no PIDalone. Julia/BLAS1,GC1,0,AS8GiB,heap2GiB,RAM6GiB/swap1GiB,compiledmodulesexisting. O(1) local scalar/flag and cold method metadata only; no newscan/solve/copy/conversion/cache. Source counts are not allocation/native-memory measurements.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1 preparation. Human chose all3 comparisons and autonomous integration.\nRuling: private exact stages reuse existing isolation and targeted wholefile suite; preserve olduserworktrees/evidence and no fullsuite/cleanup/menu, no duplicate numerics for bookkeeping.\nPre-flight: A,B,C independent; B concrete signatures deliberately live after type definition; source clones load after realJ, production include graph independently checked. No change before originalRED beyond explicitly authorized private measurement spikes.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('four private exact-source modules; noJulia/productionstage')
