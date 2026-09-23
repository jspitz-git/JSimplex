using LinearAlgebra,SparseArrays

function indexed_update_allocation_probe(factor,rhs,dest,transposed)
    operation = transposed ? JSimplex.transpose_solve! : JSimplex.forward_solve!
    return @allocated operation(dest,factor,rhs;kernel_mode=:sparse)
end

@testset "Warmed indexed update solves reuse owned storage" begin
    for Factor in (JSimplex.PFIFactorization,JSimplex.ForrestTomlinFactorization,
                   JSimplex.SuhlSuhlFactorization,JSimplex.BartelsGolubFactorization)
        factor = Factor(spdiagm(0=>ones(512)))
        tableau = zeros(512); tableau[1:2] .= [1.0,2.0]
        JSimplex.replace_column!(factor,tableau,1)
        rhs,dest = JSimplex.IndexedVector{Float64}(512),JSimplex.IndexedVector{Float64}(512)
        JSimplex.set_entry!(rhs,2,1.0)
        for transposed in (false,true)
            indexed_update_allocation_probe(factor,rhs,dest,transposed)
            indexed_update_allocation_probe(factor,rhs,dest,transposed)
            @test indexed_update_allocation_probe(factor,rhs,dest,transposed) == 0
        end
        @test Base.summarysize(factor.sparse) < 1_000_000
    end
end
