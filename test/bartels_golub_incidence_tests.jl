using SparseArrays, LinearAlgebra
function bg_stable_incidence(f)
    rows=[Int[] for _ in f.upper]
    for column in eachindex(f.upper),row in f.upper[column].indices
        push!(rows[row],f.column_order[column])
    end
    foreach(sort!,rows)
    return rows
end
@testset "BG incidence retains stable column identities across rotations" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        B=Matrix{T}(I,7,7);f=JSimplex.BartelsGolubFactorization(B)
        for k in 1:12
            row=mod1(k,7)
            replacement=B[:,row]+B[:,mod1(row+2,7)]/T(8)
            JSimplex.replace_column!(f,JSimplex.forward_solve(f,replacement),row)
            B[:,row]=replacement
            @test f.row_columns==bg_stable_incidence(f)
            @test all(issorted,f.row_columns)
            @test B*JSimplex.forward_solve(f,ones(T,7))≈ones(T,7)
        end
        saved=JSimplex.copy_basis_factorization(f)
        old_rows=deepcopy(f.row_columns)
        replacement=B[:,1]+B[:,4]/T(8)
        JSimplex.replace_column!(saved,JSimplex.forward_solve(saved,replacement),1)
        @test saved.row_columns==bg_stable_incidence(saved)
        @test f.row_columns==old_rows
        @test_throws SingularException JSimplex.refactorize!(f,zeros(T,7,7))
        @test f.row_columns==old_rows
        JSimplex.refactorize!(f,Matrix{T}(I,4,4))
        JSimplex.replace_column!(f,T[2,1,0,1],1)
        @test f.row_columns==bg_stable_incidence(f)
    end
end
