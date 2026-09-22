using SparseArrays, LinearAlgebra
using Logging

struct PivotApplicationThrowLogger <: AbstractLogger end
Logging.min_enabled_level(::PivotApplicationThrowLogger) = Logging.Debug
Logging.shouldlog(::PivotApplicationThrowLogger,args...) = true
Logging.catch_exceptions(::PivotApplicationThrowLogger) = false
function Logging.handle_message(::PivotApplicationThrowLogger,level,message,args...;kwargs...)
    message == "Refactorizing basis" && error("logger failed during candidate refactorization")
end

@testset "Logger failures preserve the count of committed steps" begin
    for algorithm in (:dual,:primal), stale in (false,true)
        dual = algorithm == :dual
        p = LinearProblem(sparse([1.0;;]),[dual ? 1.0 : -1.0];
            row_lower=dual ? [1.0] : [nothing],row_upper=dual ? [nothing] : [1.0])
        options = SolverOptions(;algorithm,verbose=true,pricing=:dantzig,
            simplex_strategy=:adaptive,refactorization_interval=1)
        w = JSimplex.initialize_workspace(p,options)
        stale && JSimplex.refactorize!(w.factorization,2JSimplex.basis_matrix(w))
        original = (copy(w.primal),copy(w.reduced_costs),copy(w.costs),
                    copy(w.basis.states),copy(w.basis.basic_indices))
        stop = JSimplex._guard_stop_callback(()->false)
        @test_throws ErrorException with_logger(PivotApplicationThrowLogger()) do
            dual ? JSimplex._dual_iteration!(w,stop) :
                JSimplex._primal_iteration!(w,stop,options.dual_tolerance)
        end
        @test w.iterations == (stale ? 0 : 1)
        if stale
            @test original == (w.primal,w.reduced_costs,w.costs,w.basis.states,w.basis.basic_indices)
        else
            @test w.primal == [1.0,1.0]
            @test JSimplex.basis_matrix(w)*JSimplex.forward_solve!(zeros(1),w.factorization,[1.0]) ≈ [1.0]
        end
    end
end

