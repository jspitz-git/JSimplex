using Test,JSimplex
@testset "Project failure attribution" begin
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","legacy_primal_preference_work_tests.jl"))
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","primal_bound_snap_tests.jl"))
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","primal_candidate_retry_tests.jl"))
include(joinpath(dirname(dirname(pathof(JSimplex))),"test","primal_retry_pricing_tests.jl"))
end
