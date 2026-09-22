using LinearAlgebra, SparseArrays

function refinement_workspace(B::Matrix{T}) where {T}
    p = LinearProblem(sparse(B),zeros(T,size(B,2)))
    w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
    w.basis.basic_indices .= axes(B,2)
    w.basis.states[1:size(B,2)] .= JSimplex.BASIC
    w.basis.states[(size(B,2)+1):end] .= JSimplex.FREE_NONBASIC
    JSimplex.recompute!(w;refactorize=true)
    return w
end

@testset "Shared refinement repairs normal and transposed basis solves" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), transposed in (false,true)
        perturbation = T === Float32 ? T(2)^-15 : T(1//(2^30))
        B = T[1 1;1 1+perturbation]
        w = refinement_workspace(B)
        policy = JSimplex.NumericalPolicy(T)
        exact = T[1,-1]
        rhs = (transposed ? transpose(B) : B)*exact
        saved = copy(rhs)
        x = T[1+1//1000,-1]
        q = JSimplex.refine_basis_solve!(x,w,rhs,policy,()->false;transposed)
        @test q isa JSimplex.SolveQuality{T}
        @test q.reliable && q.finite
        @test rhs == saved
        if T <: Rational
            @test (transposed ? transpose(B) : B)*x == rhs
        else
            setprecision(BigFloat,1024) do
                wide = BigFloat.(transposed ? transpose(B) : B)
                residual = abs.(BigFloat.(rhs)-wide*BigFloat.(x))
                scale = abs.(BigFloat.(rhs))+abs.(wide)*abs.(BigFloat.(x))
                @test all(residual .<= BigFloat(policy.solve_tolerance).*scale)
            end
        end
        # A well-conditioned fixture keeps the stale-factor residual above
        # tolerance for all types, independently of forward-error conditioning.
        stale_B = T[2 1;0 1]
        stale = refinement_workspace(stale_B)
        JSimplex.refactorize!(stale.factorization,2stale_B)
        stale_rhs = (transposed ? transpose(stale_B) : stale_B)*T[1,0]
        saved_stale_rhs = copy(stale_rhs)
        fill!(x,zero(T))
        q = JSimplex.refine_basis_solve!(x,stale,stale_rhs,policy,()->false;transposed)
        @test !q.reliable
        @test stale_rhs == saved_stale_rhs
    end
end

@testset "Shared refinement honors alias, deadline and exception boundaries" begin
    B = [2.0 1.0;0.0 1.0]
    w = refinement_workspace(B)
    policy = JSimplex.NumericalPolicy(Float64)
    rhs = [2.0,0.0]
    @test_throws ArgumentError JSimplex.refine_basis_solve!(rhs,w,rhs,policy,()->false)
    @test rhs == [2.0,0.0]
    @test_throws ArgumentError JSimplex.refine_basis_solve!(view(rhs,:),w,rhs,policy,()->false)
    x = [0.0,0.0]
    @test !JSimplex.refine_basis_solve!(x,w,rhs,policy,()->true).reliable
    @test x == [0.0,0.0]
    failure = ErrorException("refinement callback failure")
    caught = try
        JSimplex.refine_basis_solve!(x,w,rhs,policy,()->throw(failure))
        nothing
    catch e
        e
    end
    @test caught === failure
    @test x == [0.0,0.0] && rhs == [2.0,0.0]
    limited = JSimplex.NumericalPolicy(Float64;max_refinements=0)
    @test !JSimplex.refine_basis_solve!(x,w,rhs,limited,()->false).reliable
    @test x == [0.0,0.0]
end

@testset "Shared refinement rejects overlapping private buffers before mutation" begin
    w = refinement_workspace([2.0 1.0;0.0 1.0])
    policy = JSimplex.NumericalPolicy(Float64)
    buffers = JSimplex._pivot_quality_buffers(w)
    for array in (buffers.rhs,buffers.unit,buffers.correction,buffers.trial,
                  buffers.column.residual,buffers.column.work_residual,
                  buffers.row.residual,buffers.row.work_scale)
        array .= [3.0,4.0]
        saved = copy(array)
        @test_throws ArgumentError JSimplex.refine_basis_solve!(array,w,[2.0,0.0],policy,()->false)
        @test array == saved
        @test_throws ArgumentError JSimplex.refine_basis_solve!(zeros(2),w,array,policy,()->false)
        @test array == saved
    end
end

@testset "Failed corrections preserve the last finite solution" begin
    for wrong_factor in (1e-308,1e308,-1.0)
        w = refinement_workspace([1.0;;])
        JSimplex.refactorize!(w.factorization,sparse([wrong_factor;;]))
        rhs = [wrong_factor == 1e-308 ? 1e308 : 2.0]
        x = [wrong_factor == 1e308 ? 1.0 : 0.0]
        saved_x,saved_rhs = copy(x),copy(rhs)
        q = JSimplex.refine_basis_solve!(x,w,rhs,JSimplex.NumericalPolicy(Float64),()->false)
        @test !q.reliable
        @test x == saved_x && rhs == saved_rhs
    end
end

@testset "BigFloat refinement retains stored precision" begin
    setprecision(BigFloat,512) do
        B = BigFloat[1 1;1 1+BigFloat(2)^-100]
        w = refinement_workspace(B)
        rhs = B*BigFloat[1,-1]
        x = BigFloat[BigFloat(1)+BigFloat(1)/1000,-1]
        policy = JSimplex.NumericalPolicy(BigFloat)
        saved_rhs = deepcopy(rhs)
        setprecision(BigFloat,64) do
            q = JSimplex.refine_basis_solve!(x,w,rhs,policy,()->false)
            @test q.reliable
            @test all(v->precision(v)>=512,x)
            @test precision(BigFloat) == 64
            @test rhs == saved_rhs
        end
    end
end

@testset "Shared solve refinement is independently configurable" begin
    @test JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive).solve_refinement
    @test !JSimplex.NumericalPolicy(Float64).solve_refinement
    @test !JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,solve_refinement=false).solve_refinement
