using JSimplex, Test
const ROOT = dirname(dirname(pathof(JSimplex)))
for name in ("triangular_fused_solve_tests.jl", "triangular_incremental_metadata_tests.jl", "triangular_selective_preparation_tests.jl")
    include(joinpath(ROOT,"test",name))
end
include(joinpath(ROOT,"diagnostics","basis-overhead","reproduce","verify-triangular.jl"))
