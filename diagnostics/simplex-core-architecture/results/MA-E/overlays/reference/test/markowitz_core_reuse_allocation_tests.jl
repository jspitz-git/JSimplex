using SparseArrays, LinearAlgebra

markowitz_core_measure(f,B) = @timed (JSimplex.refactorize!(f,B); nothing)

@testset "Markowitz reuses dense core LU and solve buffers" begin
    for T in (Float32,Float64),
        Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        band=spdiagm(-1=>fill(-one(T),63),0=>fill(T(4),64),1=>fill(-one(T),63))
        dense=fill(T(1//8),64,64)+Matrix{T}(I,64,64)*T(4)
        for B in (band,dense,sparse(dense),zeros(T,0,0))
            f=Factor(B,Val(:markowitz))
            for _ in 1:5
                markowitz_core_measure(f,B)
            end
            samples=[markowitz_core_measure(f,B) for _ in 1:3]
            @test minimum(t.bytes for t in samples)==0
            @test minimum(Base.gc_alloc_count(t.gcstats) for t in samples)==0
            rhs=B*ones(T,size(B,1))
            @test JSimplex.forward_solve(f,rhs) ≈ ones(T,size(B,1))
            @test JSimplex.transpose_solve(f,transpose(B)*ones(T,size(B,1))) ≈ ones(T,size(B,1))
        end
    end
end

@testset "Markowitz rejects damaged dense cores without changing saved factors" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        B=fill(T(1//8),8,8)+Matrix{T}(I,8,8)*T(4)
        f=JSimplex.PFIFactorization(B,Val(:markowitz))
        for _ in 1:4
            JSimplex.refactorize!(f,B)
        end
        saved=JSimplex.copy_basis_factorization(f)
        singular=copy(B); singular[2,:]=singular[1,:]
        @test_throws SingularException JSimplex.refactorize!(f,singular)
        @test JSimplex.forward_solve(f,B*ones(T,8)) ≈ ones(T,8)
        @test JSimplex.transpose_solve(saved,transpose(B)*ones(T,8)) ≈ ones(T,8)
        for (step,k) in enumerate((8,2,0,5,8,8,8))
            replacement=Matrix{T}(I,8,8)*T(step+1)
            if k>0
                replacement[1:k,1:k].+=T(1//8)
            end
            JSimplex.refactorize!(f,sparse(replacement))
            @test JSimplex.forward_solve(f,replacement*ones(T,8)) ≈ ones(T,8)
            @test JSimplex.transpose_solve(f,transpose(replacement)*ones(T,8)) ≈ ones(T,8)
            @test JSimplex.forward_solve(saved,B*ones(T,8)) ≈ ones(T,8)
        end
    end
end

@testset "Markowitz isolates nonfinite dense LU failures" begin
    for T in (Float32,Float64),
        Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        B=fill(T(1//8),8,8)+Matrix{T}(I,8,8)*T(4)
        f=Factor(B,Val(:markowitz))
        for _ in 1:4
            JSimplex.refactorize!(f,B)
        end
        saved=JSimplex.copy_basis_factorization(f)
        invalid=copy(B); invalid[1,1]=T(NaN)
        @test_throws ArgumentError JSimplex.refactorize!(f,invalid)
        for factor in (f,saved)
            @test JSimplex.forward_solve(factor,B*ones(T,8)) ≈ ones(T,8)
            @test JSimplex.transpose_solve(factor,transpose(B)*ones(T,8)) ≈ ones(T,8)
        end
        for _ in 1:3
            JSimplex.refactorize!(f,2B)
        end
        @test JSimplex.forward_solve(f,2B*ones(T,8)) ≈ ones(T,8)
        @test JSimplex.forward_solve(saved,B*ones(T,8)) ≈ ones(T,8)
    end
end
