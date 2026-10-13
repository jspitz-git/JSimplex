using SparseArrays, LinearAlgebra, Random
isdefined(@__MODULE__, :bg_replay_forward) || include("helpers/triangular_replay.jl")

@testset "FT and SS compose dense permutations without changing arithmetic" begin
    rng=MersenneTwister(7271)
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization),
        T in (Float32,Float64,BigFloat,Rational{BigInt})
        B=Matrix{T}(I,11,11)
        f=Factor(B)
        @test hasproperty(f,:row_cache)
        for k in 1:40
            row=mod1(k,11)
            replacement=B[:,row]+B[:,mod1(row+3,11)]*T(1//8)
            JSimplex.replace_column!(f,JSimplex.forward_solve(f,replacement),row)
            B[:,row]=replacement
            rhs=T.(rand(rng,-9:9,11))
            @test isequal(JSimplex.forward_solve(f,rhs),bg_replay_forward(f,rhs))
            @test isequal(JSimplex.transpose_solve(f,rhs),bg_replay_transpose(f,rhs))
            @test B*JSimplex.forward_solve(f,rhs)≈rhs
            @test transpose(B)*JSimplex.transpose_solve(f,rhs)≈rhs
            copyto!(f.work,rhs)
            @test isequal(JSimplex.transpose_solve!(f.spike,f,f.work),bg_replay_transpose(f,rhs))
        end
        saved=JSimplex.copy_basis_factorization(f)
        JSimplex.refactorize!(f,Matrix{T}(I,11,11))
        @test B*JSimplex.forward_solve(saved,ones(T,11))≈ones(T,11)
        @test JSimplex.forward_solve(f,ones(T,11))==ones(T,11)
    end
end