end

@testset "Recomputation rejects an unreliable solve without changing costs" begin
    w = refinement_workspace([2.0 1.0;0.0 1.0])
    w.costs[1:2] .= [2.0,0.0]
    w.progress = JSimplex.SimplexProgressContext(w.problem;
        numerical_policy=JSimplex.NumericalPolicy(Float64;solve_refinement=true))
    JSimplex.refactorize!(w.factorization,2JSimplex.basis_matrix(w))
    saved_costs = copy(w.costs)
    @test_throws JSimplex._UnreliableBasisSolve JSimplex.recompute!(w)
    @test w.costs == saved_costs
end

@testset "Aggregate BFRT refinement preserves the entering direction on failure" begin
    p = LinearProblem(sparse([1.0 2.0]),zeros(2);column_upper=[1.0,1.0])
    progress = JSimplex.SimplexProgressContext(p;
        numerical_policy=JSimplex.NumericalPolicy(Float64;solve_refinement=true))
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    JSimplex.refactorize!(w.factorization,2JSimplex.basis_matrix(w))
    w.scratch.row_solution .= [123.0]
    saved = (copy(w.costs),copy(w.primal),copy(w.basis.states))
    @test !JSimplex._apply_bound_flips!(w,[1])
    @test w.scratch.row_solution == [123.0]
    @test saved == (w.costs,w.primal,w.basis.states)
end

@testset "Bound-flip refinement events observe committed primal prices" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];column_upper=[1.0])
    options = SolverOptions(;algorithm=:primal,verbose=false,simplex_strategy=:adaptive,pricing=:dantzig)
    live = Ref{Any}()
    seen = Ref(0)
    diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason == :correction && state.iterations == 1 || return
        seen[] += 1
        @test state === live[]
        @test live[].iterations == 1
        @test live[].primal ≈ [1.0,1.0]
        @test live[].reduced_costs == [-1.0,0.0]
    end)
    progress = JSimplex.SimplexProgressContext(p;diagnostics,
        numerical_policy=JSimplex.NumericalPolicy(Float64,options))
    w = JSimplex.initialize_workspace(p,options;progress)
    live[] = w
    JSimplex.refactorize!(w.factorization,(1+1e-6)*JSimplex.basis_matrix(w))
    @test isnothing(JSimplex._primal_iteration!(w,()->false,options.dual_tolerance))
    @test seen[] > 0
    @test w.iterations == 1
end

@testset "Correction observers retain exception identity and working costs" begin
    p = LinearProblem(sparse([2.0 1.0;0.0 1.0]),[0.0,0.0])
    failure = ErrorException("correction observer failed")
    diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason == :correction_attempt && throw(failure)
    end)
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    saved_costs = copy(w.costs)
    x,rhs = zeros(2),[1.0,1.0]
    caught = try
        JSimplex.refine_basis_solve!(x,w,rhs,JSimplex.NumericalPolicy(Float64),()->false)
        nothing
    catch e
        e
    end
    @test caught isa JSimplex.DiagnosticObserverFailure
    @test caught.cause === failure
    @test x == zeros(2) && rhs == [1.0,1.0]
    @test w.costs == saved_costs
end

@testset "Precision-specialized repairs retain their stronger residual targets" begin
    B = sparse([1.0 1.0;2.0 2.0+2.0^-30])
    exact = [1.0,-1.0]
    for bits in (256,512), transposed in (false,true)
        rhs = (transposed ? transpose(B) : B)*exact
        saved_rhs = copy(rhs)
        factor = lu(1.0001B)
        x = JSimplex._refined_basis_solution(factor,B,rhs,bits,()->false;transposed)
        @test !isnothing(x)
        if !isnothing(x)
            setprecision(BigFloat,1024) do
                wide = BigFloat.(transposed ? transpose(B) : B)
                error = maximum(abs,wide*x-BigFloat.(rhs))
                target = BigFloat(10)^(-(bits==256 ? 40 : 90))
                @test error <= target*max(one(BigFloat),maximum(abs,rhs))
            end
        end
        @test rhs == saved_rhs
        @test isnothing(JSimplex._refined_basis_solution(lu(2B),B,rhs,bits,()->false;transposed))
        @test isnothing(JSimplex._refined_basis_solution(factor,B,rhs,bits,()->true;transposed))
    end
    # The wide residual must be checked before conversion reaches the narrow LU.
    @test isnothing(JSimplex._refined_basis_solution(lu(sparse([1.0;;])),
        sparse([1e308;;]),[1e308],256,()->false))
