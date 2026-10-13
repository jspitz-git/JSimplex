using Test, JSimplex, SparseArrays, LinearAlgebra
import MathOptInterface as MOI

@testset "Huangfu-Hall Markowitz backend" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{BigInt},Rational{Int})
        @testset "$T" begin
            accepted = try
                SolverOptions(T;basis_update=:huangfu_hall,basis_refactorization=:markowitz)
            catch err
                err
            end
            @test accepted isa SolverOptions{T,:huangfu_hall,:markowitz}
            accepted isa SolverOptions || continue
            tol = T <: Rational ? zero(T) : 100eps(T)
            close(a,b) = T <: Rational ? a == b : isapprox(a,b;rtol=tol,atol=tol)
            L=Matrix{T}(I,8,8)
            L[6,1]=T(1)/4;L[7,2]=T(1)/2;L[8,3]=T(1)/4
            U=Matrix{T}(I,8,8);U[6:8,6:8]=T[0 2 1;3 1 0;1 0 4]
            mixed=sparse((L*U)[[4,8,1,6,2,7,3,5],[5,2,8,1,6,4,7,3]])
            for B0 in (spdiagm(0=>T[2,3,4]), sparse(T[0 2 1;3 1 0;1 0 4]), mixed)
                B=Matrix(B0);n=size(B,1);rhs=T.(1:n)
                f=@inferred JSimplex._basis_factorization(B0,accepted)
                @test f.refactor_workspace isa JSimplex.MarkowitzBackend{T}
                @test close(Matrix(f.base.lower*f.base.upper),B[f.base.rows,f.base.columns])
                @test all(isone,f.base.scaling) && !f.base.divide_scaling
                if n==8
                    @test 0<f.refactor_workspace.sparse_pivots<n
                    @test f.refactor_workspace.core.p != collect(1:length(f.refactor_workspace.core.p))
                end
                for step in 1:6
                    p=mod1(step,n);d=zeros(T,n);d[p]=one(T);d[mod1(p+1,n)]=T(1)/4
                    column=B*d
                    direction=JSimplex.forward_solve(f,column)
                    iseven(step) && JSimplex.forward_solve(f,rhs)
                    JSimplex.replace_column!(f,direction,p);B[:,p]=column
                    for (op,M) in ((JSimplex.forward_solve!,B),(JSimplex.transpose_solve!,transpose(B)))
                        x=copy(rhs);op(x,f,x)
                        @test close(M*x,rhs)
                    end
                    if step%2==0
                        saved=JSimplex.copy_basis_factorization(f)
                        JSimplex.refactorize!(f,sparse(2B))
                        @test close(B*JSimplex.forward_solve(saved,rhs),rhs)
                        @test close(2B*JSimplex.forward_solve(f,rhs),rhs)
                        @test_throws SingularException JSimplex.refactorize!(f,zeros(T,n,n))
                        @test close(2B*JSimplex.forward_solve(f,rhs),rhs)
                        JSimplex.refactorize!(saved,sparse(B))
                        @test saved.refactor_workspace isa JSimplex.MarkowitzBackend{T}
                        JSimplex.refactorize!(f,B)
                        @test f.refactor_workspace isa JSimplex.MarkowitzBackend{T}
                    end
                end
                for dim in (0,5,0,n)
                    JSimplex.refactorize!(f,Matrix{T}(I,dim,dim))
                    @test JSimplex.forward_solve(f,ones(T,dim)) == ones(T,dim)
                    @test JSimplex.transpose_solve(f,ones(T,dim)) == ones(T,dim)
                    @test f.refactor_workspace isa JSimplex.MarkowitzBackend{T}
                end
            end
        end
    end
end

@testset "Markowitz HH fill and precision" begin
    for T in (Float64,BigFloat,Rational{BigInt})
        n=12
        B=spdiagm(-1=>fill(T(-1),n-1),0=>fill(T(4),n),1=>fill(T(2),n-1))
        B=B[vcat(2:n,1),n:-1:1]
        f=JSimplex.HuangfuHallFactorization(B,Val(:markowitz))
        @test any(!isempty(v.indices) for v in f.refactor_workspace.lower)
        @test any(!isempty(v.indices) for v in f.refactor_workspace.upper)
        @test f.base.lower*f.base.upper ≈ B[f.base.rows,f.base.columns]
        rhs=T.(1:n)
        for (op,M) in ((JSimplex.forward_solve,B),(JSimplex.transpose_solve,transpose(B)))
            actual=M*op(f,rhs)
            @test T <: Rational ? actual==rhs : actual≈rhs
        end
    end
    for bits in (96,256,512)
        setprecision(BigFloat,bits) do
            delta=BigFloat(2)^(-bits+8)
            B=BigFloat[0 1+delta;1-delta 1]
            f=JSimplex.HuangfuHallFactorization(B,Val(:markowitz))
            @test f.base.lower*f.base.upper == B[f.base.rows,f.base.columns]
            @test precision(f.base.upper[1,1]) == bits
            new=BigFloat[1+2delta,delta]
            d=JSimplex.forward_solve(f,new)
            JSimplex.replace_column!(f,d,1);B[:,1]=new
            @test norm(B*JSimplex.forward_solve(f,ones(BigFloat,2))-ones(BigFloat,2),Inf)<=8eps(BigFloat)
        end
    end
end
