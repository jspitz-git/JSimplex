using LinearAlgebra, SparseArrays, Random

@testset "Triangular unit prefix ownership and arithmetic" begin
    rng=MersenneTwister(7359)
    for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),
        T in (Float32,Float64), backend in (:native,:markowitz)
        n=9;B=Matrix{T}(I,n,n);f=F(B,Val(backend))
        available=hasproperty(f.row_cache,:upper_prefix_safe)
        @test available
        available || continue
        @test f.row_cache.upper_prefix_safe
        for step in 1:24
            row=mod1(4*step,n)
            a=B[:,row]+B[:,mod1(row+2,n)]*T(1//8)
            isodd(step) && (a .*= -one(T))
            d=JSimplex.forward_solve(f,a)
            JSimplex.replace_column!(f,d,row);B[:,row]=a
            @test f.row_cache.upper_prefix_safe
            saved=JSimplex.copy_basis_factorization(f)
            @test saved.row_cache.upper_prefix_safe
            @test saved.row_cache !== f.row_cache
            for g in (f,saved),p in (1,cld(n,2),n)
                rhs=zeros(T,n);rhs[p]=one(T)
                tagged=JSimplex._unit_transpose_rhs(g,rhs,p)
                reference=JSimplex.transpose_solve(g,rhs)
                @test isequal(JSimplex.transpose_solve(g,tagged),reference)
                @test all(isfinite,reference)
                @test transpose(B)*reference ≈ rhs
                inplace=copy(rhs)
                @test isequal(JSimplex.transpose_solve!(inplace,g,JSimplex._unit_transpose_rhs(g,inplace,p)),reference)
            end
            @test f.row_cache.upper_prefix_safe
            @test all(c->all(isfinite,c.values),f.upper)
            @test all(j->!iszero(JSimplex._upper_diagonal(f.upper[j],j)),1:n)
        end
        # Preparation rejection cannot invalidate an unchanged upper factor.
        @test_throws LinearAlgebra.ZeroPivotException JSimplex.replace_column!(f,zeros(T,n),1)
        @test f.row_cache.upper_prefix_safe
        @test_throws Exception JSimplex.refactorize!(f,zeros(T,n,n))
        @test f.row_cache.upper_prefix_safe
        JSimplex._invalidate_sparse_upper!(f,7)
        @test !f.row_cache.upper_prefix_safe
        saved=JSimplex.copy_basis_factorization(f)
        @test !saved.row_cache.upper_prefix_safe
        # A later valid update does not promote an externally invalidated factor.
        d=JSimplex.forward_solve(f,B[:,2]);JSimplex.replace_column!(f,d,2)
        @test !f.row_cache.upper_prefix_safe
        JSimplex.refactorize!(f,Matrix{T}(I,4,4))
        @test f.row_cache.upper_prefix_safe
        @test !saved.row_cache.upper_prefix_safe
        # Several mutations can precede the next active-column rebuild.
        for row in (3,1,4)
            JSimplex.replace_column!(f,T[i==row ? 2 : 0 for i in 1:4],row)
            @test f.row_cache.upper_prefix_safe
        end
        rhs=T[0,0,0,1]
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,4)),JSimplex.transpose_solve(f,rhs))
        # Actual packing of a nonfinite off-pivot coefficient must disable skipping.
        g=F(Matrix{T}(I,4,4),Val(backend))
        try
            JSimplex.replace_column!(g,T[1,Inf,0,0],1)
        catch e
            @test e isa LinearAlgebra.ZeroPivotException
        end
        @test !g.row_cache.upper_prefix_safe
    end
end

@testset "Triangular prefix scalar fallback and SS early return" begin
    for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),
        T in (Float16,BigFloat,Rational{Int},Rational{BigInt})
        f=F(Matrix{T}(I,3,3))
        available=hasproperty(f.row_cache,:upper_prefix_safe);@test available
        available || continue
        @test !f.row_cache.upper_prefix_safe
        JSimplex.replace_column!(f,T[1,1,0],1)
        rhs=T[0,0,1]
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,3)),JSimplex.transpose_solve(f,rhs))
    end
    for T in (Float32,Float64)
        f=JSimplex.SuhlSuhlFactorization(Matrix{T}(I,4,4))
        available=hasproperty(f.row_cache,:upper_prefix_safe);@test available
        available || continue
        JSimplex.replace_column!(f,T[0,0,-2,0],3)
        @test f.updates[end].pivot==f.updates[end].last==3
        @test f.row_cache.upper_prefix_safe
        rhs=T[0,0,0,1]
        @test isequal(JSimplex.transpose_solve(f,JSimplex._unit_transpose_rhs(f,rhs,4)),JSimplex.transpose_solve(f,rhs))
    end
end

function triangular_prefix_bytes!(out, f, rhs)
    return @allocated JSimplex.transpose_solve!(out, f, rhs)
