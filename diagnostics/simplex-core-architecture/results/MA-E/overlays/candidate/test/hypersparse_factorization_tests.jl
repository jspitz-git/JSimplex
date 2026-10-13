using LinearAlgebra, SparseArrays

@testset "Triangular reachability follows nonzero dependencies" begin
    L = sparse([1.0 0 0 0; 2 1 0 0; 0 0 1 0; 0 0 3 1])
    @test Set(JSimplex.reachability_order(L, [1]; transposed=false)) == Set([1, 2])
    @test Set(JSimplex.reachability_order(L, [2]; transposed=true)) == Set([1, 2])
    @test isempty(JSimplex.reachability_order(L, Int[]))
end

@testset "Public UMFPACK reconstruction includes scaling and permutations" begin
    B = sparse([0.0 2 0; 1 0 3; 4 0 5])
    F = lu(B)
    L, U, p, q, Rs = F.L, F.U, F.p, F.q, F.Rs
    @test L * U ≈ (Rs .* B)[p,q]
    @test any(!=(1.0), Rs)
    @test p != collect(1:3) || q != collect(1:3)
end

@testset "Indexed base solves match both original systems" begin
    for T in (Float32, Float64, BigFloat, Rational{Int}, Rational{BigInt})
        B = sparse(T[0 2 0; 1 0 3; 4 0 5])
        for backend_kind in (T == Float64 ? (:markowitz, :native) : (:markowitz,))
            backend = JSimplex._factorize_basis(B, Val(backend_kind))
            view = JSimplex.sparse_solve_view(backend)
            @test view isa JSimplex.SparseSolveView
            rhs = JSimplex.IndexedVector{T}(3)
            dest = JSimplex.IndexedVector{T}(3)
            for values in (T[0,0,0], T[1,0,0], T[0,0,1], T[1,2,3])
                JSimplex.load_indexed!(rhs, values)
                for transposed in (false, true)
                    operation = transposed ? JSimplex.hypersparse_transpose_solve! :
                                             JSimplex.hypersparse_forward_solve!
                    operation(dest, view, rhs)
                    A = transposed ? transpose(B) : B
                    if T <: Rational
                        @test A * dest.values == values
                    else
                        @test norm(A * dest.values - values, Inf) <=
                            64eps(T) * max(one(T), norm(A, Inf)*norm(dest.values, Inf), norm(values, Inf))
                    end
                    @test Set(dest.indices) == Set(findall(!iszero, dest.values))
                    @test rhs.values == values
                end
            end
        end
    end
end
