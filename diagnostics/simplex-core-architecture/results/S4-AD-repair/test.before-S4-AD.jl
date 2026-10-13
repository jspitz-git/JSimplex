using SparseArrays, LinearAlgebra, Random

markowitz_workspace_fresh(B) = @timed JSimplex.MarkowitzBackend(B)
markowitz_workspace_reset(f,B) = @timed (JSimplex.refactorize!(f,B); nothing)

@testset "Repeated Markowitz construction reuses private workspace" begin
    B=spdiagm(-1=>fill(-1.0,63),0=>fill(4.0,64),1=>fill(-1.0,63))
    markowitz_workspace_fresh(B)
    fresh=minimum(Base.gc_alloc_count(markowitz_workspace_fresh(B).gcstats) for _ in 1:3)
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        f=Factor(B,Val(:markowitz))
        for _ in 1:3
            markowitz_workspace_reset(f,B)
        end
        samples=[markowitz_workspace_reset(f,B) for _ in 1:3]
        @test minimum(Base.gc_alloc_count(t.gcstats) for t in samples) < 2fresh÷3
        @test B*JSimplex.forward_solve(f,ones(64)) ≈ ones(64)
        @test transpose(B)*JSimplex.transpose_solve(f,ones(64)) ≈ ones(64)
    end
end

@testset "Markowitz pivot ties do not depend on retained dictionary capacity" begin
    n=32
    history=spdiagm(0=>fill(32.0,n))
    for row in 1:n, offset in 1:12
        history[row,mod1(row+offset,n)]=1.0
    end
    for seed in 1:8
        rng=MersenneTwister(seed)
        B=spdiagm(0=>ones(n))
        for row in 1:n, offset in (1,5,13)
            B[row,mod1(row+offset,n)]=rand(rng,Bool) ? 1.0 : -1.0
        end
        f=JSimplex.PFIFactorization(B,Val(:markowitz))
        rows=copy(f.base.row_order)
        columns=copy(f.base.column_order)
        saved=JSimplex.copy_basis_factorization(f)
        JSimplex.refactorize!(f,history)
        JSimplex.refactorize!(f,B)
        @test f.base.row_order==rows
        @test f.base.column_order==columns
        @test B*JSimplex.forward_solve(f,ones(n)) ≈ ones(n)
        @test transpose(B)*JSimplex.transpose_solve(f,ones(n)) ≈ ones(n)
        JSimplex.refactorize!(saved,history)
        @test saved.base.workspace !== f.base.workspace
        @test saved.base.workspace.rows[1] !== f.base.workspace.rows[1]
        @test B*JSimplex.forward_solve(f,ones(n)) ≈ ones(n)
    end
end

@testset "Markowitz workspace resets clear dimension and failure history" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        original=spdiagm(0=>fill(T(2),8))
        f=JSimplex.PFIFactorization(original,Val(:markowitz))
        saved=JSimplex.copy_basis_factorization(f)
        for n in (16,0,0,3,12,4,16)
            B=Matrix{T}(I,n,n)*T(4)
            if n>=3
                B[1:3,1:3]=T[4 1 0;1 4 1;0 1 4]
            end
            input=sparse(B)
            JSimplex.refactorize!(f,input)
            @test input==B
            @test B*JSimplex.forward_solve(f,ones(T,n)) ≈ ones(T,n)
            @test transpose(B)*JSimplex.transpose_solve(f,ones(T,n)) ≈ ones(T,n)
            child=JSimplex.copy_basis_factorization(f)
            @test_throws SingularException JSimplex.refactorize!(f,spzeros(T,n+1,n+1))
            @test B*JSimplex.forward_solve(f,ones(T,n)) ≈ ones(T,n)
            JSimplex.refactorize!(f,sparse(B*T(2)))
            @test (B*T(2))*JSimplex.forward_solve(f,ones(T,n)) ≈ ones(T,n)
            @test B*JSimplex.forward_solve(child,ones(T,n)) ≈ ones(T,n)
            @test original*JSimplex.forward_solve(saved,ones(T,8)) ≈ ones(T,8)
        end
    end
end

function replace_markowitz_backend_for_capacity!(holder,B)
    holder[] = JSimplex._refactorize_backend(holder[],B)
    nothing
end
@testset "Retained Markowitz capacity after smaller bases" begin
    for T in (Float32,Float64)
        large=spdiagm(0=>fill(T(4),64)); small=spdiagm(0=>fill(T(4),3))
        holder=Ref(JSimplex.MarkowitzBackend(large))
        for _ in 1:4; replace_markowitz_backend_for_capacity!(holder,large);end
        for _ in 1:2; replace_markowitz_backend_for_capacity!(holder,small);end
        for _ in 1:2
            @test (@allocated replace_markowitz_backend_for_capacity!(holder,large))==0
            output=zeros(T,64)
            JSimplex._backend_forward_solve!(output,holder[],fill(T(4),64))
            @test output==ones(T,64)
        end
    end
end
