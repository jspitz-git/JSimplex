using JSimplex,Test,Logging
@testset "Legacy primal retry pricing and numerical guards" begin
    for file in ("primal_retry_pricing_tests.jl","primal_candidate_retry_tests.jl",
                 "legacy_primal_pivot_row_tests.jl","legacy_primal_point_tests.jl",
                 "legacy_harris_feasibility_tests.jl","legacy_retry_edge_tests.jl",
                 "primal_simplex_tests.jl","postsolve_cleanup_performance_tests.jl")
        println("FILE ",file);flush(stdout)
        include(joinpath(pwd(),"test",file))
    end
end
