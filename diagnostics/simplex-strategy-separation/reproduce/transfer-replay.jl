using Test, JSimplex
@testset "Separated policy transfer and replay" begin
    for name in ("simplex_strategy_separation", "simplex_phase_one_state", "simplex_precision")
        include(joinpath(pwd(), "test", name * "_tests.jl"))
    end
    for name in ("basis_recovery", "simplex_driver", "simplex_policy")
        include(joinpath(pwd(), "dev", "tests", name * "_tests.jl"))
    end
end
