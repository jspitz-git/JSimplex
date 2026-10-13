using LinearAlgebra, SparseArrays

@testset "Reusable reachable graph and empty factors" begin
    L = sparse([1.0 0 0 0; 2 1 0 0; 0 0 1 0; 0 0 3 1])
    g = JSimplex.SparseTriangularFactor(L)
    order = JSimplex.reachability_order(g,[1])
    @test order == [1,2]
    @test JSimplex.reachability_order(g,[3]) === order
    @test order == [3,4]
    g.reach.generation = typemax(UInt)
    @test JSimplex.reachability_order(g,[2];transposed=true) == [2,1]
    @test g.reach.generation == 1
    @test_throws BoundsError JSimplex.reachability_order(g,[5])
    @test JSimplex.reachability_order(g,[1,1]) == [1,2]
    @test_throws DimensionMismatch JSimplex.SparseTriangularFactor(spzeros(2,3))
    @test_throws ArgumentError JSimplex.SparseTriangularFactor(sparse([1.0 1;1 1]))
    @test_throws SingularException JSimplex.SparseTriangularFactor(spzeros(2,2))
    for kind in (:native,:markowitz)
        backend = JSimplex._factorize_basis(spzeros(0,0),Val(kind))
        view = JSimplex.sparse_solve_view(backend)
        rhs = JSimplex.IndexedVector{Float64}(0)
        @test isempty(JSimplex.hypersparse_forward_solve!(rhs,view,rhs).indices)
        @test isempty(JSimplex.hypersparse_transpose_solve!(rhs,view,rhs).indices)
    end
end

@testset "Mixed dense core and permuted sparse factors" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        B = Matrix{T}(I,12,12)
        B[10:12,10:12] .= T[4 1 2;1 5 1;2 1 6]
        backend = JSimplex.MarkowitzBackend(sparse(B))
        @test 0 < backend.sparse_pivots < 12
        view = JSimplex.sparse_solve_view(backend)
        rhs,dest = JSimplex.IndexedVector{T}(12),JSimplex.IndexedVector{T}(12)
        for index in (1,12)
            JSimplex.clear!(rhs); JSimplex.set_entry!(rhs,index,one(T))
            for operation in (JSimplex.hypersparse_forward_solve!,JSimplex.hypersparse_transpose_solve!)
                operation(dest,view,rhs)
                @test length(dest.indices) == (index == 1 ? 1 : 3)
                if T <: Rational
                    @test B*dest.values == rhs.values
                else
                    @test B*dest.values ≈ rhs.values
                end
            end
        end
        # Coupled leading elimination and a nontrivial external permutation.
        A = spdiagm(-1=>fill(-one(T),23),0=>fill(T(4),24),1=>fill(one(T),23))
        A = A[vcat(2:24,1),24:-1:1]
        backend = JSimplex.MarkowitzBackend(A)
        @test backend.sparse_pivots > 0
        view = JSimplex.sparse_solve_view(backend)
        rhs,dest = JSimplex.IndexedVector{T}(24),JSimplex.IndexedVector{T}(24)
        # Use B*x as RHS to keep fixed-width rational intermediates bounded.
        expected = ones(T,24)
        for transposed in (false,true)
            matrix = transposed ? transpose(A) : A
            JSimplex.load_indexed!(rhs,matrix*expected)
            operation = transposed ? JSimplex.hypersparse_transpose_solve! : JSimplex.hypersparse_forward_solve!
            operation(dest,view,rhs)
            if T <: Rational
                @test dest.values == expected
            else
                @test dest.values ≈ expected
            end
        end
    end
end

@testset "Owned snapshots survive backend reuse and solve aliases" begin
    for kind in (:native,:markowitz)
        B = spdiagm(-1=>fill(-1.0,11),0=>fill(4.0,12),1=>fill(1.0,11))
        backend = JSimplex._factorize_basis(B,Val(kind))
        old = JSimplex.sparse_solve_view(backend)
        for offset in (1.0,2.0,3.0)
            backend = JSimplex._refactorize_backend(backend,B+offset*I)
        end
        rhs = JSimplex.IndexedVector{Float64}(12)
        JSimplex.set_entry!(rhs,1,1.0)
        values = copy(rhs.values)
        JSimplex.hypersparse_forward_solve!(rhs,old,rhs)
        @test B*rhs.values ≈ values
        JSimplex.load_indexed!(rhs,values)
        JSimplex.hypersparse_transpose_solve!(rhs,old,rhs)
        @test transpose(B)*rhs.values ≈ values
        @test_throws ArgumentError JSimplex.hypersparse_forward_solve!(old.work,old,rhs)
        @test_throws ArgumentError JSimplex.hypersparse_forward_solve!(rhs,old,old.work)
        @test_throws DimensionMismatch JSimplex.hypersparse_forward_solve!(JSimplex.IndexedVector{Float64}(1),old,rhs)
        newer = JSimplex.sparse_solve_view(backend)
        @test old.work.values !== newer.work.values
        @test old.lower.reach.order !== newer.lower.reach.order
    end
    for T in (Float32,BigFloat,Rational{Int},Rational{BigInt})
        @test isnothing(JSimplex.sparse_solve_view(JSimplex._factorize_basis(Matrix{T}(I,2,2))))
    end
    singular = lu(sparse([1.0 1;1 1]);check=false)
    @test_throws SingularException JSimplex.sparse_solve_view(JSimplex.UMFPACKBackend(singular,2))
end

@testset "Sparse solve retains stored BigFloat precision" begin
    setprecision(BigFloat,256) do
        B = Matrix{BigFloat}(I,12,12)
        B[10:12,10:12] .= BigFloat[4 1 2;1 5 1;2 1 6]
        B[10,10] += BigFloat(2)^(-80)
        backend = JSimplex.MarkowitzBackend(sparse(B))
        rhs = JSimplex.IndexedVector{BigFloat}(12)
        JSimplex.set_entry!(rhs,12,BigFloat(1)+BigFloat(2)^(-90))
        dest = JSimplex.IndexedVector{BigFloat}(12)
        setprecision(BigFloat,24) do
            view = JSimplex.sparse_solve_view(backend)
            JSimplex.hypersparse_forward_solve!(dest,view,rhs)
        end
        @test norm(B*dest.values-rhs.values,Inf) < BigFloat(2)^(-240)
        @test all(i->precision(dest.values[i])>=256,dest.indices)
    end
end
