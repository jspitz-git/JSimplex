using SparseArrays, LinearAlgebra, Random

@testset "HH prefix eligibility follows the immutable base" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{Int},Rational{BigInt}), backend in (:native,:markowitz)
        f=JSimplex.HuangfuHallFactorization(Matrix{T}(I,4,4),Val(backend))
        @test hasproperty(f.base,:finite_upper)
        if hasproperty(f.base,:finite_upper)
            @test f.base.finite_upper == (T <: Union{Float32,Float64})
            saved=JSimplex.copy_basis_factorization(f);old=f.base
            JSimplex.refactorize!(f,Matrix{T}(I,6,6))
            @test saved.base === old && f.base !== old
            @test f.base.finite_upper == old.finite_upper
            rhs=zeros(T,6);rhs[5]=one(T)
            tagged=JSimplex._unit_transpose_rhs(f,rhs,5)
            @test (tagged !== rhs) == (T <: Union{Float32,Float64})
            @test isequal(JSimplex.transpose_solve(f,tagged),JSimplex.transpose_solve(f,rhs))
        end
    end
end

function prefix_test_factor(U)
    T=eltype(U);n=size(U,1);ids=collect(1:n)
    f=JSimplex.HuangfuHallFactorization(Matrix{T}(I,n,n))
    f.base=JSimplex.HHBase(spdiagm(0=>ones(T,n)),U,ids,copy(ids),copy(ids),ones(T,n),false,ones(Int,n+1),Int[])
    f
end
@testset "HH prefix preserves zero signs and exceptional propagation" begin
    rng=MersenneTwister(5037)
    for T in (Float32,Float64),n in (1,32),density in (0.0,0.03,1.0)
        U=triu(sprandn(rng,T,n,n,density),1)+spdiagm(0=>T[isodd(i) ? -2 : 2 for i in 1:n])
        f=prefix_test_factor(U)
        for p in 1:n
            rhs=zeros(T,n);rhs[p]=1;ref=JSimplex.transpose_solve(f,rhs)
            @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,p)),ref)
        end
    end
    for T in (Float32,Float64),value in (T(Inf),T(-Inf),T(NaN),nextfloat(zero(T)),floatmin(T)),p in 1:3
        f=prefix_test_factor(sparse(T[-2 value 0;0 1 value;0 0 -1]))
        if hasproperty(f.base,:finite_upper);@test f.base.finite_upper==isfinite(value);end
        rhs=zeros(T,3);rhs[p]=1
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,p)),JSimplex.transpose_solve(f,rhs))
    end
    # Skip column 2's prefix product, overflow at p=3, then evaluate 0*Inf.
    for T in (Float32,Float64)
        U=SparseMatrixCSC(4,4,[1,2,4,5,7],[1,1,2,3,3,4],T[2,1,-2,nextfloat(zero(T)),0,1])
        f=prefix_test_factor(U);rhs=T[0,0,1,0]
        @test U.colptr[3]>3
        ref=JSimplex.transpose_solve(f,rhs)
        @test isinf(ref[3]) && isnan(ref[4])
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,3)),ref)
    end
end

@testset "HH prefix leaves prepared updates and copied factors intact" begin
    rng=MersenneTwister(875)
    for T in (Float32,Float64),backend in (:native,:markowitz)
        n=16;B=sparse(T.(Matrix{Int}(I,n,n)*16+rand(rng,-2:2,n,n)))
        f=JSimplex.HuangfuHallFactorization(B,Val(backend));g=JSimplex.copy_basis_factorization(f)
        for step in 1:8
            p=step;a=Vector(B[:,p])+Vector(B[:,mod1(p+1,n)])/T(16)
            d=JSimplex.forward_solve(f,a);e=JSimplex.forward_solve(g,a)
            partial=copy(f.prepared_partial);direction=copy(f.prepared_direction)
            rhs=zeros(T,n);rhs[n]=1
            @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,n)),JSimplex.transpose_solve(g,rhs))
            @test f.prepared_valid && isequal(partial,f.prepared_partial) && isequal(direction,f.prepared_direction)
            @test_throws LinearAlgebra.ZeroPivotException JSimplex.replace_column!(f,zeros(T,n),p)
            JSimplex.replace_column!(f,d,p);JSimplex.replace_column!(g,e,p);B[:,p]=a
            u=f.updates[end];v=g.updates[end]
            @test isequal((u.u_indices,u.u_values,u.v_indices,u.v_values,u.pivot),(v.u_indices,v.u_values,v.v_indices,v.v_values,v.pivot))
            if step==4;JSimplex.refactorize!(f,B);JSimplex.refactorize!(g,B);end
        end
    end
end
