using Test, JSimplex, LinearAlgebra, SparseArrays
root=dirname(dirname(pathof(JSimplex)))
@testset "Native BG terminal recovery" begin
    for file in ("native_cleanup_second_correction_tests.jl","native_cleanup_recovery_tests.jl",
        "native_driver_reconstruction_tests.jl","native_dual_reconstruction_tests.jl",
        "native_reliable_price_tests.jl","native_certificate_recovery_tests.jl")
        println("TEST ",file);flush(stdout)
        include(joinpath(root,"test",file))
    end
end
