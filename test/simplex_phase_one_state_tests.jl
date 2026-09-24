using Test,JSimplex,SparseArrays

@testset "Phase-one feasibility never accepts unrelated working bounds" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
    ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    ws.lower[2]=Bound(0.0)
    JSimplex.recompute!(ws)
    result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status == NUMERICAL_ERROR
    @test isnothing(result.primal)
end

@testset "Phase one retires owned working bounds before extending a basis" begin
    p=LinearProblem(sparse([1.0;;]),[1.0];row_lower=[1.0])
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true)
    ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    journal=JSimplex.PerturbationJournal(ws)
    journal.bounds=JSimplex.BoundPerturbationState(ws)
    journal.bounds.active_lower[2]=Bound(0.0)
    journal.bounds.active=true
    ws.lower=journal.bounds.active_lower
    ws.scratch.perturbations=journal
    JSimplex.recompute!(ws)
    result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status == OPTIMAL
    @test ws.primal[1]==1.0
    @test JSimplex._original_bounds_active(ws)
    @test isnothing(ws.scratch.perturbations)
    @test ws.costs==[1.0,0.0]
end

@testset "Artificial removal retires sparse row indices and pricing storage" begin
    p=LinearProblem(sparse(reshape([1.0,1.0],2,1)),[1.0];row_lower=ones(2),row_upper=ones(2))
    auxiliary_matrix=Ref{Any}(nothing)
    d=JSimplex.SimplexDiagnostics(;observer=(reason,phase)->begin
        if reason==:phase_one
            cache=JSimplex._sparse_pricing_workspace!(phase)
            auxiliary_matrix[]=cache.rows.matrix
        end
    end)
    policy=JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,phase_one=true,
        sparse_pricing=true,hypersparse=true)
    ws=JSimplex.initialize_workspace(p,SolverOptions(;algorithm=:primal,verbose=false,pricing=:auto);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
    result=JSimplex.run_phase_one!(ws,JSimplex.SimplexRunBudget(ws),policy,()->false)
    @test result.status==OPTIMAL
    @test !isnothing(auxiliary_matrix[])
    @test size(auxiliary_matrix[],2)==3
    @test length(ws.pricing_weights)==length(ws.devex_reference)==length(ws.scratch.tableau_row)==3
    @test isnothing(ws.scratch.stage_values)
    @test isnothing(ws.scratch.perturbations)
    @test all(c->length(c.basis.states)==3,ws.scratch.checkpoints)
    cache=JSimplex._sparse_pricing_workspace!(ws)
    @test cache.rows.matrix===p.A
    @test cache.rows.matrix!==auxiliary_matrix[]
    @test length(cache.out.values)==3
end
