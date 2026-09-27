# Only runs while building the package cache. Keep inputs independent of files,
# user datasets, global precision, and thread settings. Different coefficients
# in the latency probe verify that reuse is by signature, not by input values.
@setup_workload begin
    examples = map((Float64, Float32)) do T
        upper = LinearProblem(sparse(T[1 1; 1 0; 0 1]), T[-3, -2];
            row_upper=T[4, 2, 3])
        lower = LinearProblem(sparse(T[1 1; -1 1]), T[1, 2];
            row_lower=T[3, 1], column_lower=T[0, 1])
        (upper, lower)
    end

    @compile_workload begin
        with_logger(NullLogger()) do
            for (upper, lower) in examples
                T = eltype(upper.objective)
                for update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl),
                    algorithm in (:primal, :dual), presolve in (false, true)
                    options = SolverOptions(T; algorithm, basis_update=update,
                        basis_refactorization=:native, pricing=:steepest_edge,
                        simplex_strategy=:legacy, presolve, verbose=false,
                        iteration_limit=32, refactorization_interval=1)
                    for (problem, objective) in ((upper, -10), (lower, 5))
                        result = solve(problem; options)
                        @assert result.status == OPTIMAL
                        @assert isapprox(result.objective_value, T(objective))
                        @assert _original_primal_feasible(problem, result.primal,
                            options.primal_tolerance)
                    end
                end
                # Also retain the public entry point with default options.
                result = solve(upper)
                @assert result.status == OPTIMAL
                @assert isapprox(result.objective_value, T(-10))
            end
        end
    end
end
