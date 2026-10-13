using Test, JSimplex, SparseArrays

@testset "Fixed correction activities do not become uncertified original basics" begin
    p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];
        column_lower=[1.0],row_lower=[1.0],row_upper=[2.0])
    options=SolverOptions(;verbose=false,presolve=false,scaling=:off)
    policy=JSimplex.NumericalPolicy(Float64;lp_refinement=true,refactor_timing=false)
    basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    ws=JSimplex.initialize_from_basis(p,basis,options;policy)
    r=JSimplex._lp_residuals(ws,[1.25,1.5],[1.0])
    correction,map=JSimplex.build_correction_problem(ws,r,4,8)
    auxiliary_basis=JSimplex.Basis([3],[JSimplex.AT_LOWER,JSimplex.AT_LOWER,JSimplex.BASIC])
    auxiliary=JSimplex.initialize_from_basis(correction,auxiliary_basis,options)
    @test auxiliary.primal==[-1.0,-2.0,1.0]
    @test bound_value(correction.row_lower[1])==1.0
    invalid_basis=JSimplex.Basis([2],[JSimplex.AT_LOWER,JSimplex.BASIC])
    @test !JSimplex._original_witness_certified(p,options,invalid_basis,[1.0],[1.0])
    saved=copy(ws.primal);saved_indices=copy(ws.basis.basic_indices)
    budget=JSimplex.SimplexRunBudget(ws)
    probe=JSimplex._lp_project_certificate(ws,auxiliary,map,[1.0,1.0],[1.0],budget,
        JSimplex._guard_stop_callback(()->false))
    @test !isnothing(probe)
    @test probe.basis.basic_indices==[1]
    @test probe.basis.states==[JSimplex.BASIC,JSimplex.AT_LOWER]
    @test probe.primal==[1.0,1.0] && probe.scratch.lp_dual_witness==[1.0]
    @test ws.primal==saved && ws.basis.basic_indices==saved_indices
    @test isempty(ws.scratch.checkpoints)
    # A nonbasic value in the interior cannot silently keep an old bound label.
    rejected=JSimplex._lp_project_certificate(ws,auxiliary,map,[1.5,1.5],[1.0],budget,
        JSimplex._guard_stop_callback(()->false))
    @test isnothing(rejected)
    @test isempty(ws.scratch.checkpoints)
end

@testset "Correction acceptance requires improvement without material degradation" begin
    options=SolverOptions(;primal_tolerance=1e-8,dual_tolerance=1e-8)
    @test JSimplex._lp_improves((1.0,1.0,1.0),(0.1,0.2,0.3),options)
    @test !JSimplex._lp_improves((1.0,1.0,1.0),(1.0,1.0,1.0),options)
    @test !JSimplex._lp_improves((1.0,1.0,1.0),(0.0,2.0,0.0),options)
    @test !JSimplex._lp_improves((1.0,1.0,1.0),(0.0,0.0,Inf),options)
end
