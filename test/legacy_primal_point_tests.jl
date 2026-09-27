using JSimplex.SparseArrays

function zero_step_ill_conditioned_workspace(::Type{T}, update; valid=true, inequality=false, reverse=false, entering_limit=Inf) where {T}
    delta = T === Float32 ? T(1e-5) : T(1e-10)
    tolerance = T === Float32 ? T(1e-4) : T(1e-7)
    A = T[1 1 -1 1 0; 1 1+delta -(1+2delta) 1 delta]
    reverse && (A[:,4] .*= -one(T))
    problem = LinearProblem(sparse(A), T[0,0,0,reverse ? 1 : -1,0];
        row_lower=zeros(T,2), row_upper=inequality ? fill(T(Inf),2) : zeros(T,2),
        column_lower=T[0,0,1,reverse ? -entering_limit : 0,0],
        column_upper=T[Inf,Inf,1,reverse ? 0 : entering_limit,Inf])
    options = SolverOptions(T; algorithm=:primal, simplex_strategy=:legacy,
        pricing=:dantzig, basis_update=update, refactorization_interval=1,
        primal_tolerance=tolerance, verbose=false)
    workspace = JSimplex.initialize_workspace(problem,options)
    workspace.basis.basic_indices .= [1,2]
    workspace.basis.states[1:2] .= JSimplex.BASIC
    workspace.basis.states[6:7] .= JSimplex.AT_LOWER
    workspace.basis.states[4] = reverse ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
    JSimplex.recompute!(workspace;refactorize=true)
    workspace.refactorizations = 0
    # This represents the feasible point maintained by an updated factor.
    # Its row error is delta; exact reconstruction instead gives (-1,2).
    workspace.primal[1] = zero(T)
    workspace.primal[2] = valid ? one(T) : zero(T)
    return workspace
end

@testset "A legacy primal zero step preserves a certified point across refactorization" begin
    for T in (Float32,Float64), update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl)
        workspace = zero_step_ill_conditioned_workspace(T,update)
        tolerance = workspace.options.primal_tolerance
        @test JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],tolerance)
        terminal = JSimplex._primal_iteration!(workspace,()->false,workspace.options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.iterations == 1
        @test workspace.refactorizations == 1
        @test workspace.basis.basic_indices == [4,2]
        @test JSimplex.primal_infeasibility(workspace) <= tolerance
        @test workspace.primal[4] == zero(T)
        @test JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],tolerance)
    end
end

@testset "Zero-step preservation rejects a point that violates the original rows" begin
    workspace = zero_step_ill_conditioned_workspace(Float64,:bartels_golub;valid=false)
    tolerance = workspace.options.primal_tolerance
    @test !JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],tolerance)
    JSimplex._primal_iteration!(workspace,()->false,workspace.options.dual_tolerance)
    @test JSimplex.primal_infeasibility(workspace) > tolerance
    @test !JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],tolerance)
end

@testset "Cancelled zero-step certification restores the reconstructed values" begin
    workspace = zero_step_ill_conditioned_workspace(Float64,:bartels_golub)
    candidate = JSimplex._legacy_primal_point_candidate(workspace,0,0,0.0,zeros(2))
    JSimplex.recompute!(workspace;refactorize=true)
    computed = copy(workspace.primal)
    calls = Ref(0)
    stop = () -> (calls[] += 1; calls[] >= 2)
    @test !JSimplex._restore_legacy_primal_point!(workspace,candidate,stop)
    @test calls[] == 2
    @test workspace.primal == computed
    # Caller exceptions after certification must restore the same values.
    calls[] = 0
    failure = ErrorException("caller stopped zero-step certification")
    throwing = () -> (calls[] += 1; calls[] >= 2 && throw(failure); false)
    @test_throws ErrorException JSimplex._restore_legacy_primal_point!(workspace,candidate,throwing)
    @test workspace.primal == computed
end

@testset "Zero-step preservation requires a consistent basis point" begin
    workspace = zero_step_ill_conditioned_workspace(Float64,:bartels_golub;inequality=true)
    workspace.primal[2] = 3.0
    tolerance = workspace.options.primal_tolerance
    @test JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],tolerance)
    @test maximum(abs, workspace.problem.A * workspace.primal[1:5] - workspace.primal[6:7]) > 1.0
    # Feasibility strictly inside an inequality does not justify keeping a
    # nonbasic row activity at a distant bound in this basis representation.
    JSimplex._primal_iteration!(workspace,()->false,workspace.options.dual_tolerance)
    @test JSimplex.primal_infeasibility(workspace) > tolerance
    @test workspace.primal[4] < 0.0
