using LinearAlgebra

@testset "Copy-free auxiliary solves retain the original cache lifetime" begin
    for Factor in (JSimplex.ForrestTomlinFactorization,JSimplex.SuhlSuhlFactorization,
                   JSimplex.BartelsGolubFactorization), T in (Float32,Float64)
        B=Matrix{T}(I,4,4);f=Factor(B);reference=Factor(B)
        for (pivot,column) in ((1,T[1.1,0.2,0.3,0.0]),(3,T[0.1,0.0,1.3,0.2]))
            direction=B\column
            JSimplex.replace_column!(f,direction,pivot)
            JSimplex.replace_column!(reference,direction,pivot)
            B[:,pivot]=column
        end
        entering=T[0.1,0.3,0.2,1.0]
        direction=JSimplex.forward_solve(f,entering)
        expected=JSimplex.forward_solve(reference,entering)
        other=zeros(T,4);ref_other=zeros(T,4)
        for rhs in (T[2,4,1,0],T[0,3,2,1],ones(T,4))
            JSimplex._ordinary_forward_solve!(other,f,rhs)
            JSimplex.forward_solve!(ref_other,reference,rhs)
            @test isequal(other,ref_other)
            @test f.row_cache.prepared.next==reference.row_cache.prepared.next
            @test JSimplex._copy_prepared_spike!(f,direction)==
                  JSimplex._copy_prepared_spike!(reference,expected)
            @test !JSimplex._copy_prepared_spike!(f,other)
        end
        JSimplex.replace_column!(f,direction,2)
        JSimplex.replace_column!(reference,expected,2)
        @test f.column_order==reference.column_order
        @test all(isequal(a.indices,b.indices) && isequal(a.values,b.values)
            for (a,b) in zip(f.upper,reference.upper))
        B[:,2]=entering
        @test B*JSimplex.forward_solve(f,ones(T,4))≈ones(T,4)
        @test B'*JSimplex.transpose_solve(f,ones(T,4))≈ones(T,4)
    end
end
