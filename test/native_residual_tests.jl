using LinearAlgebra, SparseArrays, Random

@testset "Long residuals use bounded native scratch" begin
    # Long dot products previously allocated BigFloat values solely because
    # their pessimistic rounding bound exceeded a fixed fraction of tolerance.
    for T in (Float32, Float64), transposed in (false, true)
        row = repeat(T[2^20, 1, -2^20], 100)
        B = sparse(transposed ? reshape(row,:,1) : reshape(row,1,:))
        x = ones(T,300)
        rhs = T[100]
        scratch = JSimplex.SolveQualityScratch(T,1)
        policy = JSimplex.NumericalPolicy(T)
        check() = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
        quality = check()
        @test quality.reliable && quality.finite
        @test scratch.residual == T[0]
        @test (@allocated check()) <= 4096
        rhs[1] = T(1_000_000)
        @test !check().reliable
        @test scratch.residual == T[999900]
    end
end

@testset "Native residual acceptance agrees with exact input arithmetic" begin
    rng = MersenneTwister(47021)
    for T in (Float32,Float64), transposed in (false,true), exponent in (-20,0,20)
        B = sparse(T.(randn(rng,8,80)) .* T(2)^exponent)
        M = transposed ? transpose(B) : B
        x = T.(randn(rng,size(M,2)))
        rhs = M*x
        policy = JSimplex.NumericalPolicy(T)
        scratch = JSimplex.SolveQualityScratch(T,length(rhs))
        for perturbation in (zero(T), T(0.01)*maximum(abs,rhs))
            trial = copy(rhs); trial[1] += perturbation
            quality = JSimplex.solve_quality!(scratch,B,x,trial,policy;transposed)
            exact_M = Rational{BigInt}.(Matrix(M))
            exact_x,exact_rhs = Rational{BigInt}.(x),Rational{BigInt}.(trial)
            residual = exact_rhs-exact_M*exact_x
            scale = abs.(exact_rhs)+abs.(exact_M)*abs.(exact_x)
            error = maximum(abs.(residual)./scale)
            @test quality.finite
            @test quality.reliable == (error <= Rational{BigInt}(policy.solve_tolerance))
        end
    end
end
