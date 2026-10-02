using Test,JSimplex
@testset "Compiled phase component and cleanup regressions" begin
    root=dirname(dirname(pathof(JSimplex)))
    include(joinpath(root,"test/native_phase_transfer_tests.jl"))
    include(joinpath(root,"test/native_cleanup_recovery_tests.jl"))
end
