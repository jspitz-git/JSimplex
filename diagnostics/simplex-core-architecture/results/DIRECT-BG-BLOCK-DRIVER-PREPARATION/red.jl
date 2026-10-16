# Eight NEW contract checks; zero factor/solve/update entries.
function run_block_bg_red()
    @testset "Missing block BG U contracts (eight expected failures)" begin
        @test isdefined(JSimplex,:BGBlockUpper)
        @test isdefined(JSimplex,:_bgu_build)
        @test isdefined(JSimplex,:_bgu_insert_at!)
        @test isdefined(JSimplex,:_bgu_swap_rows!)
        @test isdefined(JSimplex,:_bgu_rotate_rows!)
        @test isdefined(JSimplex,:BlockBGFactor)
        @test isdefined(JSimplex,:_block_bg_factor)
        @test isdefined(JSimplex,:_block_bg_replace!)
    end
end
