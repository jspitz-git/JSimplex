# UNEXECUTED structural missing-contract RED; no factorization or solve.
function run_bg_export_red()
    @testset "Missing BG export workspace contracts (six expected failures)" begin
        @test isdefined(JSimplex, :BGExportWorkspace)
        @test isdefined(JSimplex, :_bgx_scratch!)
        @test isdefined(JSimplex, :_bgx_scale_mode)
        @test isdefined(JSimplex, :_bgx_import_upper)
        @test isdefined(JSimplex, :BGExportFactor)
        @test isdefined(JSimplex, :_bgx_refactor_with!)
    end
end
