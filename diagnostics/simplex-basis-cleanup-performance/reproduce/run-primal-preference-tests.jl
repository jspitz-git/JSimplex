using JSimplex,Test,Logging
@testset "Legacy primal candidate preference and retry guards" begin
    for file in ("legacy_primal_roundoff_pivot_tests.jl","legacy_primal_pivot_preference_tests.jl","legacy_primal_preference_work_tests.jl","primal_retry_pricing_tests.jl",
                 "primal_candidate_retry_tests.jl","legacy_primal_pivot_row_tests.jl",
                 "legacy_primal_point_tests.jl","legacy_harris_feasibility_tests.jl",
                 "legacy_retry_edge_tests.jl")
        println("FILE ",file);flush(stdout)
        include(joinpath(pwd(),"test",file))
    end
end
