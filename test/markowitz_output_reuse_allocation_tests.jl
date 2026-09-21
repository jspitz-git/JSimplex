using SparseArrays, LinearAlgebra

markowitz_output_measure(f,B) = @timed (JSimplex.refactorize!(f,B); nothing)

@testset "Markowitz reuses retired sparse factor vectors" begin
    B=spdiagm(-1=>fill(-1.0,63),0=>fill(4.0,64),1=>fill(-1.0,63))
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        f=Factor(B,Val(:markowitz))
        for _ in 1:5
            markowitz_output_measure(f,B)
        end
        samples=[markowitz_output_measure(f,B) for _ in 1:3]
        @test minimum(Base.gc_alloc_count(t.gcstats) for t in samples) < 32
        @test B*JSimplex.forward_solve(f,ones(64)) ≈ ones(64)
        @test transpose(B)*JSimplex.transpose_solve(f,ones(64)) ≈ ones(64)
    end
end

function check_markowitz_retained(f,B)
    rhs=B*ones(eltype(B),size(B,1))
    rhs_t=transpose(B)*ones(eltype(B),size(B,1))
    @test JSimplex.forward_solve(f,rhs) ≈ ones(eltype(B),size(B,1))
    @test JSimplex.transpose_solve(f,rhs_t) ≈ ones(eltype(B),size(B,1))
end

@testset "Recycled Markowitz outputs preserve branching copies and failures" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),
        Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        B=Matrix{T}(I,12,12)*T(4)
        B[10:12,10:12]=T[4 1 2;1 5 1;2 1 6]
        f=Factor(sparse(B),Val(:markowitz))
        for _ in 1:4
            JSimplex.refactorize!(f,sparse(B))
        end
        saved=JSimplex.copy_basis_factorization(f)
        grandchild=JSimplex.copy_basis_factorization(saved)
        column=zeros(T,12); column[1]=one(T);column[2]=T(1//4)
        current=copy(B); current[:,1]=B*column
        JSimplex.replace_column!(f,column,1)
        updated=JSimplex.copy_basis_factorization(f)
        @test_throws SingularException JSimplex.refactorize!(f,spzeros(T,12,12))
        check_markowitz_retained(f,current)
        @test_throws DimensionMismatch JSimplex.refactorize!(f,spzeros(T,12,13))
        for (step,n) in enumerate((12,3,0,0,12,6,12,12))
            replacement=Matrix{T}(I,n,n)*T(step+1)
            if n>=3 && isodd(step)
                replacement[1:3,1:3]=T[5 1 0;1 6 1;0 1 7]
            end
            JSimplex.refactorize!(f,sparse(replacement))
            check_markowitz_retained(f,replacement)
            check_markowitz_retained(saved,B)
            check_markowitz_retained(grandchild,B)
            check_markowitz_retained(updated,current)
        end
        JSimplex.refactorize!(saved,sparse(B*T(2)))
        JSimplex.refactorize!(grandchild,sparse(B*T(3)))
        check_markowitz_retained(saved,B*T(2))
        check_markowitz_retained(grandchild,B*T(3))
        check_markowitz_retained(updated,current)
    end
end
