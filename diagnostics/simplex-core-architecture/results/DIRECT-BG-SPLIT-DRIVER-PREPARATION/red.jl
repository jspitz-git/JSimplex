# Ten NEW missing contracts; no numerical calls. UNEXECUTED.
function run_split_bg_red()
    @testset "Missing split BG U contracts (ten expected failures)" begin
        @test isdefined(JSimplex,:BGSplitUpper)
        @test isdefined(JSimplex,:_sbu_target)
        @test isdefined(JSimplex,:_sbu_reserve_block!)
        @test isdefined(JSimplex,:_sbu_build)
        @test isdefined(JSimplex,:_sbu_insert_at!)
        @test isdefined(JSimplex,:_sbu_rotate_rows!)
        @test isdefined(JSimplex,:SplitBGFactor)
        @test isdefined(JSimplex,:_split_bg_factor)
        @test isdefined(JSimplex,:_split_bg_replace!)
        @test isdefined(JSimplex,:_split_bg_copy_with)
    end
end
