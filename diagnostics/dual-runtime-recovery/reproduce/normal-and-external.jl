using Test,JSimplex
@testset "Native cleanup final focused checks" begin
    include(joinpath(pwd(),"test/native_cleanup_recovery_tests.jl"))
    include(joinpath(pwd(),"test/native_residual_tests.jl"))
end
include(joinpath(pwd(),"diagnostics/simplex-strategy-separation/reproduce/external.jl"))
