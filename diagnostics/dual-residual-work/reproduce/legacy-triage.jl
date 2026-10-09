using JSimplex,Test,SparseArrays,LinearAlgebra
@testset "Legacy full-suite failure triage" begin
 for file in ("primal_bound_snap_tests.jl","primal_candidate_retry_tests.jl","primal_retry_pricing_tests.jl")
  include(joinpath(dirname(dirname(pathof(JSimplex))),"test",file))
 end
end
