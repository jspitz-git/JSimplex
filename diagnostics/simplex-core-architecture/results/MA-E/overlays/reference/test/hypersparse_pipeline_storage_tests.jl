using Test,JSimplex,SparseArrays

function pipeline_workspace(::Type{T}=Float64;n=32,enabled=true,basis_update=:pfi,backend=:native) where T
    problem = LinearProblem(spdiagm(0=>ones(T,n)),zeros(T,n);row_lower=zeros(T,n))
    options = SolverOptions(T;simplex_strategy=:adaptive,pricing=:dantzig,verbose=false,
        basis_update,basis_refactorization=backend)
    policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,hypersparse=enabled,
        refactor_timing=false)
    return JSimplex.initialize_workspace(problem,options;
        progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy))
end

@testset "Pipeline owns support and borrows existing scratch values" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        ws = pipeline_workspace(T)
        cache = JSimplex._hypersparse_workspace!(ws)
        @test JSimplex._hypersparse_workspace!(ws) === cache
        for (i,name) in enumerate(JSimplex.HYPERSPARSE_BUFFER_FIELDS)
            @test cache.buffers[i].values === getfield(ws.scratch,name)
        end
        rhs = JSimplex._pipeline_unit_rhs!(ws,3)
        @test rhs === ws.scratch.row_rhs
        indexed = JSimplex._pipeline_vector!(ws,rhs)
        @test indexed.values == T[i==3 for i in 1:32]
        @test indexed.indices == [3]
        rebuilt = cache.support_rebuilds
        @test JSimplex._pipeline_vector!(ws,rhs) === indexed
        @test cache.support_rebuilds == rebuilt
        JSimplex._pipeline_column_rhs!(ws,5)
        @test indexed.values == T[i==5 for i in 1:32]
        @test indexed.indices == [5]
        JSimplex._pipeline_column_rhs!(ws,32+7)
        @test indexed.values == -T[i==7 for i in 1:32]
        @test indexed.indices == [7]
        @test cache.support_rebuilds == rebuilt
        JSimplex._pipeline_add!(ws,rhs,7,one(T))
        @test isempty(JSimplex._pipeline_vector!(ws,rhs).indices)
        # An accepted dense correction can create an entry outside old support.
        rhs[11] = T(2)
        JSimplex._pipeline_changed!(ws,rhs)
        @test JSimplex._pipeline_vector!(ws,rhs).indices == [11]
        @test cache.support_rebuilds == rebuilt+1
        @test rhs[11] == T(2)
        candidate = JSimplex._candidate_workspace(ws)
        other = JSimplex._hypersparse_workspace!(candidate)
        @test other !== cache
        @test other.buffers[1].values !== indexed.values
        @test other.buffers[1].indices !== indexed.indices
        @test other.buffers[1].membership !== indexed.membership
        @test other.modes === cache.modes # Measurements belong to the live phase.
        @test JSimplex._pipeline_vector!(candidate,candidate.scratch.row_rhs).indices == [11]
        JSimplex._pipeline_unit_rhs!(candidate,2)
        @test indexed.indices == [11] && rhs[11] == T(2)
        JSimplex._copy_pivot_state!(ws,candidate)
        @test JSimplex._pipeline_vector!(ws,rhs).indices == [2]
        @test rhs == T[i==2 for i in 1:32]
        JSimplex._invalidate_sparse_pricing_scratch!(ws.scratch)
        @test isnothing(ws.scratch.hypersparse)
        @test isnothing(ws.scratch.stage_scratch.hypersparse)
        @test JSimplex._hypersparse_workspace!(ws) !== cache
    end
end

@testset "Dense fallback retains the original scratch contract" begin
    ws = pipeline_workspace(;enabled=false)
    @test isnothing(ws.scratch.hypersparse)
    @test JSimplex._pipeline_unit_rhs!(ws,4) == Float64[i==4 for i in 1:32]
    @test JSimplex._pipeline_column_rhs!(ws,6) == Float64[i==6 for i in 1:32]
    @test isnothing(ws.scratch.hypersparse)
    @test !JSimplex.NumericalPolicy(Float64).hypersparse
    @test !JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive).hypersparse
end
