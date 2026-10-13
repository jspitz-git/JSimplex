using LinearAlgebra,SparseArrays,Random

@testset "Indexed update sequences match an explicit exact basis" begin
    RT = Rational{BigInt}
    for T in (Float32,Float64,BigFloat,Rational{Int},RT)
        for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
            for kind in (:native,:markowitz)
                rng = MersenneTwister(1818)
                B = Matrix{RT}(I,5,5)
                factor = Factor(sparse(T.(B)),Val(kind))
                rhs,dest = JSimplex.IndexedVector{T}(5),JSimplex.IndexedVector{T}(5)
                for _ in 1:4
                    pivot = rand(rng,1:5)
                    tableau = RT.(rand(rng,-1:1,5))./2
                    tableau[pivot] = 2
                    replacement = B*tableau
                    JSimplex.replace_column!(factor,T.(tableau),pivot)
                    B[:,pivot] = replacement
                    for values in (RT[1,0,0,0,0],RT[0,0,1,0,0],RT[1,-2,3,-1,2])
                        JSimplex.load_indexed!(rhs,T.(values))
                        for transposed in (false,true)
                            matrix = transposed ? transpose(B) : B
                            reference = matrix \ values
                            operation = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                            operation(dest,factor,rhs;kernel_mode=:sparse)
                            if T <: Rational
                                @test RT.(dest.values) == reference
                            else
                                allowance = 512BigFloat(eps(T))*max(BigFloat(1),norm(BigFloat.(reference),Inf))
                                @test norm(BigFloat.(dest.values)-BigFloat.(reference),Inf) <= allowance
                            end
                            @test Set(dest.indices) == Set(findall(!iszero,dest.values))
                            @test rhs.values == T.(values)
                        end
                    end
                end
            end
        end
    end
end

@testset "Updated upper snapshots reset without rebuilding the base view" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization)
        factor = Factor(Matrix{Float64}(I,5,5))
        rhs,dest = JSimplex.IndexedVector{Float64}(5),JSimplex.IndexedVector{Float64}(5)
        JSimplex.set_entry!(rhs,1,1.0)
        JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
        first = factor.sparse.upper
        @test factor.sparse.upper_rebuilds == 1
        JSimplex.replace_column!(factor,[2.0,1,0,1,0],1)
        @test isnothing(factor.sparse.upper)
        JSimplex.forward_solve!(dest,factor,rhs;kernel_mode=:sparse)
        @test factor.sparse.upper !== first
        @test factor.sparse.upper_rebuilds == 2
        @test factor.sparse.base_builds == 1
        checkpoint = JSimplex.copy_basis_factorization(factor)
        @test checkpoint.sparse.upper.matrix === factor.sparse.upper.matrix
        @test checkpoint.sparse.upper.reach !== factor.sparse.upper.reach
        JSimplex.transpose_solve!(rhs,checkpoint,rhs;kernel_mode=:sparse)
        B = Matrix{Float64}(I,5,5); B[:,1] = [2.0,1,0,1,0]
        @test transpose(B)*rhs.values == [1.0,0,0,0,0]
    end
end

@testset "BigFloat indexed updates preserve stored working precision" begin
    setprecision(BigFloat,256) do
        for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization),
            kind in (:native,:markowitz)
            B = Matrix{BigFloat}(I,4,4)
            factor = Factor(sparse(B),Val(kind))
            replacement = BigFloat[1+BigFloat(2)^(-80),2,0,0]
            JSimplex.replace_column!(factor,replacement,1)
            B[:,1] = replacement
            rhs,dest = JSimplex.IndexedVector{BigFloat}(4),JSimplex.IndexedVector{BigFloat}(4)
            JSimplex.set_entry!(rhs,1,BigFloat(1)+BigFloat(2)^(-90))
            for transposed in (false,true), mode in (:sparse,:auto,:dense)
                setprecision(BigFloat,24) do
                    operation = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                    operation(dest,factor,rhs;kernel_mode=mode)
                end
                matrix = transposed ? transpose(B) : B
                @test norm(matrix*dest.values-rhs.values,Inf) < BigFloat(2)^(-240)
                @test all(i->precision(dest.values[i])>=256,dest.indices)
            end
        end
    end
end
