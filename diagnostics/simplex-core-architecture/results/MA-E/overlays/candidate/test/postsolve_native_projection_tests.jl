using Test, JSimplex, SparseArrays, LinearAlgebra

function postsolve_native_projection_fixture(T;algorithm=:dual,manager=:huangfu_hall,diagnostics=nothing,max_refinements=3)
    A=sparse(T[4 4 0 -5 1;3 2 -1 4 -3;0 -4 4 -5 2;-3 1 0 5 3;0 0 -4 -4 -3])
    # The last equation is homogeneous. A fresh native solve of the final
    # basis leaves tiny terms that fail original feasibility at this scale.
    target=T[1,2,0,0,0] * T(2)^(T===Float32 ? 12 : 30)
    rhs=A*target
    @assert rhs[5]==0
    p=LinearProblem(A,zeros(T,5);row_lower=rhs,row_upper=rhs,column_lower=fill(nothing,5))
    options=SolverOptions(T;algorithm,basis_update=manager,presolve=false,scaling=:off,verbose=false)
    progress=JSimplex.SimplexProgressContext(p;diagnostics,
        numerical_policy=JSimplex.NumericalPolicy(T;max_refinements))
    ws=JSimplex.initialize_workspace(p,options;progress)
    # Only the first two structural columns need projection; retain the other
    # three so the final factorization has the failing native LU structure.
    ws.basis=JSimplex.Basis([6,7,3,4,5], [JSimplex.FREE_NONBASIC,JSimplex.FREE_NONBASIC,JSimplex.BASIC,JSimplex.BASIC,JSimplex.BASIC,JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(ws;refactorize=true)
    return ws,target
end
@testset "Postsolve projection repairs native reconstruction before rejection" begin
    for T in (Float32,Float64),algorithm in (:primal,:dual),manager in (:pfi,:huangfu_hall)
        diagnostics=JSimplex.SimplexDiagnostics()
        ws,target=postsolve_native_projection_fixture(T;algorithm,manager,diagnostics)
        @test JSimplex._original_primal_feasible(ws.problem,target,ws.options.primal_tolerance)
        exchanges=JSimplex._project_postsolve_basis!(ws,target,()->false)
        @test exchanges==2
        @test JSimplex._original_primal_feasible(ws.problem,ws.primal[1:5],ws.options.primal_tolerance)
        @test ws.primal[1:5]==target
        T===Float64 && (@test JSimplex.event_count(diagnostics,:correction_attempt)>0)
    end
end

@testset "Postsolve native repair respects its budget and deadline" begin
    for manager in (:pfi,:huangfu_hall)
        diag=JSimplex.SimplexDiagnostics()
        ws,target=postsolve_native_projection_fixture(Float64;manager,diagnostics=diag,max_refinements=0)
        @test isnothing(JSimplex._project_postsolve_basis!(ws,target,()->false))
        @test JSimplex.event_count(diag,:correction_attempt)==0
        ws,target=postsolve_native_projection_fixture(Float64;manager)
        before=deepcopy((ws.primal,ws.basis.basic_indices,ws.basis.states))
        @test isnothing(JSimplex._project_postsolve_basis!(ws,target,()->true))
        @test (ws.primal,ws.basis.basic_indices,ws.basis.states)==before
    end
end