end

@testset "Refinement removes a lone rounding artifact in a homogeneous equation" begin
    for transposed in (false,true)
        base = [1.0 0.0 0.1;0.0 1.0 0.0;0.0 1.0 -2.0]
        B = transposed ? Matrix(transpose(base)) : base
        p = LinearProblem(sparse(B),zeros(3))
        w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
        w.basis.basic_indices .= 1:3
        w.basis.states[1:3] .= JSimplex.BASIC
        w.basis.states[4:6] .= JSimplex.FREE_NONBASIC
        JSimplex.recompute!(w;refactorize=true)
        JSimplex.refactorize!(w.factorization,1.01B)
        rhs = [1.0,0.0,0.0]
        x = [1.0,0.0,1e-18]
        policy = JSimplex.NumericalPolicy(Float64;solve_refinement=true,max_refinements=1)
        q = JSimplex.refine_basis_solve!(x,w,rhs,policy,()->false;transposed)
        @test q.reliable
        @test x == [1.0,0.0,0.0]
        @test rhs == [1.0,0.0,0.0]
    end
end

@testset "Discarded candidate corrections retain actual work counts" begin
    p = LinearProblem(sparse([1.0;;]),[0.0])
    seen = Symbol[]
    diagnostics = JSimplex.SimplexDiagnostics(;kernel_timing=true,observer=(reason,state)->push!(seen,reason))
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    empty!(seen)
    before = (diagnostics.counts[:correction_attempt],diagnostics.counts[:correction],diagnostics.kernel_calls[:ftran])
    result = JSimplex._transactional_simplex_step!(w,()->false) do candidate,stop
        candidate.scratch.post_iteration = :primal
        q = JSimplex.refine_basis_solve!([0.0],candidate,[1.0],
                                        JSimplex.NumericalPolicy(Float64),stop)
        @test q.reliable
        JSimplex.DualTermination(NUMERICAL_ERROR,"discard after completed numerical work")
    end
    @test result.status == NUMERICAL_ERROR
    @test w.iterations == 0
    @test diagnostics.counts[:correction_attempt] == before[1]+1
    @test diagnostics.counts[:correction] == before[2]+1
    @test diagnostics.kernel_calls[:ftran] == before[3]+1
    @test isempty(seen)
end

@testset "Homogeneous cleanup preserves small nonzero right-hand sides" begin
    w = refinement_workspace([1.0 1.0;0.0 1.0])
    JSimplex.refactorize!(w.factorization,1.01JSimplex.basis_matrix(w))
    rhs = [1.0,1e-20]
    x = [1.0,0.0]
    q = JSimplex.refine_basis_solve!(x,w,rhs,
        JSimplex.NumericalPolicy(Float64;solve_refinement=true,max_refinements=1),()->false)
    @test !q.reliable
    @test x[2] > 0.0
    @test rhs == [1.0,1e-20]
end

@testset "Refinement removes coupled rounding artifacts in a homogeneous equation" begin
    for transposed in (false,true)
        base = [1.0 0.1 0.2;0.0 1.0 1.0;0.0 1.0 -1.0]
        B = transposed ? Matrix(transpose(base)) : base
        p = LinearProblem(sparse(B),zeros(3))
        w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
        w.basis.basic_indices .= 1:3
        w.basis.states[1:3] .= JSimplex.BASIC
        w.basis.states[4:6] .= JSimplex.FREE_NONBASIC
        JSimplex.recompute!(w;refactorize=true)
        JSimplex.refactorize!(w.factorization,1.01B)
        rhs = [1.0,0.0,0.0]
        x = [1.0,1e-18,2e-18]
        policy = JSimplex.NumericalPolicy(Float64;solve_refinement=true,max_refinements=1)
        q = JSimplex.refine_basis_solve!(x,w,rhs,policy,()->false;transposed)
        @test q.reliable
        @test x == [1.0,0.0,0.0]
        @test rhs == [1.0,0.0,0.0]
    end
end

@testset "Rejected homogeneous cleanup restores the ordinary correction" begin
    w = refinement_workspace([1.0 0.0 0.0;0.0 1.0 1.0;0.0 0.0 1.0])
    JSimplex.refactorize!(w.factorization,1.01JSimplex.basis_matrix(w))
    rhs = [1.0,0.0,1e-20]
    x = [1.0,0.0,0.0]
    q = JSimplex.refine_basis_solve!(x,w,rhs,
        JSimplex.NumericalPolicy(Float64;solve_refinement=true,max_refinements=1),()->false)
    @test !q.reliable
    @test x[2] < 0.0 && x[3] > 0.0
    @test x[2]+x[3] == 0.0
    @test rhs == [1.0,0.0,1e-20]
end
