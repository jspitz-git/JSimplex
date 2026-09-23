using LinearAlgebra, SparseArrays, Random

@testset "Sparse solve rejects borrowed private support" begin
    view = JSimplex.sparse_solve_view(JSimplex._factorize_basis(spdiagm(0=>ones(3))))
    rhs = JSimplex.IndexedVector{Float64}(3)
    JSimplex.set_entry!(rhs,1,1.0)
    dest = JSimplex.IndexedVector(zeros(3),view.work.indices,zeros(UInt,3),UInt(1))
    @test_throws ArgumentError JSimplex.hypersparse_forward_solve!(dest,view,rhs)
    dest = JSimplex.IndexedVector(zeros(3),Int[],view.work.membership,UInt(1))
    @test_throws ArgumentError JSimplex.hypersparse_forward_solve!(dest,view,rhs)
end

@testset "Overflow leaves reusable solve scratch" begin
    for kind in (:native,:markowitz)
        B = spdiagm(0=>[1.0e-300,1.0])
        view = JSimplex.sparse_solve_view(JSimplex._factorize_basis(B,Val(kind)))
        rhs,dest = JSimplex.IndexedVector{Float64}(2),JSimplex.IndexedVector{Float64}(2)
        JSimplex.set_entry!(rhs,1,1.0e300)
        @test_throws OverflowError JSimplex.hypersparse_forward_solve!(dest,view,rhs)
        JSimplex.clear!(rhs); JSimplex.set_entry!(rhs,2,1.0)
        JSimplex.hypersparse_forward_solve!(dest,view,rhs)
        @test dest.values == [0.0,1.0]
        @test dest.indices == [2]
    end
end

@testset "UMFPACK public scaling convention is checked" begin
    for diagonal in ([1e-300,1e300],[2.0,4.0],[1.0,1.0])
        B = spdiagm(0=>diagonal)
        view = JSimplex.sparse_solve_view(JSimplex._factorize_basis(B))
        @test !isnothing(view)
        @test view.divide_scaling == (diagonal[1] == 1e-300)
        rhs,dest = JSimplex.IndexedVector{Float64}(2),JSimplex.IndexedVector{Float64}(2)
        JSimplex.load_indexed!(rhs,diagonal)
        JSimplex.hypersparse_forward_solve!(dest,view,rhs)
        @test dest.values ≈ ones(2)
        JSimplex.hypersparse_transpose_solve!(dest,view,rhs)
        @test dest.values ≈ ones(2)
    end
    # Neither interpretation is distinguishable from rounding at this scale.
    near = JSimplex._factorize_basis(spdiagm(0=>[nextfloat(1.0),1.0]))
    @test isnothing(JSimplex.sparse_solve_view(near))
end

@testset "Random base solves have independent high precision references" begin
    rng = MersenneTwister(1701)
    for trial in 1:8
        n = 8
        A = zeros(n,n)
        for i in 1:n, j in 1:n
            rand(rng) < 0.16 && (A[i,j] = rand(rng,-3:3))
        end
        for i in 1:n
            A[i,i] = 1+sum(abs,A[i,:])
        end
        A = sparse(A[randperm(rng,n),randperm(rng,n)])
        values = trial <= 4 ? [1.0;zeros(n-1)] : rand(rng,-3.0:3.0,n)
        for kind in (:native,:markowitz)
            view = JSimplex.sparse_solve_view(JSimplex._factorize_basis(A,Val(kind)))
            rhs,dest = JSimplex.IndexedVector{Float64}(n),JSimplex.IndexedVector{Float64}(n)
            JSimplex.load_indexed!(rhs,values)
            for transposed in (false,true)
                operation = transposed ? JSimplex.hypersparse_transpose_solve! : JSimplex.hypersparse_forward_solve!
                operation(dest,view,rhs)
                matrix = transposed ? transpose(A) : A
                reference = setprecision(BigFloat,256) do
                    Matrix{BigFloat}(matrix) \ BigFloat.(values)
                end
                @test norm(BigFloat.(dest.values)-reference,Inf) <=
                    128eps(Float64)*max(BigFloat(1),norm(reference,Inf))
                @test norm(dest.values-(matrix\values),Inf) <=
                    128eps(Float64)*max(1,norm(dest.values,Inf))
                @test Set(dest.indices) == Set(findall(!iszero,dest.values))
            end
        end
    end
end

@testset "Sparse substitution removes exact cancellation" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        B = sparse(T[1 0 0;2 1 0;0 0 1])
        view = JSimplex.sparse_solve_view(JSimplex.MarkowitzBackend(B))
        rhs,dest = JSimplex.IndexedVector{T}(3),JSimplex.IndexedVector{T}(3)
        JSimplex.load_indexed!(rhs,T[1,2,0])
        JSimplex.hypersparse_forward_solve!(dest,view,rhs)
        @test dest.values == T[1,0,0]
        @test dest.indices == [1]
        JSimplex.load_indexed!(rhs,T[2,1,0])
        JSimplex.hypersparse_transpose_solve!(dest,view,rhs)
        @test dest.values == T[0,1,0]
        @test dest.indices == [2]
    end
end
