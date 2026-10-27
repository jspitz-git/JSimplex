from pathlib import Path
import sys,json,shutil
D=Path('/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-bounds-norm-infeasibility/2026-10-27');sys.path.insert(0,str(D));import common as c
c.put('source-host.json',c.host())
p=(D/'baseline/src/primal_simplex.jl').read_text();du=(D/'baseline/src/dual_simplex.jl').read_text()
def reg(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
norm=reg(p,'function _primal_direction_weight(direction::AbstractVector{T})','function _primal_weighted_score')
normbf=reg(p,'function _primal_direction_weight(direction::AbstractVector{T})','function _primal_direction_weight(direction::AbstractVector{T}) where {T<:Rational}')
normbf=normbf.replace('direction::AbstractVector{T}) where {T<:AbstractFloat}','direction::AbstractVector{BigFloat})\n    T = BigFloat')
normbf=normbf.replace('stored_weight = min(floatmax(T), scale * factor)','product = scale * factor\n    stored_weight = isinf(product) && !signbit(product) ? floatmax(BigFloat) : product')
steep=reg(p,'function _primal_steepest_weight!','_primal_cacheable_weight(weight::T)')
init=reg(p,'function _primal_initialize_steepest!','function _primal_updated_weight')
bounds=reg(p,'function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}','function _primal_ratio(workspace::SimplexWorkspace{T}')
snapbf=reg(p,'function _primal_bound_snap_feasible(workspace::SimplexWorkspace{BigFloat}','function _primal_step_bounds_feasible')
snapgen=reg(p,'function _primal_bound_snap_feasible(workspace::SimplexWorkspace{T}','function _primal_bound_snap_feasible(workspace::SimplexWorkspace{BigFloat}')
step=reg(p,'function _primal_step_bounds_feasible(workspace::SimplexWorkspace{T}','function _primal_ratio(workspace::SimplexWorkspace{T}')
helper='''# Invocation-private comparison zero is read-only and never published by these Boolean guards.
_primal_bound_lower_violation(bound::Bound{T},value::T,z::T) where T =
    isfinite(bound) ? bound_value(bound)-value : z
_primal_bound_upper_violation(bound::Bound{T},value::T,z::T) where T =
    isfinite(bound) ? value-bound_value(bound) : z

'''
def zero_reuse(s,snap):
 for x in ['entering','index']:
  s=s.replace('_lower_violation(workspace.lower['+x+'], value)','_primal_bound_lower_violation(workspace.lower['+x+'], value, comparison_zero)')
  s=s.replace('_upper_violation(workspace.upper['+x+'], value)','_primal_bound_upper_violation(workspace.upper['+x+'], value, comparison_zero)')
 s=s.replace('max(zero(T),','max(comparison_zero,')
 if snap:s=s.replace('    violation = max(comparison_zero,','    comparison_zero = zero(T)\n    violation = max(comparison_zero,',1)
 else:
  s=s.replace('    tolerance = workspace.options.primal_tolerance','    tolerance = workspace.options.primal_tolerance\n    comparison_zero = nothing',1)
  s=s.replace('        violation = max(comparison_zero,','        if isnothing(comparison_zero)\n            comparison_zero = zero(T)\n        end\n        violation = max(comparison_zero,',1)
 return s
newsnapbf=zero_reuse(snapbf,True)
snaprat=snapgen.replace('workspace::SimplexWorkspace{T},','workspace::SimplexWorkspace{Rational{BigInt}},',1).replace('direction::T, column::Vector{T}, leaving_row::Int) where {T}','direction::Rational{BigInt}, column::Vector{Rational{BigInt}}, leaving_row::Int)\n    T = Rational{BigInt}',1)
newsnaprat=zero_reuse(snaprat,True)
newstep=zero_reuse(step.replace('where {T}','where {T<:Union{BigFloat,Rational{BigInt}}}',1),False)
newbounds=bounds.replace(snapbf,newsnapbf)+newsnaprat+newstep
ratio=reg(p,'function _primal_ratio(workspace::SimplexWorkspace{T}','function _legacy_primal_iteration!')
cert=reg(du,'function _floating_infeasibility_certified','function _dual_direction_residual_ok!')
certbf=cert.replace('workspace::SimplexWorkspace{T},','workspace::SimplexWorkspace{BigFloat},',1).replace('rho::Vector{T}, below::Bool) where {T<:AbstractFloat}','rho::Vector{BigFloat}, below::Bool)\n    T = BigFloat',1)
certbf=certbf.replace('coefficient_upper > zero(T)','coefficient_upper > 0').replace('coefficient_lower < zero(T)','coefficient_lower < 0').replace('minimum_value > zero(T)','minimum_value > 0').replace('max(abs(coefficient_lower),abs(coefficient_upper))','max(_primal_direction_magnitude(coefficient_lower),_primal_direction_magnitude(coefficient_upper))')
imports='''using JSimplex: SimplexWorkspace,Bound,BASIC,AT_LOWER,AT_UPPER,FREE_NONBASIC,bound_value,_lower_violation,_upper_violation,_can_preserve_primal_bound_value,_primal_relaxed_step,_legacy_primal_row_validation_enabled,_primal_direction_magnitude,_primal_nonnegative_step,_pipeline_column_rhs!,_checked_basis_solve!,_primal_cacheable_weight,_primal_unit_basis,_add_product_bounds,_infeasibility_bound_allowance
'''
wrapper='''_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:AbstractFloat} = _floating_infeasibility_certified(w,rho,below)
_infeasibility_certified(w::SimplexWorkspace{T},rho::Vector{T},below::Bool) where {T<:Rational} = JSimplex._infeasibility_certified(w,rho,below)
'''
for arm in ['Reference','A','B','C']:
 body=(helper+newbounds if arm=='A' else bounds)+ratio+norm+(normbf if arm=='B' else '')+steep+init+cert+(certbf if arm=='C' else '')+wrapper
 (D/(arm+'.jl')).write_text('module BNI'+arm+'\nimport JSimplex\n'+imports+body+'\nend\n')
changes=[dict(variant='A',file='src/primal_simplex.jl',old=bounds,new=helper+newbounds),dict(variant='B',file='src/primal_simplex.jl',old=norm,new=norm+normbf),dict(variant='C',file='src/dual_simplex.jl',old=cert,new=cert+certbf)]
c.put('changes.json',changes);c.put('source-clones.json',{a:c.sha(D/(a+'.jl')) for a in ['Reference','A','B','C']})
O=D.parents[1]/'generic-ratio-monitor/2026-10-27';shutil.copytree(O/'guard',D/'guard',ignore=shutil.ignore_patterns('__pycache__'));(D/'launch.py').write_text((O/'launch.py').read_text())
(D/'PLAN.md').write_text('''# Bounds comparison zero, direction cap and infeasibility scalars
Human-selected three short whole-function correctness/time/bytes/events comparisons and autonomous usual integration of accepted variants. Baseline9d29b1f0; existing linked diagnostics worktree reused, R/src notbaseline. Fresh637groups ANDsessions/boot/startticks/command/noJulia beforelaunch/continuation edits, fixed unrelatedWSL identity allowance. Preserve userfiles/indexes/oldworktrees/raw/scripts/rejections. CIoff/automationpaused/HHdisabled/broaderfullsuite/x64/native-retentionOPEN.
A invocation-private readonly comparisonzero in BigFloat/RationalBigInt Boolean bound-snap/final-step guards, including unbounded-side zeros. Firstzero at original firstreachedmax site after same finite/earlyreturn gates; lazy in step loop for empty/nonfinite paths. Same lower-read/subtraction then upper-read/subtraction evaluation order, comparisons/arithmetic/rowpasses/ties/guards. No zero published/shared acrosscalls, no callbacks/precision changes inside guarded loops. Othertypes originalmethods.
B BigFloat directionnorm cap only on positiveinfinite product. Same two norm passes, unit/inv/squares/sqrt/frexp/product order retained apartfrom omitted earlier unusedcap constructor. Base min chooses product on finite tie,NaN,-Inf andfinite products; current-precision product fits currentfloatmax. Overflow cap remainsfresh percall; tuple/scalar outputprecision/owner/signedzero andeverycacheabilitycheck unchanged. Measure norm+whole steepestinitialization+genuinecheckedFTRAN maintenance, includingexistingviews andallprep.
C BigFloat-only floatinginfeasibility certificate uses exact integerzero only at three comparison sites andconditionalmagnitudes only at existing penalty endpoints. Coefficient/accumulator freshzeros,add_product_bounds,allprevfloat/nextfloat,enclosures,multiplication/sums,allowance,tolerance,finiteness,unbounded/sign rejection unchanged. Rational/native routes original. Measure complete dispatch+certificate, valid/invalidwitnesses andfinite/one-sided/zeroallowance controls, bothorientations.
Private exact Reference/A/B/C fragments first, no Base/J method overwrite. Ordinary Test only/no customrecorder/manualstacks. BF64/128/256xfive modes, stored512/extreme/signedzero/NaNInf/empty/dimension/partialstate/owner/input/context checks; nativeFloat32/64/RationalBigInt/Int64 controls. Sparse/dense16/64, threewarm+9alternatingpairs, everymeasuredcompile/recompile0, preserveallGC/outliers. Fixture/reset/snapshot/cold/warm/GC/preparation costs separatelyretained. One independentlyadmitted600s process withusualJulia/BLAS1GC1,0 heap2GiB/AS8GiB RAM6GiB/swap1GiB compiledexisting; no longLP.
Independent pervariantcost/resultadmission, ordinary newpermanentcorrectness+fixed3pair lowerEvents/lowerMedianBytes gates on benefitingwholepaths; originalRED witnessed beforeproductionstage. Same existing50wholefiles+newregression/affectedfile additions,3000s sharedGREEN/actualMASTER justified last50~1935s; no oldtest/threshold weakening/oldreleaseexceptionreuse. Wholebranch independentnumerical/workmemoryreview, exactprivateindexcommit/actualcommitreview/localff/freshsamefiles+totalMASTER/normalnonforcepush/remoteverify. Finalreport+exactbeforeimages/maps+independentfinalreview/separatePASSclosure/exactallstagedcommittednames/blobsDIpublication. No newscan/solve/copy/conversion/cache;O(1)locals/readiness tests+coldmethodmetadata. Sourceconstructorcounts not measuredallocations/nativefree/live-memoryproof. Noautomaticnexttask/cleanup/automationresume.
''')
(D/'progress.md').write_text('# SDD ledger — plan: '+str(D/'PLAN.md')+'\nTask1: private candidates/sourcebudget prepared; noJulia.\nPre-flight: A modifies bounds region; B norm region; C certificate region, no overlapping source replacements. Fullratio consumes A, initializer/FTRAN consumes B; completecertdispatch consumes C.\n')
shutil.copyfile(__file__,D/'source-prepare.py');print('privateA/B/C andexactReference prepared')
