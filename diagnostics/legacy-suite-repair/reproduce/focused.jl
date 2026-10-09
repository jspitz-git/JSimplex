using JSimplex,Test,SparseArrays,LinearAlgebra
@testset "Legacy fixture contracts and adjacent safeguards" begin
 for file in ("primal_bound_snap_tests.jl","primal_candidate_retry_tests.jl","primal_retry_pricing_tests.jl", "legacy_primal_row_value_tests.jl", "legacy_primal_structural_value_tests.jl", "legacy_primal_point_tests.jl", "legacy_primal_point_recovery_tests.jl", "legacy_primal_direction_price_tests.jl", "legacy_primal_correlated_pivot_tests.jl", "legacy_primal_roundoff_pivot_tests.jl")
  include(joinpath(dirname(dirname(pathof(JSimplex))),"test",file))
 end
end
