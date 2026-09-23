using SparseArrays

function partial_pricing_workspace(::Type{T};algorithm=:primal,enabled=true,observer=nothing) where T
    problem = algorithm == :primal ?
        LinearProblem(spzeros(T,1,129),zeros(T,129);row_upper=T[1],column_upper=ones(T,129)) :
        LinearProblem(spzeros(T,129,1),T[0];row_lower=fill(-one(T),129))
    options = SolverOptions(T;algorithm,pricing=:dantzig,simplex_strategy=:adaptive,verbose=false)
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
        partial_pricing=enabled,refactor_timing=false)
    diagnostics = JSimplex.SimplexDiagnostics(;observer)
    ws = JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    return ws,policy,diagnostics
end

@testset "Partial pricing cannot certify an exhausted first block" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        ws,policy,_ = partial_pricing_workspace(T)
        ws.costs[129] = ws.reduced_costs[129] = -one(T)
        pool = JSimplex.CandidatePool(;algorithm=:primal,block_size=64)
        @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 129
        @test pool.scanned_entries >= 129
        @test JSimplex.select_pricing_candidate!(ws,pool,policy;force_full=true) == 129
        ws.costs[129] = ws.reduced_costs[129] = one(T)
        @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
        @test pool.full_scan
        @test pool.full_scans > 0
    end
end

@testset "Current scores, validity, and deterministic full scans" begin
    for algorithm in (:primal,:dual)
        ws,policy,_ = partial_pricing_workspace(Float64;algorithm)
        pool = JSimplex.CandidatePool(;algorithm,block_size=64)
        if algorithm == :primal
            ws.reduced_costs[1] = -1.0
            ws.reduced_costs[129] = -10.0
        else
            ws.primal[ws.basis.basic_indices[1]] = -2.0
            ws.primal[ws.basis.basic_indices[129]] = -11.0
        end
        @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 1
        @test pool.scanned_entries == 64
        @test !pool.full_scan
        @test JSimplex.select_pricing_candidate!(ws,pool,policy;force_full=true) == 129
        if algorithm == :primal
            ws.reduced_costs[1] = -10.0
        else
            ws.primal[ws.basis.basic_indices[1]] = -11.0
        end
        @test JSimplex.select_pricing_candidate!(ws,pool,policy;force_full=true) == 1
        if algorithm == :primal
            ws.lower[1] = ws.upper[1]
        else
            ws.primal[ws.basis.basic_indices[1]] = 0.0
        end
        @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 129
        if algorithm == :primal
            ws.basis.states[129] = JSimplex.BASIC
        else
            ws.primal[ws.basis.basic_indices[129]] = 0.0
        end
        @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
        @test pool.full_scan
    end
end

@testset "An absent cached candidate requires a complete current scan" begin
    ws,policy,_ = partial_pricing_workspace(Float64)
    pool = JSimplex.CandidatePool(;algorithm=:primal,block_size=64)
    ws.reduced_costs[1] = -1.0
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 1
    ws.reduced_costs[1] = 0.0
    ws.reduced_costs[129] = -1.0
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 129
    # Previously scanned blocks may become eligible after a completed step.
    ws.reduced_costs[129] = 0.0
    ws.reduced_costs[2] = -1.0
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 2
    ws.reduced_costs[2] = 0.0
    @test JSimplex.select_pricing_candidate!(ws,pool,policy) == 0
    @test pool.full_scan
end

@testset "Partial pricing is adaptive and keeps small domains on full scans" begin
    @test !JSimplex.NumericalPolicy(Float64).partial_pricing
    @test JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive).partial_pricing
    @test !JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,partial_pricing=false).partial_pricing
    problem = LinearProblem(sparse([1.0 1.0]),[-1.0,-2.0];row_upper=[1.0])
    policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,partial_pricing=true)
    ws = JSimplex.initialize_workspace(problem,SolverOptions(verbose=false,pricing=:dantzig);
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
    @test first(JSimplex._primal_entering(ws,ws.options.dual_tolerance)) == 2
    @test isnothing(ws.scratch.pricing_pool)
    @test_throws ArgumentError JSimplex.CandidatePool(;block_size=0)
    @test_throws ArgumentError JSimplex.CandidatePool(;algorithm=:unknown)
end