@testset "Accurate small pivots work across scalar types" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), algorithm in (:dual,:primal)
        dual = algorithm == :dual
        a = T(1//10^14)
        p = LinearProblem(sparse(reshape(T[a],1,1)),T[dual ? 1 : -1];
            row_lower=dual ? T[1] : [nothing],row_upper=dual ? [nothing] : T[1])
        options = SolverOptions(T;algorithm,verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
        w = JSimplex.initialize_workspace(p,options)
        result = dual ? JSimplex._dual_iteration!(w,()->false) :
            JSimplex._primal_iteration!(w,()->false,options.dual_tolerance)
        @test isnothing(result)
        @test w.iterations == 1
        @test w.basis.basic_indices == [1]
        @test w.primal[1] ≈ inv(a)
    end
end

@testset "Adaptive pivot validation is independently configurable" begin
    @test JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive).pivot_validation
    @test !JSimplex.NumericalPolicy(Float64;pivot_validation=false).pivot_validation
    @test JSimplex.NumericalPolicy(Float64;pivot_validation=true,stable_ratio=false).pivot_validation
end

@testset "Uncertain pivot solves receive bounded corrections" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), transposed in (false,true)
        B = T[2 1;0 1]
        w = pivot_workspace(B,T[1,1])
        policy = JSimplex.NumericalPolicy(T)
        exact = T[1,0]
        rhs = transposed ? transpose(B)*exact : B*exact
        saved_rhs = copy(rhs)
        x = T[1+1//1000,0]
        q = JSimplex._refine_pivot_solve!(x,w,rhs,policy,()->false;transposed)
        @test q.reliable
        @test x ≈ exact
        @test rhs == saved_rhs
        JSimplex.refactorize!(w.factorization,2B)
        fill!(x,zero(T))
        q = JSimplex._refine_pivot_solve!(x,w,rhs,policy,()->false;transposed)
        @test !q.reliable
        @test rhs == saved_rhs
    end
end

@testset "Completion observers see an atomic simplex state" begin
    for failure_event in (:pivot_proposed,:bound_flipped,:pivot_completed)
        p = LinearProblem(sparse([1.0 1.0]),[1.0,2.0];
                          column_upper=[1.0,2.0],row_lower=[2.0])
        options = SolverOptions(verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
        live = Ref{Any}()
        observer = function(reason,state)
            reason == failure_event || return
            w = live[]
            if reason == :pivot_proposed
                @test w.iterations == 0
                @test w.basis.basic_indices == [3]
            else
                @test state === w
                @test w.iterations == 1
                @test w.basis.basic_indices == [2]
                @test w.primal == [1.0,1.0,2.0]
                @test p.A*w.primal[1:2] == w.primal[3:3]
            end
            error("observer failure")
        end
        diagnostics = JSimplex.SimplexDiagnostics(;observer,kernel_timing=true)
        progress = JSimplex.SimplexProgressContext(p;diagnostics,
            numerical_policy=JSimplex.NumericalPolicy(Float64,options))
        w = JSimplex.initialize_workspace(p,options;progress)
        live[] = w
        @test_throws JSimplex.DiagnosticObserverFailure JSimplex._dual_iteration!(w,()->false)
        @test w.iterations == (failure_event == :pivot_proposed ? 0 : 1)
        if failure_event != :pivot_proposed
            @test diagnostics.kernel_calls[:ftran] > 0
            @test diagnostics.kernel_calls[:btran] > 0
        end
    end
end

@testset "Both algorithms refresh stale factors before application" begin
    for algorithm in (:dual,:primal), update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl),
        backend in (:native,:markowitz)
        dual = algorithm == :dual
        p = LinearProblem(sparse([1.0;;]),[dual ? 1.0 : -1.0];
            row_lower=dual ? [1.0] : [nothing],row_upper=dual ? [nothing] : [1.0])
        options = SolverOptions(;algorithm,verbose=false,pricing=:dantzig,
            simplex_strategy=:adaptive,basis_update=update,basis_refactorization=backend)
        w = JSimplex.initialize_workspace(p,options)
        JSimplex.refactorize!(w.factorization,2JSimplex.basis_matrix(w))
        result = dual ? JSimplex._dual_iteration!(w,()->false) :
            JSimplex._primal_iteration!(w,()->false,options.dual_tolerance)
        @test isnothing(result)
        @test w.iterations == 1
        @test w.primal[1] ≈ 1.0
        @test p.A*w.primal[1:1] ≈ w.primal[2:2]
    end
end

function cancellation_pivot_workspace(algorithm)
    B = [1.0 1.0;1.0 1.0+2.0^-40]
    A = hcat(B,[-1.0,-1.0],[-2.0^-42,0.0])
    dual = algorithm == :dual
    dual || (A[:,3:4] .*= -1)
    costs = dual ? [0.0,0.0,1.0,0.25] : [0.0,0.0,-1.0,-0.25]
    p = LinearProblem(sparse(A),costs;
        row_lower=fill(dual ? -1.0 : 0.0,2),row_upper=fill(dual ? -1.0 : 0.0,2))
    options = SolverOptions(;algorithm,verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
    diagnostics = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(p;diagnostics,
        numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    w = JSimplex.initialize_workspace(p,options;progress)
    w.basis.basic_indices .= [1,2]
    fill!(w.basis.states,JSimplex.AT_LOWER)
    w.basis.states[1:2] .= JSimplex.BASIC
    JSimplex.recompute!(w;refactorize=true)
    return w,diagnostics
end

@testset "Cancellation rejects one pivot and selects another" begin
    for algorithm in (:dual,:primal)
        w,diagnostics = cancellation_pivot_workspace(algorithm)
        result = algorithm == :dual ? JSimplex._dual_iteration!(w,()->false) :
            JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance)
        @test isnothing(result)
        @test w.iterations == 1
        @test w.basis.basic_indices[1] == 4
        @test diagnostics.counts[:pivot_rejected] >= 1
        @test diagnostics.counts[:pivot_completed] == 1
    end
end

@testset "Rejection budgets preserve state and refresh cached policy" begin
    w,_ = cancellation_pivot_workspace(:dual)
    old = w.progress
    limited = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,
        max_pivot_candidates=1,max_recovery_rounds=0,max_refinements=0)
    w.progress = JSimplex.SimplexProgressContext(w.problem;diagnostics=old.diagnostics,
                                                numerical_policy=limited)
    original = (copy(w.basis.basic_indices),copy(w.basis.states),copy(w.primal),copy(w.costs))
    result = JSimplex._dual_iteration!(w,()->false)
    @test result.status == NUMERICAL_ERROR
    @test w.iterations == 0
    @test original == (w.basis.basic_indices,w.basis.states,w.primal,w.costs)
    @test isempty(w.scratch.rejected_entering) && isempty(w.scratch.rejected_rows)
    w.progress = old
    candidate = JSimplex._candidate_workspace(w)
    @test candidate.progress.numerical_policy.max_refinements == old.numerical_policy.max_refinements
    @test candidate.progress.start_ns == old.start_ns
    @test isnothing(JSimplex._dual_iteration!(w,()->false))
    @test w.iterations == 1
end
