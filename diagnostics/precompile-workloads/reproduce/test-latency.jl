using TOML
loading = @timed @eval using JSimplex, Test
root = dirname(dirname(pathof(JSimplex)))
checks = @timed @eval begin
    @testset "Representative native solver tests" begin
        include(joinpath($root,"test","legacy_dual_correction_tests.jl"))
        include(joinpath($root,"test","legacy_dual_price_repair_tests.jl"))
        include(joinpath($root,"test","triangular_prepared_spike_tests.jl"))
    end
end
open(ARGS[1],"w") do io
    TOML.print(io,Dict("julia"=>string(VERSION),"load_seconds"=>loading.time,
        "test_seconds"=>checks.time,"compile_seconds"=>checks.compile_time,
        "recompile_seconds"=>checks.recompile_time))
end