end

@testset "A nonzero legacy primal step preserves its certified predicted point" begin
    for T in (Float32, Float64), update in (:pfi, :bartels_golub, :forrest_tomlin, :suhl_suhl)
        workspace = zero_step_ill_conditioned_workspace(T, update)
        workspace.primal[1] = one(T)
        workspace.primal[2] = zero(T)
        tolerance = workspace.options.primal_tolerance
        @test JSimplex._original_primal_feasible(workspace.problem, workspace.primal[1:5], tolerance)
        terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.scratch.last_primal_step == one(T)
        @test workspace.basis.basic_indices == [4, 2]
        @test JSimplex.primal_infeasibility(workspace) <= tolerance
        @test workspace.primal[4] == one(T)
        @test JSimplex._original_primal_feasible(workspace.problem, workspace.primal[1:5], tolerance)
    end
end

@testset "Primal point fallback leaves other numerical policies alone" begin
    problem = LinearProblem(sparse([1.0 1.0]), [-1.0, 0.0]; row_upper=[1.0])
    for (algorithm, strategy) in ((:dual, :legacy), (:primal, :adaptive))
        options = SolverOptions(; algorithm, simplex_strategy=strategy, verbose=false)
        workspace = JSimplex.initialize_workspace(problem, options)
        @test isnothing(JSimplex._legacy_primal_point_candidate(workspace, 1, 0, 0.0, [1.0]))
    end
    for flag in (:pivot_validation, :solve_refinement, :recovery,
                 :incremental_primal, :incremental_primal_pivots, :adaptive_refactor)
        policy = JSimplex.NumericalPolicy(Float64; flag => true)
        progress = JSimplex.SimplexProgressContext(problem; numerical_policy=policy)
        workspace = JSimplex.initialize_workspace(problem,
            SolverOptions(algorithm=:primal, verbose=false); progress)
        @test isnothing(JSimplex._legacy_primal_point_candidate(workspace, 1, 0, 0.0, [1.0]))
    end
end

@testset "Row consistency certifies cancellation against stored activities" begin
    problem = LinearProblem(sparse([1e16 1.0 -1e16]), zeros(3))
    workspace = JSimplex.initialize_workspace(problem, SolverOptions(algorithm=:primal, verbose=false))
    workspace.primal[1:3] .= 1.0
    workspace.primal[4] = 1.0
    @test JSimplex._legacy_primal_row_consistent(workspace, 1e-7)
    workspace.primal[4] = 0.0
    @test !JSimplex._legacy_primal_row_consistent(workspace, 1e-7)
end


@testset "Certified primal predictions cover negative steps and bound flips" begin
    for reverse in (false, true), flip in (false, true)
        workspace = zero_step_ill_conditioned_workspace(Float64, :bartels_golub;
            reverse, entering_limit=flip ? 0.5 : Inf)
        workspace.primal[1] = 1.0
        workspace.primal[2] = 0.0
        terminal = JSimplex._primal_iteration!(workspace, () -> false, workspace.options.dual_tolerance)
        step = (reverse ? -1.0 : 1.0) * (flip ? 0.5 : 1.0)
        @test isnothing(terminal)
        @test workspace.scratch.last_primal_step == step
        @test workspace.basis.basic_indices == (flip ? [1, 2] : [4, 2])
        @test workspace.primal[4] == step
        @test JSimplex.primal_infeasibility(workspace) <= workspace.options.primal_tolerance
        @test JSimplex._legacy_primal_row_consistent(workspace, workspace.options.primal_tolerance)
    end
end

@testset "A sub-tolerance pivot retry preserves a certified current point" begin
    for T in (Float32,Float64), update in (:pfi,:bartels_golub,:forrest_tomlin,:suhl_suhl)
        workspace=zero_step_ill_conditioned_workspace(T,update)
        tiny=workspace.options.zero_tolerance/T(2)
        # A stale solve makes only the zero-valued first basic variable leave.
        # Refactorization reconstructs (-1,2), while (0,1) remains certified.
        workspace.factorization.base=JSimplex._factorize_basis(sparse(T[inv(tiny) 0;0 -1]))
        terminal=JSimplex._primal_iteration!(workspace,()->false,workspace.options.dual_tolerance)
        @test isnothing(terminal)
        @test workspace.iterations==1
        @test workspace.basis.basic_indices==[4,2]
        @test JSimplex.primal_infeasibility(workspace)<=workspace.options.primal_tolerance
        @test JSimplex._original_primal_feasible(workspace.problem,workspace.primal[1:5],workspace.options.primal_tolerance)
    end
end
