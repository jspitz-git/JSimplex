include("pilotnov.jl")
using Test
function matrix(output, completed)
    ispath(output) && error("Choose a fresh directory")
    mkpath(output)
    @testset "Pilotnov across all public managers and refactorizations" begin
        for backend in ("markowitz","native"), manager in ("pfi","huangfu_hall","forrest_tomlin","suhl_suhl","bartels_golub")
            path=joinpath(output,"$manager-$backend.toml")
            if completed != "-" && backend=="markowitz" && manager=="pfi"
                cp(completed,path)
            else
                Base.invokelatest(main,path,manager,backend)
            end
            r=TOML.parsefile(path)
            @test r["status"]=="OPTIMAL"
            @test get(r,"original_primal_feasible",false)
            @test get(r,"reference_matches",false)
            flush(stdout)
        end
    end
end
Base.invokelatest(matrix,ARGS...)
