using SparseArrays, LinearAlgebra, Random

@testset "Packed BG row rotation equals adjacent swaps" begin
    @test isdefined(JSimplex, :_rotate_upper_rows!)
    if isdefined(JSimplex, :_rotate_upper_rows!)
        rng=MersenneTwister(8881)
        for T in (Float32,Float64,BigFloat,Rational{BigInt}), n in (1,2,9), density in (0.0,0.2,1.0)
            M=T.(rand(rng,-4:4,n,n))
            M[rand(rng,n,n).>density].=0
            for first in 1:n, last in first:n
                upper=[JSimplex._packed_column(M[:,j]) for j in 1:n]
                rows=JSimplex._rebuild_row_columns!([Int[] for _ in 1:n],upper)
                marks=zeros(T,n)
                JSimplex._rotate_upper_rows!(upper,rows,Int[],marks,first,last)
                @test all(iszero,marks)
                permutation=vcat(collect(1:first-1),collect(first+1:last),first,collect(last+1:n))
                expected=M[permutation,:]
                actual=zeros(T,n,n)
                for j in 1:n
                    @test issorted(upper[j].indices)
                    actual[upper[j].indices,j]=upper[j].values
                end
                @test actual==expected
                @test rows==[findall(!iszero,expected[i,:]) for i in 1:n]
            end
        end
    end
end

include("helpers/bartels_golub_reference.jl")
@testset "Batched BG replacement matches scalar pivot history" begin
    rng=MersenneTwister(8224)
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        n=19
        f=JSimplex.BartelsGolubFactorization(Matrix{T}(I,n,n))
        reference=JSimplex.copy_basis_factorization(f)
        for k in 1:100
            pivot=rand(rng,1:n)
            column=zeros(T,n)
            for j in 1:n
                rand(rng)<0.15 && (column[j]=T(rand(rng,(-1,1))) / T(8))
            end
            column[pivot]=T(rand(rng,(1,2)))
            JSimplex.replace_column!(f,column,pivot)
            bg_reference_replace_column!(reference,column,pivot)
            @test f.column_order==reference.column_order
            @test all(j -> f.upper[j].indices==reference.upper[j].indices &&
                isequal(f.upper[j].values,reference.upper[j].values),1:n)
            steps=[(s.row,s.last,s.swapped,s.multiplier) for s in f.updates[end].steps]
            expected=[(s.row,s.last,s.swapped,s.multiplier) for s in reference.updates[end].steps]
            @test isequal(steps,expected)
        end
    end
end
