using LinearAlgebra

@testset "Native residual bounds require gradual underflow" begin
    previous = get_zero_subnormals()
    try
        for T in (Float32,Float64)
            set_zero_subnormals(false)
            a = nextfloat(floatmin(T))
            x = T[nextfloat(one(T))]
            B = reshape(T[a],1,1)
            rhs = T[a*x[1]]
            policy = JSimplex.NumericalPolicy(T;solve_tolerance=eps(T)^3)
            residual = Rational{BigInt}(rhs[1])-Rational{BigInt}(a)*Rational{BigInt}(x[1])
            scale = abs(Rational{BigInt}(rhs[1]))+abs(Rational{BigInt}(a)*Rational{BigInt}(x[1]))
            @test abs(residual)/scale > Rational{BigInt}(policy.solve_tolerance)
            if set_zero_subnormals(true)
                scratch = JSimplex.SolveQualityScratch(T,1)
                @test isnothing(JSimplex._compensated_solve_quality!(scratch,B,x,rhs,policy,false))
                @test !JSimplex.solve_quality!(scratch,B,x,rhs,policy).reliable
            else
                @test_skip "Hardware does not support flushing subnormals"
            end
        end
    finally
        set_zero_subnormals(previous)
    end
    @test get_zero_subnormals() == previous
end
