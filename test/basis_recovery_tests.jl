using SparseArrays, Logging

struct BasisRecoveryThrowLogger{E} <: AbstractLogger
    failure::E
end

@testset "Discarded recovery candidates retain the triggering pivot pair" begin
    p = LinearProblem(sparse([1.0;;]),[0.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
    @test_throws JSimplex._PivotRejection JSimplex._transactional_simplex_step!(w,()->false) do candidate,stop
        candidate.scratch.selected_row = 1
        candidate.scratch.selected_entering = 1
        throw(JSimplex._PivotRejection(1,1,:refresh))
    end
    @test (w.scratch.selected_row,w.scratch.selected_entering) == (1,1)
    @test w.iterations == 0 && w.basis.basic_indices == [2]
end
Logging.min_enabled_level(::BasisRecoveryThrowLogger) = Logging.Debug
Logging.shouldlog(::BasisRecoveryThrowLogger,args...) = true
Logging.catch_exceptions(::BasisRecoveryThrowLogger) = false
function Logging.handle_message(logger::BasisRecoveryThrowLogger,level,message,args...;kwargs...)
    message == "Rebuilding recovery basis" && throw(logger.failure)
end

@testset "Basis checkpoints own working data and preserve consumed work" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p = LinearProblem(sparse(T[1;;]),T[1];row_lower=T[1])
        w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
        c = JSimplex.checkpoint_basis(w)
        w.costs[1] = T(7)
        w.lower[1] = Bound(T(-2))
        w.iterations = 9
        old_refactors = w.refactorizations
        old_factor = w.factorization
        @test c.costs[1] == one(T)
        @test bound_value(c.lower[1]) == zero(T)
        @test JSimplex.restore_checkpoint!(w,c,()->false)
        @test w.iterations == 9
        @test w.costs[1] == one(T)
        @test w.refactorizations == old_refactors+1
        @test w.factorization !== old_factor
        @test w.basis.basic_indices !== c.basis.basic_indices
        @test w.costs !== c.costs
        @test w.primal == T[0,0]
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve(w.factorization,T[1]) == T[1]
    end
end

@testset "Repair failures preserve the live basis and the saved checkpoint" begin
    p = LinearProblem(sparse([2.0;;]),[1.0])
    policy = JSimplex.NumericalPolicy(Float64)
    for reason in (:repair,:checkpoint)
        failure = JSimplex.SingularException(23)
        diagnostics = JSimplex.SimplexDiagnostics(;observer=(event,state)->begin
            event == reason && throw(failure)
        end)
        w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
            progress=JSimplex.SimplexProgressContext(p;diagnostics))
        saved = JSimplex.checkpoint_basis(w)
        push!(w.scratch.checkpoints,saved)
        old_factor = w.factorization
        caught = try
            JSimplex.repair_basis!(w,policy,()->false)
            nothing
        catch e
            e
        end
        @test caught isa JSimplex.DiagnosticObserverFailure
        @test caught.cause === failure
        @test w.factorization === old_factor && w.basis.basic_indices == [2]
        @test w.scratch.checkpoints == [saved]
        @test saved.costs == [1.0,0.0]
        @test diagnostics.counts[:repair] == 0
    end
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    c = JSimplex.checkpoint_basis(w)
    old_factor = w.factorization
    before = w.refactorizations
    @test !JSimplex.repair_basis!(w,policy,()->w.refactorizations>before)
    @test w.refactorizations == before+1
    @test w.factorization === old_factor && w.basis.basic_indices == c.basis.basic_indices
    failure = JSimplex.SingularException(29)
    before = w.refactorizations
    caught = try
        with_logger(BasisRecoveryThrowLogger(failure)) do
            JSimplex.restore_checkpoint!(w,c,()->false)
        end
        nothing
    catch e
        e
    end
    @test caught === failure
    @test w.factorization === old_factor && w.refactorizations == before
    empty_problem = LinearProblem(spzeros(1,0),Float64[])
    empty_ws = JSimplex.initialize_workspace(empty_problem,SolverOptions(verbose=false))
    @test !JSimplex.repair_basis!(empty_ws,policy,()->false)
    @test empty_ws.refactorizations == 0
end

@testset "Recovery rejection pairs belong to one basis generation" begin
    p = LinearProblem(sparse([1.0;;]),[0.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    policy = JSimplex.NumericalPolicy(Float64;recovery=true,max_pivot_candidates=2)
    JSimplex._reject_recovery_pair!(w,1,1,policy)
    candidate = JSimplex.PivotCandidate(1,1,-1.0,[-1.0],[-1.0])
    @test JSimplex.validate_pivot!(w,candidate,policy) == :reject_candidate
    w.basis.basic_indices .= [1]
    w.basis.states .= [JSimplex.BASIC,JSimplex.FREE_NONBASIC]
    JSimplex.recompute!(w;refactorize=true)
    candidate = JSimplex.PivotCandidate(2,1,-1.0,[-1.0],[1.0])
    @test JSimplex.validate_pivot!(w,candidate,policy) == :accept
    @test isempty(w.scratch.recovery_rejections)
    for entering in 1:10
        JSimplex._reject_recovery_pair!(w,1,entering,policy)
    end
    @test length(w.scratch.recovery_rejections) == 2
end

@testset "Exhausted pivot refresh repairs the basis before resuming dual" begin
  for checked in (false,true)
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0]),[0.0,0.0];
        column_lower=[1.0,0.0],row_lower=[1.0,2.0])
    options = SolverOptions(verbose=false,pricing=:dantzig,simplex_strategy=:adaptive)
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,pivot_validation=checked)
    w = JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    w.basis.basic_indices .= [1,2]
    w.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]
    w.primal[1] = 0.0
    w.iterations = 11
    result = try
        JSimplex._dual_iteration!(w,JSimplex._guard_stop_callback(()->false))
    catch e
        e
    end
    @test result isa JSimplex.DualTermination
    if result isa JSimplex.DualTermination
        @test result.status == OPTIMAL
    end
    @test w.basis.basic_indices != [1,2]
    @test w.iterations == 11
    @test JSimplex.primal_infeasibility(w) == 0.0
    @test JSimplex.basis_matrix(w)*JSimplex.forward_solve(w.factorization,[1.0,2.0]) ≈ [1.0,2.0]
  end
