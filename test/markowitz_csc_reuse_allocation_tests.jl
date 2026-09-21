using SparseArrays, LinearAlgebra

markowitz_csc_measure(B) = @timed JSimplex.MarkowitzBackend(B)

@testset "Markowitz reads matching CSC without copying its storage" begin
    for T in (Float32,Float64)
        B = fill(one(T),64,64) + Matrix{T}(I,64,64) .* T(64)
        C = sparse(B)
        markowitz_csc_measure(B)
        markowitz_csc_measure(C)
        dense = minimum(markowitz_csc_measure(B).bytes for _ in 1:3)
        csc = minimum(markowitz_csc_measure(C).bytes for _ in 1:3)
        @test csc <= dense + 256
    end
end

@testset "Borrowed Markowitz input remains caller-owned" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt}),
        make_matrix in (identity,sparse)
        B = Matrix{T}(I,12,12) .* T(2)
        B[10:12,10:12] = T[4 1 2;1 5 1;2 1 6]
        input = make_matrix(copy(B))
        f = JSimplex.PFIFactorization(input,Val(:markowitz))
        @test input == B
        saved = JSimplex.copy_basis_factorization(f)
        fill!(input isa Matrix ? input : input.nzval,zero(T))
        rhs = B * ones(T,12)
        @test JSimplex.forward_solve(f,rhs) ≈ ones(T,12)
        @test JSimplex.transpose_solve(f,rhs) ≈ ones(T,12)
        JSimplex.refactorize!(f,make_matrix(B .* T(2)))
        @test JSimplex.forward_solve(f,rhs) ≈ fill(T(1//2),12)
        @test JSimplex.forward_solve(saved,rhs) ≈ ones(T,12)
        @test_throws SingularException JSimplex.refactorize!(f,make_matrix(zeros(T,12,12)))
        @test JSimplex.forward_solve(f,rhs) ≈ fill(T(1//2),12)
    end
end
