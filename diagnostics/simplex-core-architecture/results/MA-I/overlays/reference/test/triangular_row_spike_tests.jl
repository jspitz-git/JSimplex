using LinearAlgebra, SparseArrays

@testset "Row-spike elimination preserves the factor equation" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),
        (Factor,last) in ((JSimplex.ForrestTomlinFactorization,24),
                         (JSimplex.SuhlSuhlFactorization,20)),
        first in (3,last-3)
        n=24
        factor=Factor(Matrix{T}(I,n,n))
        original=Matrix{T}(I,n,n)
        for column in 4:n
            original[column-3,column]=T(1//4)
        end
        original[last,first:last-1] .= T(1//8)
        for column in 1:n
            JSimplex._packed_column!(factor.upper[column],original[:,column])
        end
        stored=sum(c->length(c.values),factor.upper)
        factor.spike .= original[last,:]
        for column in first:last-1
            JSimplex._set_upper_value!(factor.upper[column],last,zero(T))
        end
        indices,multipliers=JSimplex._eliminate_triangular_row_spike!(factor,first,last,stored)
        actual=zeros(T,n,n)
        for column in 1:n, (row,value) in zip(factor.upper[column].indices,factor.upper[column].values)
            actual[row,column]=value
        end
        transform=Matrix{T}(I,n,n)
        for (row,multiplier) in zip(indices,multipliers)
            transform[last,row]=multiplier
        end
        @test transform * original ≈ actual
        @test all(iszero,actual[last,first:last-1])
        @test actual[setdiff(1:n,[last]),:] == original[setdiff(1:n,[last]),:]
        @test issorted(indices) && all(i->first<=i<last,indices)
        @test all(c->issorted(c.indices),factor.upper)
    end
end

@testset "Forrest-Tomlin skips an empty or delayed row spike" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), delayed in (false,true)
        B=Matrix{T}(I,24,24)
        factor=JSimplex.ForrestTomlinFactorization(copy(B))
        if delayed
            B[1,18]=T(1//4)
            B[1,24]=T(1//8)
            JSimplex._set_upper_value!(factor.upper[18],1,T(1//4))
            JSimplex._set_upper_value!(factor.upper[24],1,T(1//8))
        end
        # Direct tableau input exercises scratch whose old contents are not a
        # valid moved row. The early all-zero multiplier prefix must be ignored.
        fill!(factor.spike,T(37))
        tableau=zeros(T,24); tableau[1]=T(2)
        replacement=B*tableau
        JSimplex.replace_column!(factor,tableau,1)
        B[:,1]=replacement
        indices=factor.updates[end].indices
        @test delayed ? (!isempty(indices) && first(indices)==17) : isempty(indices)
        rhs=T.(1:24)
        @test B * JSimplex.forward_solve(factor,rhs) ≈ rhs
        @test B' * JSimplex.transpose_solve(factor,rhs) ≈ rhs
        @test all(c->issorted(c.indices),factor.upper)
    end
end

@testset "Terminal row rotations preserve untouched entries" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),
        (Factor,pivot) in ((JSimplex.ForrestTomlinFactorization,6),
                          (JSimplex.SuhlSuhlFactorization,4))
        B=Matrix{T}(I,6,6)
        factor=Factor(B)
        if pivot < 6
            # An explicit signed zero in a column outside the SS rotation.
            pushfirst!(factor.upper[6].indices,pivot)
            pushfirst!(factor.upper[6].values,-zero(T))
        end
        replacement=copy(B[:,pivot]); replacement[pivot]=T(2)
        JSimplex.replace_column!(factor,replacement,pivot)
        B[:,pivot]=replacement
        @test isempty(factor.updates[end].indices)
        rhs=T.(1:6)
        @test B * JSimplex.forward_solve(factor,rhs) ≈ rhs
        @test B' * JSimplex.transpose_solve(factor,rhs) ≈ rhs
        if pivot < 6
            @test isequal(JSimplex._upper_value(factor.upper[6],pivot),-zero(T))
            @test pivot in factor.upper[6].indices
        end
    end
end

@testset "Skipped zero spikes do not conceal invalid diagonals" begin
    for diagonal in (0.0,NaN)
        factor=JSimplex.ForrestTomlinFactorization(Matrix{Float64}(I,4,4))
        # Old column 2 becomes column 1 after deleting the leaving column.
        JSimplex._set_upper_value!(factor.upper[2],2,diagonal)
        JSimplex.replace_column!(factor,[2.0,0,0,0],1)
        @test first(factor.updates[end].indices)==1
        @test isnan(first(factor.updates[end].multipliers))
    end
end
