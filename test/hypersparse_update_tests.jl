using LinearAlgebra,SparseArrays

@testset "Indexed basis updates create and cancel support" begin
    for T in (Float32,Float64,BigFloat,Rational{Int},Rational{BigInt})
        for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                       JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
            B = Matrix{T}(I,4,4)
            factor = Factor(sparse(B),Val(:markowitz))
            rhs,dest = JSimplex.IndexedVector{T}(4),JSimplex.IndexedVector{T}(4)
            for replacement in (T[1,2,0,0],T[1,0,0,0])
                tableau = JSimplex.forward_solve(factor,replacement)
                JSimplex.replace_column!(factor,tableau,1)
                B[:,1] = replacement
                for values in (T[1,0,0,0],T[0,1,0,0],T[0,0,1,0],T[1,1,1,1])
                    for transposed in (false,true), mode in (:sparse,:dense,:auto)
                        JSimplex.load_indexed!(rhs,values)
                        operation = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
                        operation(dest,factor,rhs;kernel_mode=mode)
                        matrix = transposed ? transpose(B) : B
                        @test matrix*dest.values == values
                        @test Set(dest.indices) == Set(findall(!iszero,dest.values))
                        @test rhs.values == values
                    end
                end
            end
        end
    end
end

@testset "PFI transpose uses eta support when the old pivot is absent" begin
    factor = JSimplex.PFIFactorization(Matrix{Float64}(I,4,4))
    JSimplex.replace_column!(factor,[1.0,2,0,0],1)
    rhs,dest = JSimplex.IndexedVector{Float64}(4),JSimplex.IndexedVector{Float64}(4)
    JSimplex.set_entry!(rhs,2,1.0)
    JSimplex.transpose_solve!(dest,factor,rhs;kernel_mode=:sparse)
    @test dest.values == [-2.0,1,0,0]
    @test Set(dest.indices) == Set([1,2])
end
