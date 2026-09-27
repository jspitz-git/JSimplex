# Pass the selected small NetLib/MIPLib model paths as CLI arguments.
using JSimplex, Test
function validate(paths)
    isempty(paths) && error("Supply at least one small model path")
    for path in paths
        lowercase(basename(realpath(path))) in ("big.mps","largo.mps","anymod.mps") &&
            error("Excluded large model")
        problem = read_mps(path)
        reference = nothing
        for manager in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl)
            options = SolverOptions(algorithm=:dual,simplex_strategy=:legacy,
                pricing=:steepest_edge,basis_refactorization=:native,
                basis_update=manager,refactorization_interval=80,
                iteration_limit=10000,time_limit=60.0,verbose=false)
            result = Base.invokelatest(solve,problem;options,relax_integrality=true)
            @testset "$(basename(path)) $manager" begin
                @test result.status == OPTIMAL
                if result.status == OPTIMAL
                    @test JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
                    if isnothing(reference)
                        reference = result.objective_value
                    else
                        @test isapprox(result.objective_value,reference;atol=1e-6,rtol=1e-8)
                    end
                end
            end
            println("MODEL ",basename(path)," manager=",manager," status=",result.status,
                " iterations=",result.statistics.iterations," seconds=",result.statistics.elapsed_seconds,
                " objective=",result.objective_value)
            flush(stdout)
        end
    end
end
Base.invokelatest(validate,ARGS)
