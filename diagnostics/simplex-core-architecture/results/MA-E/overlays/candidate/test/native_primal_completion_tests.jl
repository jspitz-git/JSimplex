using SparseArrays

@testset "Native primal steps publish coherent values before completion callbacks" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), strategy in (:legacy, :adaptive),
        flip in (false, true), interruption in (:none, :proposed, :completed, :throw_completed)
        updates = T == Float64 ? (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub) : (:pfi,)
        for update in updates, interval in (1, 80)
            stopped = Ref(false)
            completed = Ref(0)
            failure = ErrorException("completion observer failed")
            value = flip ? one(T) : one(T)/2
            expected_point = T[value, value]
            expected_prices = flip ? T[-1, 0] : T[0, -1]
            problem = LinearProblem(sparse(reshape(T[1], 1, 1)), T[-1];
                row_upper=T[flip ? 2 : value], column_upper=T[1])
            options = SolverOptions(T; algorithm=:primal, simplex_strategy=strategy,
                pricing=:dantzig, basis_update=update, refactorization_interval=interval,
                presolve=false, verbose=false)
            diagnostics = JSimplex.SimplexDiagnostics(observer=(event, ws)->begin
                if event == :pivot_proposed && interruption == :proposed
                    stopped[] = true
                elseif event == (flip ? :flip_completed : :pivot_completed)
                    completed[] += 1
                    @test ws.iterations == 1
                    @test ws.primal == expected_point
                    @test ws.reduced_costs == expected_prices
                    @test ws.basis.states == (flip ? [JSimplex.AT_UPPER, JSimplex.BASIC] :
                                                              [JSimplex.BASIC, JSimplex.AT_UPPER])
                    interruption == :completed && (stopped[] = true)
                    interruption == :throw_completed && throw(failure)
                end
            end)
            ws = JSimplex.initialize_workspace(problem, options;
                progress=JSimplex.SimplexProgressContext(problem; diagnostics))
            before = (copy(ws.primal), copy(ws.reduced_costs), copy(ws.basis.basic_indices),
                      copy(ws.basis.states), copy(ws.pricing_weights))
            if interruption == :throw_completed
                caught = try
                    JSimplex._primal_iteration!(ws, ()->stopped[], options.dual_tolerance)
                catch exception
                    exception
                end
                @test caught isa JSimplex.DiagnosticObserverFailure
                @test caught.cause === failure
            else
                result = JSimplex._primal_iteration!(ws, ()->stopped[], options.dual_tolerance)
                @test interruption == :none ? isnothing(result) : result.status == TIME_LIMIT
            end
            if interruption == :proposed
                @test ws.iterations == completed[] == 0
                @test (ws.primal, ws.reduced_costs, ws.basis.basic_indices,
                       ws.basis.states, ws.pricing_weights) == before
                @test isempty(ws.factorization.updates)
            else
                @test ws.iterations == completed[] == 1
                @test ws.primal == expected_point
                @test ws.reduced_costs == expected_prices
            end
            # A fresh solve of the stored basis must agree with the returned point.
            point, prices = copy(ws.primal), copy(ws.reduced_costs)
            JSimplex.recompute!(ws)
            @test ws.primal == point
            @test ws.reduced_costs == prices
        end
    end
end
