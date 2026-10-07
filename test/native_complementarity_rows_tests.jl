using Test,JSimplex,SparseArrays

@testset "Complementarity resolves cancellation at active row bounds" begin
    for T in (Float32,Float64), upper in (true,false)
        scale=T(2)^(T===Float32 ? 30 : 60)
        A=sparse(reshape(T[scale,1,-scale],1,3))
        bound=T(50); y=T[upper ? -1 : 1]
        p=LinearProblem(A,vec(Matrix(A)).*y[1];
            row_lower=[upper ? nothing : bound],row_upper=[upper ? bound : nothing],
            column_lower=T[1,0,1],column_upper=[T(1),nothing,T(1)])
        options=SolverOptions(T;verbose=false)
        basis=JSimplex.Basis([2],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.AT_LOWER,upper ? JSimplex.AT_UPPER : JSimplex.AT_LOWER])
        x=T[1,bound,1]
        lo,hi=JSimplex._primal_row_bounds(A,x,Val(false))
        @test !JSimplex._primal_interval_at_bound(lo[1],hi[1],JSimplex.Bound(bound),options.primal_tolerance)
        @test JSimplex._original_primal_feasible(p,x,options.primal_tolerance)
        @test JSimplex._original_witness_certified(p,options,basis,x,y)
        # A feasible point away from the priced active bound is not optimal.
        inside=copy(x);inside[2]+=upper ? -one(T) : one(T)
        @test JSimplex._original_primal_feasible(p,inside,options.primal_tolerance)
        @test !JSimplex._original_witness_certified(p,options,basis,inside,y)
        outside=copy(x);outside[2]+=upper ? one(T) : -one(T)
        @test !JSimplex._original_witness_certified(p,options,basis,outside,y)
        @test !JSimplex._original_witness_certified(p,options,basis,x,-y)
        # Preserve basic stationarity while reversing the row price: the only
        # finite active bound now has the wrong dual sign.
        opposite = LinearProblem(A, -p.objective;
            row_lower=p.row_lower, row_upper=p.row_upper,
            column_lower=p.column_lower, column_upper=p.column_upper)
        @test !JSimplex._original_witness_certified(opposite,options,basis,x,-y)
    end
end
