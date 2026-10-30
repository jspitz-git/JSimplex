using JSimplex,Test
@assert realpath(pathof(JSimplex))==realpath(joinpath(@__DIR__,"overlays","reference","src","JSimplex.jl"))
include("weights_fixture.jl")
function task4_red()
    @testset "TASK4_RED" begin
        strict=Task4WeightFixture.fixture(Float64;failed_row=2)
        @test JSimplex._rebuild_recovery_weights!(strict.ws,strict.guard)===false
        @test (strict.factor.unit_calls,strict.factor.correction_calls)==(2,1)
        @test strict.ws.pricing_weights==[1.0,8.0,7.0,6.0]
        @test strict.ws.scratch.refactorization.latest_quality.finite
        @test !strict.ws.scratch.refactorization.latest_quality.reliable
        @test !strict.ws.dual_devex_fallback
        proposed=Task4WeightFixture.fixture(Float64;failed_row=2)
        # The baseline executes its actual strict numerical boundary, not an
        # undefined new API. Candidate readiness is tested fully by GREEN.
        recovery_ready=if isdefined(JSimplex,:_rebuild_recovery_weights_result!)
            JSimplex._rebuild_recovery_weights_result!(proposed.ws,proposed.guard;algorithm=:dual).fallback_ready
        else
            JSimplex._rebuild_recovery_weights!(proposed.ws,proposed.guard)
        end
        @test (proposed.factor.unit_calls,proposed.factor.correction_calls)==(2,1)
        @test recovery_ready === true # EXPECTED_RED: sole baseline behavioral failure
    end
end
Base.invokelatest(task4_red)
