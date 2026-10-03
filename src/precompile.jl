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
                for update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl, :huangfu_hall),
                    refactorization in (:native,),
                    algorithm in (:primal, :dual), presolve in (false, true)
                    # The public MPF manager currently supports native Float64 only.
                    update === :huangfu_hall &&
                        !(T === Float64 && refactorization === :native && Int === Int64) && continue
                    options = SolverOptions(T; algorithm, basis_update=update,
                        basis_refactorization=refactorization, pricing=:steepest_edge,
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
            # Warm the shared Markowitz backend without duplicating every complete
            # simplex specialization. Cover sparse pivots and the dense trailing core.
            for T in (Float64, Float32)
                matrices = (spdiagm(0 => T[2, 3, 4]), sparse(T[4 1 2; 2 5 1; 1 3 6]))
                expected = T[1, -2, 3]
                destination = zeros(T, 3)
                for (i, matrix) in enumerate(matrices)
                    backend = _factorize_basis(matrix, Val(:markowitz))
                    @assert (backend.sparse_pivots > 0) == (i == 1)
                    _backend_forward_solve!(destination, backend, matrix * expected)
                    @assert destination ≈ expected
                    _backend_transpose_solve!(destination, backend, transpose(matrix) * expected)
                    @assert destination ≈ expected
                    replacement = matrices[3 - i]
                    backend = _refactorize_backend(backend, replacement)
                    _backend_forward_solve!(destination, backend, replacement * expected)
                    @assert destination ≈ expected
                    _backend_transpose_solve!(destination, backend, transpose(replacement) * expected)
                    @assert destination ≈ expected
                end
            end
        end
    end
end
