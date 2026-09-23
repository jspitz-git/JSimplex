using Random

@testset "Sparse pricing preserves arithmetic order, zeros, and precision" begin
    rng = MersenneTwister(16016)
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        for density in (0.0,0.1,1.0)
            A = sparse(T.(rand(rng,-3:3,9,13)))
            rho = JSimplex.IndexedVector{T}(9)
            values = T.(rand(rng,-3:3,9))
            for i in randperm(rng,9)
                rand(rng) <= density && JSimplex.add_entry!(rho,i,values[i])
            end
            original_indices = copy(rho.indices)
            out = JSimplex.IndexedVector{T}(22)
            JSimplex.sparse_price!(out,A,rho,JSimplex.RowAccess(A))
            reference = vcat(transpose(A)*rho.values,-rho.values)
            @test out.values == reference
            @test Set(out.indices) == Set(findall(!iszero,reference))
            @test rho.indices == original_indices
        end
        # Duplicate stored entries must retain all contributions and cancellation.
        A = SparseMatrixCSC(3,1,[1,4],[1,1,2],T[2,-2,3])
        rho = JSimplex.IndexedVector{T}(3)
        JSimplex.load_indexed!(rho,T[1,2,0])
        out = JSimplex.IndexedVector{T}(4)
        JSimplex.sparse_price!(out,A,rho,JSimplex.RowAccess(A))
        @test out.values == T[6,-1,-2,0]
        for (m,n) in ((0,0),(0,3),(3,0))
            A = spzeros(T,m,n)
            rhs = JSimplex.IndexedVector{T}(m)
            JSimplex.load_indexed!(rhs,ones(T,m))
            out = JSimplex.IndexedVector{T}(m+n)
            JSimplex.sparse_price!(out,A,rhs,JSimplex.RowAccess(A))
            @test out.values == vcat(zeros(T,n),-ones(T,m))
        end
    end
    for T in (Float32,Float64)
        A = sparse(reshape(T[1],1,1))
        rhs = JSimplex.IndexedVector{T}(1)
        JSimplex.add_entry!(rhs,1,nextfloat(zero(T)))
        out = JSimplex.IndexedVector{T}(2)
        JSimplex.sparse_price!(out,A,rhs,JSimplex.RowAccess(A))
        @test out.values == [nextfloat(zero(T)),-nextfloat(zero(T))]
        A.nzval[1] = floatmax(T)
        rows = JSimplex.RowAccess(A)
        JSimplex.set_entry!(rhs,1,T(2))
        @test_throws OverflowError JSimplex.sparse_price!(out,A,rhs,rows)
        JSimplex.clear!(out)
        @test isempty(out.indices) && all(iszero,out.values)
    end
    T = Rational{Int64}
    limit = typemax(Int64)//1
    A = sparse(reshape(T[limit,-limit,1],3,1))
    rhs,out = JSimplex.IndexedVector{T}(3),JSimplex.IndexedVector{T}(4)
    for i in (3,1,2)
        JSimplex.add_entry!(rhs,i,1//1)
    end
    JSimplex.sparse_price!(out,A,rhs,JSimplex.RowAccess(A))
    @test out.values == T[1,-1,-1,-1]
    # Sorted active rows would overflow here; preserve this custom CSC order.
    A = SparseMatrixCSC(3,1,[1,4],[2,3,1],T[limit,-limit,1])
    rows = JSimplex.RowAccess(A)
    @test !rows.ordered_csc
    JSimplex.sparse_price!(out,A,rhs,rows)
    @test out.values == T[1,-1,-1,-1]
    stored_A,stored_rhs,expected = setprecision(BigFloat,512) do
        a = BigFloat(1)+BigFloat(2)^(-200)
        sparse(reshape([a],1,1)),[BigFloat(1)],a
    end
    rows = JSimplex.RowAccess(stored_A)
    setprecision(BigFloat,64) do
        rho,out = JSimplex.IndexedVector{BigFloat}(1),JSimplex.IndexedVector{BigFloat}(2)
        JSimplex.load_indexed!(rho,stored_rhs)
        JSimplex.sparse_price!(out,stored_A,rho,rows)
        @test out.values[1] == expected && precision(out.values[1]) >= 512
    end
end

@testset "Sparse pricing checks aliases before changing matrix storage" begin
    for which in (:rowval,:colptr)
        A = sparse([1.0 2.0;3.0 4.0])
        saved = copy(A)
        rows = JSimplex.RowAccess(A)
        rhs,out = JSimplex.IndexedVector{Float64}(2),JSimplex.IndexedVector{Float64}(4)
        JSimplex.load_indexed!(rhs,[1.0,0.0])
        @test_throws ArgumentError JSimplex.sparse_price!(out,A,rhs,rows;
            ordered_rows=getfield(A,which))
        @test A.colptr == saved.colptr && A.rowval == saved.rowval && A.nzval == saved.nzval
    end
    ws = sparse_pricing_workspace(Float64)
    @test_throws DimensionMismatch JSimplex.price!(zeros(5),ws,[0.0,2.0])
    JSimplex.price!(zeros(4),ws,[0.0,2.0])
    candidate = JSimplex._candidate_workspace(ws)
    JSimplex._invalidate_basis_checkpoints!(ws)
    @test isnothing(ws.scratch.sparse_pricing)
    @test isnothing(candidate.scratch.sparse_pricing)
    ws.problem = LinearProblem(sparse([1.0 2.0 3.0]),zeros(3);row_upper=[1.0])
    out = zeros(4)
    JSimplex.price!(out,ws,[2.0])
    @test out == [2.0,4.0,6.0,-2.0]
    @test length(ws.scratch.sparse_pricing.rhs.values) == 1
end

@testset "Sparse row pricing retains independent simplex optima" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}), algorithm in (:primal,:dual), update in (:pfi,:forrest_tomlin)
        problem = LinearProblem(sparse(T[1 2;2 2]),T[1,3];row_lower=T[1,2])
        options = SolverOptions(T;algorithm,basis_update=update,pricing=:auto,
            simplex_strategy=:adaptive,presolve=false,verbose=false)
        policy = JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,
            sparse_pricing=true,refactor_timing=false)
        result = JSimplex._solve_diagnosed(problem,nothing;options,numerical_policy=policy)
        @test result.status == OPTIMAL
        if T <: Rational
            @test result.objective_value == one(T)
            @test result.primal == T[1,0]
        else
            @test isapprox(result.objective_value,one(T);atol=64eps(T),rtol=64eps(T))
            @test isapprox(result.primal,T[1,0];atol=64eps(T),rtol=64eps(T))
        end
        @test !isnothing(result.primal) && JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    end
