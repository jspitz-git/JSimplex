using Test, JSimplex, SparseArrays, LinearAlgebra

function native_cleanup_workspace(; strategy=:legacy, update=:pfi, diagnostics=nothing)
    # Native LU leaves rounding artifacts in the last homogeneous equation.
    A = sparse([4.0 4.0 0.0 -5.0 1.0; 3.0 2.0 -1.0 4.0 -3.0;
                0.0 -4.0 4.0 -5.0 2.0; -3.0 1.0 0.0 5.0 3.0;
                0.0 0.0 -4.0 -4.0 -3.0])
    rhs = [12.0, 7.0, -8.0, -1.0, 0.0]
    problem = LinearProblem(A,zeros(5);row_lower=rhs,row_upper=rhs,
                            column_lower=fill(-Inf,5))
    options = SolverOptions(;verbose=false,algorithm=:dual,simplex_strategy=strategy,
        basis_update=update,presolve=false,scaling=:off)
    progress = JSimplex.SimplexProgressContext(problem;diagnostics,
        numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    ws = JSimplex.initialize_workspace(problem,options;progress)
    ws.basis = JSimplex.Basis(collect(1:5),vcat(fill(JSimplex.BASIC,5),fill(JSimplex.AT_LOWER,5)))
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Native cleanup repairs a feasible basis before restarting" begin
    for strategy in (:legacy,:adaptive), update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws = native_cleanup_workspace(;strategy,update)
        @test !ws.progress.numerical_policy.solve_refinement
        @test JSimplex.primal_infeasibility(ws) == 0.0
        @test JSimplex._original_primal_feasible(ws,ws.primal[1:5])
        # Force the mandatory original-cost cleanup without enabling heuristics.
        ws.perturbed = true
        basis = deepcopy(ws.basis)
        result = JSimplex.run_from_basis!(ws,JSimplex.SimplexRunBudget(ws),
            ws.progress.numerical_policy,()->false)
        @test result.status == OPTIMAL
        @test result.iterations == 0
        @test ws.basis.basic_indices == basis.basic_indices
        @test ws.basis.states == basis.states
        @test ws.primal[1:5] ≈ [1.0,2.0,0.0,0.0,0.0]
        @test JSimplex._recomputed_basis_reliable(ws)
        @test JSimplex._original_costs_active(ws)
        @test !ws.progress.numerical_policy.solve_refinement
    end
end

@testset "Native cleanup keeps rejected and interrupted corrections private" begin
    for interruption in (:deadline,:exception,:bad_factor,:bad_dual)
        ws = native_cleanup_workspace()
        if interruption == :bad_factor
            JSimplex.refactorize!(ws.factorization,-JSimplex.basis_matrix(ws))
            ws.primal[1] = 50.0
        elseif interruption == :bad_dual
            ws.scratch.rho[1] = NaN
        end
        saved = deepcopy((ws.primal,ws.reduced_costs,ws.scratch.rho,
                          ws.costs,ws.lower,ws.upper,ws.basis.basic_indices,ws.basis.states))
        calls=Ref(0)
        exception=SingularException(29)
        stop=JSimplex._guard_stop_callback(()->begin
            calls[] += 1
            if calls[] == 3
                interruption == :exception && throw(exception)
                interruption == :deadline && return true
            end
            false
        end)
        result=try
            JSimplex._try_native_cleanup_recompute!(ws,stop)
        catch error
            error
        end
        @test result === (interruption == :exception ? exception : false)
        @test isequal(saved,(ws.primal,ws.reduced_costs,ws.scratch.rho,
                           ws.costs,ws.lower,ws.upper,ws.basis.basic_indices,ws.basis.states))
        @test ws.iterations == 0
    end
end

@testset "Native cleanup preserves tiny nonzero equations" begin
    for T in (Float32,Float64), transposed in (false,true)
        B = sparse(T[1 0 0; 0 1 1; 0 0 1])
        transposed && (B=copy(transpose(B)))
        p=LinearProblem(B,zeros(T,3))
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
        JSimplex.refactorize!(ws.factorization,B)
        tiny=T === Float32 ? T(1e-15) : T(1e-30)
        rhs=T[1,0,tiny]
        x=T[1,0,0]
        @test JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->false;transposed)
        @test x[3] == tiny
        @test x[2] == -tiny
        @test JSimplex.solve_quality!(JSimplex.SolveQualityScratch(T,3),B,x,rhs,
            ws.progress.numerical_policy;transposed).reliable
    end
end

@testset "Native cleanup observes the correction budget and arithmetic mode" begin
    ws=native_cleanup_workspace()
    ws.progress=JSimplex.SimplexProgressContext(ws.problem;
        numerical_policy=JSimplex.NumericalPolicy(Float64;max_refinements=0))
    saved=copy(ws.primal)
    @test !JSimplex._try_native_cleanup_recompute!(ws,()->false)
    @test ws.primal == saved
    original_mode = get_zero_subnormals()
    set_zero_subnormals(true)
    try
        ws.progress=JSimplex.SimplexProgressContext(ws.problem)
        @test !JSimplex._try_native_cleanup_recompute!(ws,()->false)
        @test ws.primal == saved
    finally
        set_zero_subnormals(original_mode)
    end
end

@testset "Native cleanup publishes corrected dual prices with the primal point" begin
    for update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws=native_cleanup_workspace(;update)
        ws.costs[1:5] .= [1.0,2.0,3.0,4.0,5.0]
        JSimplex.recompute!(ws)
        ws.scratch.rho[1] += 1e-5
        ws.reduced_costs .+= 1.0
        costs=copy(ws.costs)
        @test !JSimplex._recomputed_basis_reliable(ws)
        @test JSimplex._try_native_cleanup_recompute!(ws,()->false)
        @test JSimplex._recomputed_basis_reliable(ws)
        @test ws.costs == costs
        @test ws.primal[1:5] ≈ [1.0,2.0,0.0,0.0,0.0]
        @test ws.reduced_costs[1:5] == zeros(5)
        @test ws.reduced_costs[6:10] == ws.costs[6:10] + ws.scratch.rho
        @test ws.problem.A' * ws.scratch.rho ≈ ws.costs[1:5]
    end
end
