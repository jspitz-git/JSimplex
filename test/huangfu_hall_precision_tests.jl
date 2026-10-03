using Test, JSimplex, SparseArrays, LinearAlgebra

function hh_precision_checks(::Type{T}) where {T}
    @testset "Huangfu-Hall $T" begin
        accepts = try
            SolverOptions(T; basis_update=:huangfu_hall).basis_update === :huangfu_hall
        catch
            false
        end
        @test accepts
        accepts || return
        tol = T <: Rational ? zero(T) : T(40)*eps(T)
        close(a, b) = T <: Rational ? a == b : isapprox(a, b; rtol=tol, atol=tol)
        # Nonsymmetric, row-pivoted LU; integer data keep exact references small.
        B = T[0 2 1; 3 1 0; 1 0 4]
        rhs = T[1, -2, 3]
        f = @inferred JSimplex.HuangfuHallFactorization(sparse(B))
        @test eltype(f.base.lower) === T
        @test eltype(f.base.upper) === T
        @test eltype(f.work) === T
        @test close(Matrix(f.base.lower*f.base.upper), B[f.base.rows,f.base.columns])
        for step in 1:12
            p = mod1(step,3)
            d = fill(zero(T),3); d[p] = one(T); d[mod1(p+1,3)] = T(1)/T(4)
            new = B*d
            direction = JSimplex.forward_solve(f,new)
            if iseven(step)
                # Invalidate preparation and exercise the supplied-direction path.
                JSimplex.forward_solve(f,rhs)
            end
            JSimplex.replace_column!(f,direction,p)
            B[:,p] = new
            @test eltype(last(f.updates).u_values) === T
            @test last(f.updates).pivot isa T
            for (op, M) in ((JSimplex.forward_solve!,B),(JSimplex.transpose_solve!,transpose(B)))
                x=copy(rhs); op(x,f,x)
                @test eltype(x) === T
                @test close(M*x,rhs)
            end
            if step%4 == 0
                saved=JSimplex.copy_basis_factorization(f)
                JSimplex.refactorize!(f,sparse(2B))
                @test close(2B*JSimplex.forward_solve(f,rhs),rhs)
                @test close(B*JSimplex.forward_solve(saved,rhs),rhs)
                @test_throws LinearAlgebra.SingularException JSimplex.refactorize!(f,zeros(T,3,3))
                @test close(2B*JSimplex.forward_solve(f,rhs),rhs)
                JSimplex.refactorize!(f,B)
            end
        end
        for n in (0,5,0,3)
            JSimplex.refactorize!(f,Matrix{T}(I,n,n))
            @test JSimplex.forward_solve(f,ones(T,n)) == ones(T,n)
            @test JSimplex.transpose_solve(f,ones(T,n)) == ones(T,n)
        end
        # Default exact pivot tolerance must not reject a small nonzero rational.
        if T === Rational{BigInt} || T === BigFloat
            tiny = T(1)/T(big(10)^30)
            identity = Matrix{T}(I,2,2)
            f = JSimplex.HuangfuHallFactorization(identity)
            JSimplex.replace_column!(f,T[tiny,0],1; zero_tolerance=zero(T))
            @test JSimplex.forward_solve(f,T[tiny,1]) == ones(T,2)
            if T <: Rational
                g=JSimplex.HuangfuHallFactorization(identity)
                JSimplex.replace_column!(g,T[tiny,0],1)
                @test JSimplex.forward_solve(g,T[tiny,1]) == ones(T,2)
            end
            JSimplex.refactorize!(f,identity)
            # Variable-sized scalar payload must not remain in retired pools.
            @test isempty(f.u_pool.pairs) && isempty(f.v_pool.pairs)
        end
    end
end

for T in (Float32, BigFloat, Rational{BigInt}, Rational{Int}, Float16)
    hh_precision_checks(T)
end

@testset "BigFloat preserves sub-Float64 coefficient bits" begin
    for bits in (96,256,512)
        setprecision(BigFloat,bits) do
            delta=BigFloat(2)^(-bits+8)
            B=BigFloat[1+delta 0;0 1-delta]
            f=JSimplex.HuangfuHallFactorization(B)
            @test f.base.upper[1,1] == 1+delta
            @test f.base.upper[2,2] == 1-delta
            new=BigFloat[1+2delta,delta]
            direction=JSimplex.forward_solve(f,new)
            JSimplex.replace_column!(f,direction,1)
            B[:,1]=new
            @test norm(B*JSimplex.forward_solve(f,BigFloat[1,1])-ones(BigFloat,2),Inf)<=4eps(BigFloat)
            @test precision(f.updates[1].pivot)==bits
            JSimplex.refactorize!(f,B)
            @test f.base.upper[1,1]==1+2delta
        end
    end
end

@testset "Growth diagnostics retain the working scalar" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{BigInt})
        T === Float64 && Int !== Int64 && continue
        f=JSimplex.HuangfuHallFactorization(Matrix{T}(I,2,2))
        @test JSimplex._factor_growth_reference(f) isa T
        @test JSimplex._factor_growth_measure(f) isa T
        JSimplex.replace_column!(f,T[2,1],1)
        @test JSimplex._factor_growth_measure(f) isa T
        @test JSimplex._factor_growth_measure(f)>=one(T)
    end
end
