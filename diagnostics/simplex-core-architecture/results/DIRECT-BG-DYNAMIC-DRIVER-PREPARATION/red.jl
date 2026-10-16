# UNEXECUTED. Missing NEW dynamic-U contracts only; zero factor/solve calls.
function run_dynamic_bg_red()
    @testset "Missing dynamic BG U contracts (eight expected failures)" begin
        @test isdefined(JSimplex,:BGSlotUpper)
        @test isdefined(JSimplex,:_bg_slots)
        @test isdefined(JSimplex,:_bg_reserve!)
        @test isdefined(JSimplex,:_bg_swap_rows!)
        @test isdefined(JSimplex,:_bg_rotate_rows!)
        @test isdefined(JSimplex,:DynamicBGFactor)
        @test isdefined(JSimplex,:_dynamic_bg_factor)
        @test isdefined(JSimplex,:_dynamic_bg_replace!)
    end
end
