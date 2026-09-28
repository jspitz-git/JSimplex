using JSimplex, Test
const ROOT = dirname(dirname(pathof(JSimplex)))
include(joinpath(ROOT,"test","triangular_selective_preparation_tests.jl"))
include(joinpath(ROOT,"test","triangular_preparation_lifecycle_tests.jl"))
include(joinpath(ROOT,"diagnostics","basis-overhead","reproduce","verify-triangular.jl"))
for name in ("hypersparse_pipeline_tests.jl", "hypersparse_pipeline_storage_tests.jl",
             "hypersparse_pipeline_solver_tests.jl", "hypersparse_pipeline_accounting_tests.jl")
    include(joinpath(ROOT,"test",name))
end
