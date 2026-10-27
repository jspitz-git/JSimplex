using Test,JSimplex,LinearAlgebra
const ROOT="/home/jspitz/.codex/worktrees/simplex-core-architecture/JSimplex.jl/diagnostics/generic-ratio-monitor/2026-10-27/GREEN"
@assert realpath(pathof(JSimplex))==realpath(joinpath(ROOT,"src/JSimplex.jl"))
@assert Base.active_project()==joinpath(ROOT,"Project.toml")
BLAS.set_num_threads(1)
@assert Threads.nthreads()==BLAS.get_num_threads()==1
println("RATIO_MONITOR_SOURCE ",pathof(JSimplex));flush(stdout)
@testset "Ratio monitor GREEN" begin
 for file in ["generic_ratio_monitor_tests.jl", "generic_interval_stagnation_devex_tests.jl", "generic_stagnation_unit_seed_tests.jl", "generic_virtual_free_pivot_tests.jl", "generic_quality_local_tests.jl", "generic_quality_devex_tests.jl", "generic_residual_magnitudes_tests.jl", "generic_pivot_scalars_tests.jl", "generic_dual_comparisons_tests.jl", "generic_weight_constants_tests.jl", "generic_primal_threshold_tests.jl", "generic_scalar_branches_tests.jl", "generic_local_reuse_tests.jl", "generic_unit_cost_tests.jl", "simplex_workspace_tests.jl", "solver_tests.jl", "numeric_type_tests.jl", "primal_feasibility_predicate_tests.jl", "primal_bound_snap_tests.jl", "exact_primal_rows_tests.jl", "primal_certificate_work_tests.jl", "native_basic_stationarity_tests.jl", "dual_simplex_tests.jl", "dual_ratio_tests.jl", "dual_bfrt_tie_tests.jl", "native_dual_tableau_tests.jl", "solver_policy_precision_tests.jl", "numeric_tests.jl", "dual_weight_validation_tests.jl", "generic_pricing_scalar_tests.jl", "adaptive_pricing_tests.jl", "adaptive_pricing_integration_tests.jl", "adaptive_pricing_lifecycle_tests.jl", "partial_pricing_option_tests.jl", "partial_pricing_tests.jl", "partial_pricing_integration_tests.jl", "partial_pricing_edge_tests.jl", "simplex_numerics_tests.jl", "primal_simplex_tests.jl", "stagnation_threshold_tests.jl", "simplex_stalling_tests.jl", "simplex_stalling_integration_tests.jl", "simplex_stalling_edge_tests.jl", "adaptive_progress_metric_tests.jl", "dual_stagnation_cost_tests.jl", "adaptive_intervention_order_tests.jl", "generic_pool_bound_tests.jl", "native_complementarity_rows_tests.jl", "native_certificate_recovery_tests.jl", "simplex_precision_state_tests.jl"]
  println("INCLUDING ",file);flush(stdout)
  include(joinpath(ROOT,"test",file))
 end
end
println("RATIO_MONITOR_COMPLETED GREEN");flush(stdout)
