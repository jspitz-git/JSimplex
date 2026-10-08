using Test, JSimplex, SparseArrays, LinearAlgebra, Logging
@testset "Postsolve box integration regressions" begin
    for file in ("postsolve_box_hint_tests.jl", "postsolve_hint_tests.jl",
                 "postsolve_native_projection_tests.jl", "postsolve_cleanup_performance_tests.jl",
                 "presolve_tests.jl")
        include(joinpath(dirname(dirname(pathof(JSimplex))), "test", file))
    end
end
