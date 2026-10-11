using Test, JSimplex
root = dirname(dirname(pathof(JSimplex)))
for file in ("hh_dimension_scratch_tests.jl", "huangfu_hall_tests.jl",
             "huangfu_hall_precision_tests.jl", "huangfu_hall_markowitz_tests.jl",
             "huangfu_hall_scalar_integration_tests.jl", "huangfu_hall_integration_tests.jl")
    println("Starting ", file); flush(stdout)
    include(joinpath(root, "test", file))
end