end

@testset "Adaptive checkpoints are opt-in and phase-local" begin
    p = LinearProblem(sparse([1.0;;]),[1.0])
    legacy = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    @test isempty(legacy.scratch.checkpoints)
    adaptive = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
    @test adaptive.progress.numerical_policy.recovery
    @test length(adaptive.scratch.checkpoints) == 1
    c = JSimplex.checkpoint_basis(adaptive)
    JSimplex._restore_original_costs!(adaptive)
    @test isempty(adaptive.scratch.checkpoints)
    @test !JSimplex.restore_checkpoint!(adaptive,c,()->false)
end

@testset "Exhausted repair restores perturbations without replaying the budget" begin
    p = LinearProblem(spzeros(1,0),Float64[];row_lower=[-2.0],row_upper=[2.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    w.costs[1] = 3.0
    w.lower[1] = Bound(-1.0)
    w.upper[1] = Bound(1.0)
    w.perturbed = true
    JSimplex.recompute!(w)
    @test JSimplex._remember_verified_basis!(w,()->false)
    w.costs[1] = 8.0
    w.upper[1] = Bound(9.0)
    w.perturbed = false
    w.iterations = 19
    w.scratch.selected_row = 1
    w.scratch.selected_entering = 1
    policy = JSimplex.NumericalPolicy(Float64)
    @test !JSimplex.repair_basis!(w,policy,()->false)
    @test w.iterations == 19
    @test w.costs == [3.0] && bound_value(w.upper[1]) == 1.0 && w.perturbed
    @test (1,1) in w.scratch.recovery_rejections
end

@testset "Recovery rebuilds edge weights and respects stored precision" begin
    p = LinearProblem(sparse([2.0 0.0;0.0 4.0]),[1.0,1.0])
    for update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl), backend in (:native,:markowitz)
        options = SolverOptions(verbose=false,pricing=:steepest_edge,
            basis_update=update,basis_refactorization=backend)
        w = JSimplex.initialize_workspace(p,options)
        w.basis.basic_indices .= [1,2]
        w.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.FREE_NONBASIC,JSimplex.FREE_NONBASIC]
        JSimplex.recompute!(w;refactorize=true)
        c = JSimplex.checkpoint_basis(w)
        w.pricing_weights .= NaN
        @test JSimplex.restore_checkpoint!(w,c,()->false)
        @test w.pricing_weights[1:2] ≈ [1/4,1/16]
        @test !any(w.scratch.steepest_valid)
    end
    setprecision(BigFloat,384) do
        delta = BigFloat(2)^(-180)
        p = LinearProblem(sparse(BigFloat[1 1;1 1+delta]),BigFloat[0,0];row_lower=BigFloat[1,1+delta])
        w = JSimplex.initialize_workspace(p,SolverOptions(BigFloat;verbose=false))
        w.basis.basic_indices .= [1,2]
        w.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER]
        JSimplex.recompute!(w;refactorize=true)
        c = JSimplex.checkpoint_basis(w)
        setprecision(BigFloat,96) do
            @test JSimplex.restore_checkpoint!(w,c,()->false)
            @test precision(BigFloat) == 96
        end
        @test JSimplex.forward_solve(w.factorization,BigFloat[0,delta]) ≈ BigFloat[-1,1]
        @test w.primal[1:2] == BigFloat[0,1]
    end
