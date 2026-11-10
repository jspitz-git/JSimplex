using SparseArrays

@testset "Rounded lower-bound cache cannot strengthen a later upper bound" begin
    Q=Rational{BigInt}
    for T in (Float32,Float64)
        # x >= 1/3, then 3x+y <= 1. The stored lower x is below 1/3,
        # so the implied upper y must remain strictly positive, not zero.
        p=LinearProblem(sparse(T[3 0;3 1]),zeros(T,2);
            row_lower=[T(1),nothing],row_upper=[nothing,T(1)],
            column_lower=[nothing,nothing],column_upper=[nothing,T(1)])
        dirty=falses(2)
        r=JSimplex._propagate_row_bounds(p,BitVector([true,false]),dirty)
        lo=bound_value(r.problem.column_lower[1]);hi=bound_value(r.problem.column_upper[2])
        @test Q(lo)<Q(1,3)<=Q(nextfloat(lo))
        @test Q(hi)>=1-3Q(lo)>0
        @test Q(prevfloat(hi))<1-3Q(lo)
        @test all(dirty)
        @test !isfinite(p.column_lower[1]) && bound_value(p.column_upper[2])==one(T)
    end
end
