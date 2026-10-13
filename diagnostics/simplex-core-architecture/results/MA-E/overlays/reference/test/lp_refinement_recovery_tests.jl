using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "LP refinement recovery interface" begin
    @test isdefined(JSimplex, :refine_lp!)
end

function lp_recovery_fixture(; algorithm=:dual, diagnostics=nothing, memory=1<<30,
                               rounds=3, boost=false, time_limit=Inf)
    p = LinearProblem(sparse(reshape([1.0],1,1)),[1.0];
        row_lower=[1.0],row_upper=[2.0],column_lower=[0.0])
    policy = JSimplex.NumericalPolicy(Float64; lp_refinement=true, precision_boosting=boost,
        solve_refinement=false, recovery=false, max_lp_refinements=rounds,
        max_precision_memory_bytes=memory, refactor_timing=false)
    options = SolverOptions(;algorithm,verbose=false,presolve=false,scaling=:off,time_limit)
    basis = JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    progress = JSimplex.SimplexProgressContext(p;diagnostics,numerical_policy=policy)
    ws = JSimplex.initialize_from_basis(p,basis,options;policy,progress)
    # Fault injection: a finite inaccurate solve, with the original model and
    # primal unchanged. A correction must repair y=1/2 to the exact witness y=1.
    ws.factorization = JSimplex._basis_factorization(sparse(reshape([2.0],1,1)),options)
    return ws, policy
end

if isdefined(JSimplex, :refine_lp!)
    @testset "One LP correction repairs an inaccurate multiplier without boosting" begin
        for algorithm in (:primal,:dual)
            events = Tuple{Symbol,Int}[]
            witness = Ref{Union{Nothing,Vector{Float64}}}(nothing)
            diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
                push!(events,(reason,size(ws.problem.A,2)))
                if reason == :certification && size(ws.problem.A,2) == 1
                    witness[] = copy(ws.scratch.lp_dual_witness)
                end
            end)
            ws,policy = lp_recovery_fixture(;algorithm,diagnostics)
            @test !JSimplex._original_optimality_certified(ws,[1.0])
            before = copy(ws.primal)
            budget = JSimplex.SimplexRunBudget(ws)
            run = JSimplex.refine_lp!(ws,budget,policy,()->false)
            @test run isa JSimplex.DualRunResult{Float64}
            @test run.status == OPTIMAL
            @test run.primal == [1.0] && run.objective_value == 1.0
            @test witness[] == [1.0]
            @test run.basis.basic_indices == [1]
            @test JSimplex._original_witness_certified(ws.problem,ws.options,run.basis,run.primal,witness[])
            @test diagnostics.counts[:lp_refinement] == 1
            @test diagnostics.counts[:precision_boost] == 0
            @test any(first(e) == :phase_lp_refinement for e in events)
            @test all(last(e) == 1 for e in events if first(e) == :certification)
            @test budget.iterations == run.iterations
            @test budget.refactorizations == run.refactorizations
            @test ws.problem.A[1,1] == 1.0 && ws.problem.objective == [1.0]
            @test before == [1.0,1.0]
        end
    end
    @testset "LP recovery remains bounded and honors final cancellation" begin
        for (memory,rounds) in ((0,3),(1<<30,0))
            ws,policy = lp_recovery_fixture(;memory,rounds)
            run = JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
            @test run.status == NUMERICAL_ERROR
            @test isnothing(run.primal) && isnothing(run.objective_value)
        end
        ws,policy = lp_recovery_fixture()
        run = JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->true)
        @test run.status == TIME_LIMIT && isnothing(run.primal)
        stopped = Ref(false)
        diagnostics = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
            reason == :certification && size(ws.problem.A,2) == 1 && (stopped[]=true)
        end)
        ws,policy = lp_recovery_fixture(;diagnostics)
        run = JSimplex.refine_lp!(ws,JSimplex.SimplexRunBudget(ws),policy,()->stopped[])
        @test stopped[] && run.status == TIME_LIMIT && isnothing(run.primal)
    end
end
