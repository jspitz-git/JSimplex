@testset "Row pricing ignores padded backing arrays like the CSC reference" begin
    for T in (Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        A=SparseMatrixCSC(2,2,[1,2,3],[1,2],T[2,3])
        # Existing presolve/phase regressions also pad buffers after construction.
        append!(A.rowval,[1,999])
        append!(A.nzval,T[99,99])
        @test nnz(A)==2 && length(A.rowval)==4
        reference=zeros(T,4)
        JSimplex._csc_price!(reference,A,T[1,2])
        @test reference==T[2,6,-1,-2]
        rows=JSimplex.RowAccess(A)
        @test rows.rowptr[end]==3
        rhs,out=JSimplex.IndexedVector{T}(2),JSimplex.IndexedVector{T}(4)
        JSimplex.load_indexed!(rhs,T[1,2])
        JSimplex.sparse_price!(out,A,rhs,rows)
        @test out.values==reference
    end
end