end
@testset "Triangular prefix exceptional arithmetic and allocations" begin
    for F in (JSimplex.ForrestTomlinFactorization, JSimplex.SuhlSuhlFactorization,
              JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        # Negative prefix diagonals and subnormal coefficients preserve signed
        # zero behavior; suffix divisions may still overflow or produce NaNs.
        f=F(Matrix{T}(I,5,5))
        for row in 1:4
            d=zeros(T,5);d[row]=-T(2);d[5]=nextfloat(zero(T))
            JSimplex.replace_column!(f,d,row)
        end
        for row in 1:5
            rhs=zeros(T,5);rhs[row]=one(T);out=similar(rhs)
            tag=JSimplex._unit_transpose_rhs(f,rhs,row)
            ref=JSimplex.transpose_solve(f,rhs)
            @test isequal(JSimplex.transpose_solve!(out,f,tag),ref)
            triangular_prefix_bytes!(out,f,tag);triangular_prefix_bytes!(out,f,tag)
            @test triangular_prefix_bytes!(out,f,tag)==0
        end
        for bad in (T(Inf),T(NaN))
            g=F(Matrix{T}(I,4,4))
            JSimplex.replace_column!(g,T[1,bad,0,0],1)
            @test !g.row_cache.upper_prefix_safe
            rhs=T[0,0,0,1]
            @test isequal(JSimplex.transpose_solve(g,JSimplex._unit_transpose_rhs(g,rhs,4)),
                          JSimplex.transpose_solve(g,rhs))
        end
        for mode in (:missing,:zero)
            g=F(Matrix{T}(I,3,3))
            if mode===:missing
                empty!(g.upper[1].indices);empty!(g.upper[1].values)
            else
                g.upper[1].values[1]=zero(T)
            end
            # New factor already has a pending metadata rebuild. The cache
            # must reject an invalid diagonal before selecting the prefix path.
            @test g.row_cache.upper_dirty
            rhs=T[0,0,1]
            got=JSimplex.transpose_solve(g,JSimplex._unit_transpose_rhs(g,rhs,3))
            @test !g.row_cache.upper_prefix_safe
            @test isequal(got,JSimplex.transpose_solve(g,rhs))
        end
    end
end

@testset "Triangular prefix underflow and exceptional suffix" begin
    for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
              JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        f=F(Matrix{T}(I,2,2))
        JSimplex.replace_column!(f,T[nextfloat(zero(T)),0],1;zero_tolerance=0)
        if F===JSimplex.SuhlSuhlFactorization
            @test_throws BoundsError JSimplex.replace_column!(f,T[0.5,0],1;zero_tolerance=0)
            @test !f.row_cache.upper_prefix_safe
        else
            JSimplex.replace_column!(f,T[0.5,0],1;zero_tolerance=0)
            JSimplex._dense_upper_columns(f)
            @test !f.row_cache.upper_prefix_safe
        end
        # All stored inputs are finite. Overflow occurs at the unit position,
        # after an eligible nonempty prefix, followed by a stored 0 * Inf.
        g=F(Matrix{T}(I,4,4))
        g.upper[1].values[1]=-T(2)
        g.upper[2].values[1]=-T(2)
        insert!(g.upper[2].indices,1,1);insert!(g.upper[2].values,1,one(T))
        g.upper[3].values[1]=nextfloat(zero(T))
        insert!(g.upper[4].indices,1,3);insert!(g.upper[4].values,1,zero(T))
        rhs=T[0,0,1,0]
        expected=JSimplex.transpose_solve(g,rhs)
        @test g.row_cache.upper_prefix_safe
        @test any(isnan,expected)
        @test isequal(JSimplex.transpose_solve(g,JSimplex._unit_transpose_rhs(g,rhs,3)),expected)
        # Finite input can overflow during spike construction/elimination.
        h=F(Matrix{T}(I,2,2))
        JSimplex.replace_column!(h,T[1,floatmax(T)],1)
        try
            JSimplex.replace_column!(h,T[1,floatmax(T)],1)
        catch e
            @test e isa LinearAlgebra.ZeroPivotException
        end
        @test !h.row_cache.upper_prefix_safe
    end
end

@testset "Finite elimination overflow invalidates triangular prefix" begin
    for F in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
              JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        f=F(Matrix{T}(I,3,3))
        # A finite canonical upper factor; elimination, not packing, overflows.
        JSimplex._set_upper_value!(f.upper[2],1,one(T))
        JSimplex._set_upper_value!(f.upper[3],1,floatmax(T))
        JSimplex._set_upper_value!(f.upper[3],2,-floatmax(T))
        @test all(c->all(isfinite,c.values),f.upper)
        JSimplex.replace_column!(f,T[1,1,nextfloat(zero(T))],1)
        @test any(c->any(!isfinite,c.values),f.upper)
        @test !f.row_cache.upper_prefix_safe
    end
end
