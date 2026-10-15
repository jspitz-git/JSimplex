"""One-time source/design evidence; no runtime/module execution."""
from common import *
source_names=['src/options.jl','src/factorization.jl','src/triangular_factorization.jl','src/simplex_recovery.jl','src/simplex_phase_one.jl','src/simplex_precision.jl','src/solver.jl','src/lp_refinement_driver.jl','src/numeric.jl','src/JSimplex.jl','src/moi/attributes.jl','src/markowitz_factorization.jl','src/hypersparse_factorization.jl','src/huangfu_hall_factorization.jl','test/options_tests.jl','test/dual_simplex_tests.jl','test/hypersparse_factorization_edge_tests.jl','diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl','diagnostics/direct-lu-markowitz/reproduce/factor-export.jl']
installed=Path('/home/jspitz/.julia/juliaup/julia-1.13.0+0.aarch64.linux.gnu/share/julia/stdlib/v1.13/SparseArrays/src/solvers/umfpack.jl')
anchors={
'src/options.jl':['struct SolverOptions{','function _validated_options(','SolverOptions(::Type{T}, options::'],
'src/factorization.jl':['mutable struct UMFPACKBackend','candidate = lu(sparse_basis)','function _copy_backend(backend::UMFPACKBackend)','_basis_factorization(B, ::SolverOptions'],
'src/triangular_factorization.jl':['function ForrestTomlinFactorization(','function SuhlSuhlFactorization(','function BartelsGolubFactorization(','new_base = _refactorize_backend(factor.base, B)'],
'src/simplex_recovery.jl':['_basis_factorization(B,ws.options)'],
'src/simplex_phase_one.jl':['function _phase_options('],
'src/simplex_precision.jl':['function _copy_precision_options(','_basis_factorization(B,options)'],
'src/solver.jl':['function _remaining_options('],
'src/lp_refinement_driver.jl':['function _lp_auxiliary_options('],
'diagnostics/direct-lu-markowitz/reproduce/direct-factor.jl':['struct DirectLowerBackend','ordinary=_factorize_basis(B,backend)','normalize=f.base.normalize_requested']}
locations={}
for n,needles in anchors.items():
 lines=(R/n).read_text().splitlines();locations[n]={}
 for a in needles:
  loc=[i+1 for i,line in enumerate(lines) if a in line];require(len(loc)==1,'Ambiguous/missing anchor '+n+' '+a);locations[n][a]=loc[0]
checks=dict(exact_source_anchors=True,default_fresh_lu='candidate = lu(sparse_basis)' in (R/'src/factorization.jl').read_text(),copy_shares_active='UMFPACKBackend(backend.factorization, backend.dimension, nothing, true)' in (R/'src/factorization.jl').read_text(),installed_controls_copied='copy(control), Vector{Float64}' in installed.read_text(),installed_spare_controls_persist='resize!(F.workspace, S, has_refinement(F))' in installed.read_text(),old_cost_false=rd(Q.parent/'DIRECT-LU-COST-PREPARATION/cost1-audit.json')['all_passed'] is False,baseline514=bindings(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')) and len(rd(Q.parent/'DIRECT-LU-PREPARATION/baseline.json')['sha256'])==514,no_new_stage=not (Q.parent/'NATIVE-PIVOT-PREPARATION').exists())
paths=[R/n for n in source_names]+[installed,R/'AGENTS.md',R/'docs/superpowers/specs/2026-10-15-native-pivot-policy-design.md',R/'docs/superpowers/plans/2026-10-15-native-pivot-policy.md',R/'diagnostics/simplex-core-architecture/NATIVE-ACCURACY-QUALIFICATION.md',PREV/'result-review.md',PREV/'result-review.json',PREV/'accuracy-audit.json',PREV/'summary.json',PREV/'closure.json',PREV/'publication.json',Q/'entry.py',Q/'entry.json',Q/'host.json',Q/'common.py',Path(__file__)]
save(Q/'source-evidence.json',dict(all_passed=all(checks.values()),checks=checks,locations=locations,sha256={str(p):sha(p) for p in paths},scope='New source-read hashes and design bindings only, not launch pins or runtime qualification; old numerical results read only'))
require(all(checks.values()),'Source evidence failed; preserve');print(dict(all_passed=True,checks=len(checks),hashes=len(paths)))
