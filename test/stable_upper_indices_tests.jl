using Random, LinearAlgebra
@testset "Stable upper row identities preserve logical order" begin
    @test isdefined(JSimplex, :_stable_rotate_upper_rows!)
    if isdefined(JSimplex, :_stable_rotate_upper_rows!)
        rng=MersenneTwister(9021)
        for T in (Float32,Float64,BigFloat,Rational{BigInt}), n in (1,4,13), density in (0.0,0.2,1.0)
            M=T.(rand(rng,-5:5,n,n)); M[rand(rng,n,n).>density].=0
            upper=JSimplex._identity_upper(T,n,Val(:stable))
            for j in 1:n; JSimplex._packed_column!(upper[j],M[:,j]); end
            for step in 1:30
                first=rand(rng,1:n); last=rand(rng,first:n)
                raw=[copy(c.indices.ids) for c in upper]
                absent=[iszero(M[first,j]) for j in 1:n]
                @test JSimplex._stable_rotate_upper_rows!(upper,first,last)
                permutation=vcat(collect(1:first-1),collect(first+1:last),first,collect(last+1:n))
                M=M[permutation,:]
                actual=zeros(T,n,n)
                for j in 1:n
                    @test issorted(upper[j].indices)
                    actual[upper[j].indices,j]=upper[j].values
                    absent[j] && (@test upper[j].indices.ids==raw[j])
                end
                @test isequal(actual,M)
            end
        end
    end
end

@testset "Stable index ownership survives copying and resized resets" begin
    f=JSimplex.BartelsGolubFactorization(Matrix{Float64}(I,7,7))
    for pivot in (2,5,1,4)
        direction=fill(0.125,7); direction[pivot]=1.0
        JSimplex.replace_column!(f,direction,pivot)
    end
    map=f.upper[1].indices.order
    @test all(c.indices.order===map for c in f.upper)
    g=JSimplex.copy_basis_factorization(f)
    saved=[copy(c.indices) for c in g.upper]
    @test g.upper[1].indices.order !== map
    @test all(isequal(a.indices,b.indices) for (a,b) in zip(f.upper,g.upper))
    rows=f.upper[1].indices
    @test setindex!(rows,rows[1],1) === rows
    JSimplex._reset_identity_upper!(f.upper,0)
    JSimplex._reset_identity_upper!(f.upper,12)
    @test all(c.indices.order===f.upper[1].indices.order for c in f.upper)
    @test [copy(c.indices) for c in f.upper]==[[i] for i in 1:12]
    @test [copy(c.indices) for c in g.upper]==saved
    JSimplex._reset_identity_upper!(f.upper,3)
    @test [copy(c.indices) for c in f.upper]==[[1],[2],[3]]
end
