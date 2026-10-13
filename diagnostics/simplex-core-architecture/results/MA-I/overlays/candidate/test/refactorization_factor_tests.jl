using SparseArrays, LinearAlgebra

@testset "Refactorization metrics follow active factor storage" begin
    for T in (Float64,BigFloat), update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl),
        backend in (:native,:markowitz)
        p = LinearProblem(spdiagm(0=>ones(T,2)),-ones(T,2);row_upper=ones(T,2))
        options = SolverOptions(T;verbose=false,basis_update=update,basis_refactorization=backend)
        policy = JSimplex.NumericalPolicy(T;adaptive_refactor=true,refactor_timing=false)
        ws = JSimplex.initialize_workspace(p,options;
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        state = ws.scratch.refactorization
        @test state.base_elements == JSimplex._factor_storage_count(ws.factorization)
        @test state.stored_elements == state.base_elements
        JSimplex.replace_column!(ws.factorization,T[1,10^10],1;zero_tolerance=zero(T))
        JSimplex._refresh_refactor_metrics!(ws;force=true)
        @test state.nupdates == 1
        @test state.stored_elements == JSimplex._factor_storage_count(ws.factorization)
        @test state.growth_scale > state.growth_limit
        @test JSimplex.refactor_reason(state,policy) == :pivot_growth
        state.growth_limit = Inf
        state.fill_limit = 0.5
        @test JSimplex.refactor_reason(state,policy) == :fill
    end
end

@testset "Growth and fill rebuilds do not earn healthy-cycle growth" begin
    for reason in (:refactor_growth,:refactor_fill)
        p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
        ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
        state = ws.scratch.refactorization
        JSimplex.replace_column!(ws.factorization,[-1.0],1;zero_tolerance=0.0)
        state.productive_updates = 1
        state.healthy_cycles = 2
        JSimplex._before_basis_refactor!(ws,reason)
        @test state.interval == state.initial_interval
        @test state.healthy_cycles == 0
    end
end

@testset "Factor state follows candidate ownership and rollback" begin
    p = LinearProblem(sparse([1.0;;]),[-1.0];row_upper=[1.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,refactor_timing=false)
    ws = JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig);
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy))
    state = ws.scratch.refactorization
    state.timing_depth = 1
    auxiliary = JSimplex._auxiliary_workspace(ws)
    @test auxiliary.scratch.refactorization !== state
    @test auxiliary.scratch.refactorization.timing_depth == 0
    @test state.timing_depth == 1
    state.timing_depth = 0
    candidate = JSimplex._candidate_workspace(ws)
    @test candidate.scratch.refactorization === state
    JSimplex.record_basis_cost!(state,:fresh,1.0)
    JSimplex.apply_primal_pivot!(candidate,1,1,1.0,[-1.0],[-1.0,1.0];
        leaving_state=JSimplex.AT_UPPER)
    JSimplex._refresh_refactor_metrics!(candidate;force=true)
    @test state.nupdates == 1
    JSimplex._discard_candidate!(ws,candidate)
    @test state.nupdates == 0
    @test state.fresh_samples == 1
    @test state.stored_elements == state.base_elements
    @test ws.iterations == 0
    @test ws.basis.basic_indices == [2]
end