end

@testset "Floating row products satisfy an independent residual bound" begin
    rng = MersenneTwister(16161)
    for T in (Float32,Float64,BigFloat), density in (0.05,0.4,1.0)
        A = sparse(T.(randn(rng,17,23)))
        values = T.(randn(rng,17))
        for i in eachindex(values)
            rand(rng) > density && (values[i]=zero(T))
        end
        rho,out = JSimplex.IndexedVector{T}(17),JSimplex.IndexedVector{T}(40)
        for i in randperm(rng,17)
            JSimplex.add_entry!(rho,i,values[i])
        end
        JSimplex.sparse_price!(out,A,rho,JSimplex.RowAccess(A))
        csc = zeros(T,40)
        JSimplex._csc_price!(csc,A,values)
        roundoff = eps(T)
        setprecision(BigFloat,max(256,precision(T)+64)) do
            for column in axes(A,2)
                products = [BigFloat(values[A.rowval[p]])*BigFloat(A.nzval[p]) for p in nzrange(A,column)]
                exact_reference = sum(products;init=BigFloat(0))
                allowance = BigFloat(2length(products))*BigFloat(roundoff)*sum(abs,products;init=BigFloat(0))
                @test abs(BigFloat(out.values[column])-exact_reference) <= allowance
                @test abs(BigFloat(csc[column])-exact_reference) <= allowance
            end
        end
        @test out.values[24:40] == -values
    end
end

@testset "Sparse pricing preserves the existing nonbinary Float32 outcome" begin
    for algorithm in (:primal,:dual), update in (:pfi,:forrest_tomlin)
        problem = LinearProblem(sparse(Float32[1 2;3 4]),Float32[1,3];row_lower=Float32[1,3])
        options = SolverOptions(Float32;algorithm,basis_update=update,pricing=:auto,
            simplex_strategy=:adaptive,presolve=false,verbose=false)
        results = map((false,true)) do enabled
            policy = JSimplex.NumericalPolicy(Float32;simplex_strategy=:adaptive,
                sparse_pricing=enabled,refactor_timing=false)
            JSimplex._solve_diagnosed(problem,nothing;options,numerical_policy=policy)
        end
        @test results[1].status == results[2].status
        @test results[1].objective_value == results[2].objective_value
        @test results[1].primal == results[2].primal
    end
end
