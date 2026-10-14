# UNEXECUTED. Run in the future admitted reference process only.
using Test, JSimplex
function run_direct_lu_red()
    @testset "Common direct LU contract is available" begin
        @test isdefined(JSimplex,:BasisLUExport)
        @test isdefined(JSimplex,:_export_basis_lu)
        @test isdefined(JSimplex,:_direct_lu_factor)
    end
end
# No auto-run, no package injection, no numerical work on include.