end

@testset "Checkpoint validation, deadlines and observer failures are atomic" begin
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0]),[1.0,2.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false))
    c = JSimplex.checkpoint_basis(w)
    other = JSimplex.initialize_workspace(deepcopy(p),SolverOptions(verbose=false))
    @test !JSimplex.restore_checkpoint!(other,c,()->false)
    old_factor = w.factorization
    old_basis = copy(w.basis.basic_indices)
    bad = deepcopy(c)
    bad.basis.basic_indices .= [1,2]
    bad.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.FREE_NONBASIC,JSimplex.FREE_NONBASIC]
    @test !JSimplex.restore_checkpoint!(w,bad,()->false)
    @test w.basis.basic_indices == old_basis && w.factorization === old_factor
    @test c.basis.basic_indices == old_basis
    before = w.refactorizations
    @test !JSimplex.restore_checkpoint!(w,c,()->w.refactorizations>before)
    @test w.refactorizations == before+1
    @test w.factorization === old_factor
    failure = JSimplex.SingularException(17)
    caught = try
        JSimplex.restore_checkpoint!(w,c,()->throw(failure))
        nothing
    catch e
        e
    end
    @test caught === failure
    @test w.factorization === old_factor
    JSimplex._invalidate_basis_checkpoints!(w)
    @test !JSimplex.restore_checkpoint!(w,c,()->false)

    diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason == :restore_checkpoint && throw(failure)
    end)
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    c = JSimplex.checkpoint_basis(w)
    w.costs[1] = 11.0
    old_factor = w.factorization
    caught = try
        JSimplex.restore_checkpoint!(w,c,()->false)
        nothing
    catch e
        e
    end
    @test caught isa JSimplex.DiagnosticObserverFailure
    @test caught.cause === failure
    @test w.costs[1] == 11.0 && w.factorization === old_factor
    @test diagnostics.counts[:restore_checkpoint] == 0
    @test c.costs == [1.0,2.0,0.0,0.0]
end

@testset "Verified history is bounded and repair changes a singular basis" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p = LinearProblem(sparse(T[1 1;1 1]),T[1,2])
        w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
        for i in 1:4
            w.costs[1] = T(i)
            JSimplex.recompute!(w)
            @test JSimplex._remember_verified_basis!(w,()->false)
        end
        @test length(w.scratch.checkpoints) == 2
        @test [c.costs[1] for c in w.scratch.checkpoints] == T[3,4]
        saved = deepcopy(w.scratch.checkpoints)
        # Distinct structural columns are linearly dependent. Fresh LU of this
        # same basis cannot recover it; one basis column must change.
        w.basis.basic_indices .= [1,2]
        w.basis.states .= [JSimplex.BASIC,JSimplex.BASIC,JSimplex.FREE_NONBASIC,JSimplex.FREE_NONBASIC]
        w.scratch.selected_row = 1
        w.scratch.selected_entering = 1
        w.iterations = 11
        @test_throws JSimplex.SingularException JSimplex._basis_factorization(JSimplex.basis_matrix(w),w.options)
        policy = JSimplex.NumericalPolicy(T;max_pivot_candidates=4)
        @test JSimplex.repair_basis!(w,policy,()->false)
        @test w.basis.basic_indices != [1,2]
        @test w.iterations == 11
        @test JSimplex.basis_matrix(w)*JSimplex.forward_solve(w.factorization,T[1,2]) ≈ T[1,2]
        @test saved[1].costs[1] == T(3)
        @test length(w.scratch.checkpoints) <= 2
    end
end

@testset "Recovery never combines trigger coordinates from different candidates" begin
    p = LinearProblem(sparse([1.0;1.0;;]),[0.0])
    w = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,simplex_strategy=:adaptive))
    for (row,entering,expected) in ((1,1,(1,1)),(2,0,(2,0)),(0,2,(0,2)),(0,0,(0,2)))
        @test_throws JSimplex._PivotRejection JSimplex._transactional_simplex_step!(w,()->false) do c,stop
            c.scratch.selected_row = row
            c.scratch.selected_entering = entering
            throw(JSimplex._PivotRejection(row,entering,:refresh))
        end
        @test (w.scratch.selected_row,w.scratch.selected_entering) == expected
    end
end
