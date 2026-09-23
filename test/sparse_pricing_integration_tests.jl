function sparse_pricing_workspace(::Type{T};enabled=true) where T
    problem = LinearProblem(sparse(T[1 2;3 4]),T[1,2];row_lower=T[1,2])
    options = SolverOptions(T;simplex_strategy=:adaptive,pricing=:auto,verbose=false)
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,sparse_pricing=enabled,
        refactor_timing=false)
    return JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
end

@testset "Sparse pricing integrates through an independent opt-in switch" begin
    @test :sparse_pricing in JSimplex.IMPLEMENTED_NUMERICAL_SWITCHES
    if :sparse_pricing in JSimplex.IMPLEMENTED_NUMERICAL_SWITCHES
        @test !JSimplex.NumericalPolicy(Float64).sparse_pricing
        @test !JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive).sparse_pricing
        for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
            ws = sparse_pricing_workspace(T)
            @test isnothing(ws.scratch.sparse_pricing)
            rho,out = T[0,2],zeros(T,4)
            JSimplex.price!(out,ws,rho)
            @test out == T[6,8,0,-2]
            cache = ws.scratch.sparse_pricing
            @test cache.rows.matrix === ws.problem.A
            JSimplex.price!(out,ws,T[1,0])
            @test out == T[1,2,-1,0]
            @test ws.scratch.sparse_pricing === cache
            ws.scratch.tableau_row .= T(7)
            JSimplex.price!(ws.scratch.pricing_row,ws,rho)
            @test ws.scratch.tableau_row == fill(T(7),4)
            candidate = JSimplex._candidate_workspace(ws)
            copy_cache = candidate.scratch.sparse_pricing
            @test copy_cache !== cache && copy_cache.rows === cache.rows
            @test copy_cache.rhs.values !== cache.rhs.values
            @test copy_cache.out.values !== cache.out.values
            JSimplex.price!(out,candidate,T[2,0])
            @test cache.rhs.values == rho
            old_rows = cache.rows
            JSimplex._invalidate_basis_checkpoints!(ws)
            JSimplex.price!(out,ws,rho)
            @test ws.scratch.sparse_pricing.rows !== old_rows
            @test out == T[6,8,0,-2]
            fresh = LinearProblem(sparse(T[2 0;0 3]),T[1,2];row_lower=T[1,2])
            ws.problem = fresh
            JSimplex.price!(out,ws,rho)
            @test out == T[0,6,0,-2]
            @test ws.scratch.sparse_pricing.rows.matrix === fresh.A
            dense_ws = sparse_pricing_workspace(T;enabled=false)
            JSimplex.price!(out,dense_ws,rho)
            @test out == T[6,8,0,-2]
            @test isnothing(dense_ws.scratch.sparse_pricing)
        end
        ws = sparse_pricing_workspace(Float64)
        candidate = JSimplex._candidate_workspace(ws)
        out = zeros(4)
        JSimplex.price!(out,candidate,[0.0,2.0])
        cache = candidate.scratch.sparse_pricing
        @test isnothing(ws.scratch.sparse_pricing)
        @test JSimplex._candidate_workspace(ws).scratch.sparse_pricing === cache
    end
end

@testset "Lazy row indexing is timed once per working phase" begin
    diagnostics = JSimplex.SimplexDiagnostics(kernel_timing=true)
    problem = LinearProblem(sparse([1.0 2.0;3.0 4.0]),[1.0,3.0];row_lower=[1.0,2.0])
    policy = JSimplex.NumericalPolicy(Float64;sparse_pricing=true)
    ws = JSimplex.initialize_workspace(problem,SolverOptions(verbose=false);
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    @test haskey(diagnostics.kernel_calls,:row_index)
    out = zeros(4)
    JSimplex.price!(out,ws,[0.0,2.0])
    JSimplex.price!(out,ws,[1.0,0.0])
    @test get(diagnostics.kernel_calls,:row_index,0) == 1
    JSimplex._invalidate_basis_checkpoints!(ws)
    JSimplex.price!(out,ws,[0.0,2.0])
    @test get(diagnostics.kernel_calls,:row_index,0) == 2
    candidate = JSimplex._candidate_workspace(ws)
    JSimplex.price!(out,candidate,[1.0,0.0])
    @test get(diagnostics.kernel_calls,:row_index,0) == 2
end
