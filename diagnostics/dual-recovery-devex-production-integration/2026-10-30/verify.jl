using JSimplex,Test,LinearAlgebra,SparseArrays,Logging
const DEVEX_MASTER_ROOT="/home/jspitz/JSimplex.jl"
@assert realpath(pathof(JSimplex))==realpath(joinpath(DEVEX_MASTER_ROOT,"src","JSimplex.jl"))
@testset "DEVEX_PRODUCTION_MASTER" begin
    include(joinpath(DEVEX_MASTER_ROOT,"test","refinement_outcome_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","refinement_reference_comparison_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","recovery_weight_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","recovery_devex_fallback_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","recovery_devex_pivot_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","simplex_numerics_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","basis_recovery_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","dual_weight_validation_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","adaptive_pricing_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","adaptive_pricing_lifecycle_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","partial_pricing_tests.jl"))
    include(joinpath(DEVEX_MASTER_ROOT,"test","partial_pricing_edge_tests.jl"))
end
println("DEVEX_PRODUCTION_MASTER_COMPLETED")
