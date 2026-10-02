using SparseArrays

function postsolve_hint_workspace(T=Float64; manager=:pfi, profile=:native, strategy=:legacy, upper=nothing)
    problem=LinearProblem(sparse(T[0 1; 1 1]),T[0,-1];
        row_lower=[nothing,T(2)],row_upper=T[1,2],column_lower=T[0,0],column_upper=[upper,nothing])
    options=SolverOptions(T;basis_update=manager,verbose=false,scaling=:off,
        simplex_strategy=strategy)
    policy=JSimplex.NumericalPolicy(T;numerical_profile=profile)
    ws=JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    ws.basis=JSimplex.Basis([3,1],JSimplex.VariableState[
        JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    return ws
end

@testset "Postsolve can use an infeasible point as a basis hint" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub),
        strategy in (:legacy,:adaptive)
        ws=postsolve_hint_workspace(T;manager,strategy)
        target=T[1+1/1024,1]
        @test !JSimplex._original_primal_feasible(ws.problem,target,ws.options.primal_tolerance)
        @test JSimplex._project_postsolve_basis!(ws,target,()->false)==1
        @test ws.primal[1:2]==T[1,1]
        @test JSimplex._original_primal_feasible(ws.problem,ws.primal[1:2],ws.options.primal_tolerance)
        @test target==T[1+1/1024,1]
        fresh=postsolve_hint_workspace(T;manager,strategy)
        result=JSimplex.cleanup_original(fresh.problem,fresh.basis,fresh.options,
            JSimplex.SolveContext(time_ns(),Inf,nothing,fresh.progress.numerical_policy),0,0;
            target_primal=target)
        @test result.status==OPTIMAL
        @test result.objective_value==T(-1)
        @test result.primal==T[1,1]
    end
end

@testset "Postsolve hints retain cancellation and input guards" begin
    for target in ([NaN,1.0],[Inf,1.0],[1.0],[1.0,0.0],[1.0,2.0])
        ws=postsolve_hint_workspace()
        @test isnothing(JSimplex._project_postsolve_basis!(ws,target,()->false))
    end
    ws=postsolve_hint_workspace()
    before=copy(ws.basis.basic_indices)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,[1.001,1.0],()->true))
    @test ws.basis.basic_indices==before
    for T in (BigFloat,Rational{BigInt})
        ws=postsolve_hint_workspace(T)
        @test isnothing(JSimplex._project_postsolve_basis!(ws,T[1025//1024,1],()->false))
    end
    ws=postsolve_hint_workspace(Float64;profile=:checked)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,[1.001,1.0],()->false))
end

@testset "An infeasible reconstructed basis is still rejected" begin
    ws=postsolve_hint_workspace(Float64;upper=0.5)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,[1.001,1.0],()->false))
    @test !JSimplex._original_primal_feasible(ws.problem,ws.primal[1:2],ws.options.primal_tolerance)
end

@testset "Cleanup discards a hint exchange rejected by final certification" begin
    ws=postsolve_hint_workspace(Float64;upper=0.5)
    original_indices=copy(ws.basis.basic_indices)
    @test isnothing(JSimplex._project_postsolve_basis!(ws,[1.001,1.0],()->false))
    @test ws.basis.basic_indices!=original_indices
    fresh=postsolve_hint_workspace(Float64;upper=0.5)
    observed=Vector{Int}[]
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(reason,state)->begin
        reason==:phase_dual && push!(observed,copy(state.basis.basic_indices))
    end)
    result=JSimplex.cleanup_original(fresh.problem,fresh.basis,fresh.options,
        JSimplex.SolveContext(time_ns(),Inf,diagnostics,fresh.progress.numerical_policy),0,0;
        target_primal=[1.001,1.0])
    @test !isempty(observed)
    @test first(observed)==original_indices
    # This deliberately infeasible model must not be certified optimal. Compare
    # with ordinary cleanup to test rollback independently of its failure status.
    baseline=JSimplex.cleanup_original(fresh.problem,fresh.basis,fresh.options,
        JSimplex.SolveContext(time_ns(),Inf,nothing,fresh.progress.numerical_policy),0,0)
    @test result.status!=OPTIMAL
    @test result.status==baseline.status
    @test result.message==baseline.message
    @test result.iterations==baseline.iterations
end
