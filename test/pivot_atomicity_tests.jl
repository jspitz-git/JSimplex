using SparseArrays

@testset "Stop callbacks always see a consistent live factor" begin
    for algorithm in (:dual,:primal)
        dual = algorithm == :dual
        p = LinearProblem(sparse([1.0;;]),[dual ? 1.0 : -1.0];
            row_lower=dual ? [1.0] : [nothing],row_upper=dual ? [nothing] : [1.0])
        options = SolverOptions(;algorithm,verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,options)
        calls = Ref(0)
        stop = function()
            calls[] += 1
            @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(1),w.factorization,[1.0]) ≈ [1.0]
            return false
        end
        result = dual ? JSimplex._dual_iteration!(w,stop) :
            JSimplex._primal_iteration!(w,stop,options.dual_tolerance)
        @test isnothing(result)
        @test w.iterations == 1
        @test calls[] > 1
    end
end

@testset "Committed bound flips publish the exact bound value" begin
    p = LinearProblem(sparse([0.0;;]),[-1.0];column_lower=[-1e16],column_upper=[1.0],row_lower=[0.0],row_upper=[0.0])
    options = SolverOptions(verbose=false,pricing=:dantzig,simplex_strategy=:adaptive,algorithm=:primal)
    seen = Ref(false)
    diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason == :flip_completed || return
        seen[] = true
        @test state.basis.states[1] == JSimplex.AT_UPPER
        @test state.primal[1] == 1.0
        @test state.iterations == 1
    end)
    progress = JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    w = JSimplex.initialize_workspace(p,options;progress)
    @test isnothing(JSimplex._primal_iteration!(w,()->false,options.dual_tolerance))
    @test seen[]
    @test w.primal[1] == 1.0
end

@testset "Validated pivots must permit finite factor updates" begin
    for a in ([1e-310],[1e-300,1e308])
        p = LinearProblem(sparse(reshape(a,:,1)),[0.0])
        w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
        rho = [-1.0;zeros(length(a)-1)]
        candidate = JSimplex.PivotCandidate(1,1,-a[1],-a,rho)
        @test JSimplex.validate_pivot!(w,candidate,JSimplex.NumericalPolicy(Float64)) == :reject_candidate
    end
end

@testset "Primal callbacks see prices for the committed basis" begin
    seen = Ref(false)
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    options = SolverOptions(;algorithm=:primal,verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
    diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason == :pivot_completed || return
        seen[] = true
        @test state.reduced_costs ≈ [0.0,-1.0]
    end)
    progress = JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    w = JSimplex.initialize_workspace(p,options;progress)
    stop = () -> begin
        w.iterations == 1 && @test w.reduced_costs ≈ [0.0,-1.0]
        false
    end
    @test isnothing(JSimplex._primal_iteration!(w,stop,options.dual_tolerance))
    @test seen[]
end
