using LinearAlgebra, SparseArrays

@testset "Shared simplex numerical quality" begin
    @test JSimplex._componentwise_backward_error([0.0], [0.0]) == 0.0
    @test isinf(JSimplex._componentwise_backward_error([1.0], [0.0]))
    @test JSimplex._componentwise_backward_error([1e-10], [2.0]) ≈ 5e-11
    @test isinf(JSimplex._componentwise_backward_error([0.0], [Inf]))

    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        policy = JSimplex.NumericalPolicy(T)
        @test policy isa JSimplex.NumericalPolicy{T}
        @test (policy.max_refinements, policy.max_pivot_candidates,
               policy.max_recovery_rounds, policy.stagnation_window,
               policy.max_precision_bits, policy.max_lp_refinements) == (3,8,2,64,512,8)
        @test all(!getfield(policy, key) for key in JSimplex.NUMERICAL_SWITCHES)
        B = sparse(T[2 1; 0 4])
        x = T[1,2]
        rhs = B*x
        saved_B, saved_rhs = copy(B), copy(rhs)
        scratch = JSimplex.SolveQualityScratch(T, 2)
        quality = JSimplex.solve_quality!(scratch, B, x, rhs, policy)
        @test quality isa JSimplex.SolveQuality{T}
        @test quality.finite && quality.reliable
        @test quality.absolute_error == 0
        @test scratch.residual == zeros(T,2)
        if T <: Rational
            @test quality.relative_error === nothing
            @test policy.solve_tolerance == 0
        else
            @test quality.relative_error == 0
            @test policy.solve_tolerance == T(256)*eps(T)
        end
        rhs[2] += one(T)
        quality = JSimplex.solve_quality!(scratch, B, x, rhs, policy)
        @test !quality.reliable && quality.finite
        @test quality.absolute_error == 1
        @test scratch.residual == T[0,1]
        @test B == saved_B
        @test rhs == saved_rhs + T[0,1]
        transpose_rhs = transpose(B)*x
        @test JSimplex.solve_quality!(scratch, B, x, transpose_rhs, policy;
                                     transposed=true).reliable
        @test_throws ArgumentError JSimplex.solve_quality!(scratch, B, x,
                                                          scratch.residual, policy)
    end

    policy = JSimplex.NumericalPolicy(Float64)
    scratch = JSimplex.SolveQualityScratch(Float64, 2)
    B = [2.0 1.0; 1.0 4.0]
    x = [1.0 + 2.0^-20, 2.0]
    rhs = [4.0, 9.0]
    errors = Float64[]
    for scale in (2.0^-500, 1.0, 2.0^500)
        q = JSimplex.solve_quality!(scratch, scale*B, x, scale*rhs, policy)
        @test !q.reliable && q.finite
        push!(errors, q.relative_error)
    end
    @test errors[1] ≈ errors[2] ≈ errors[3]

    # A small residual is not a bound on forward error for an ill-conditioned system.
    B = [1.0 1.0; 1.0 1.0 + 2.0^-50]
    @test JSimplex.solve_quality!(scratch, B, [2.0,-1.0], [1.0,1.0], policy).reliable

    # The true componentwise scale exceeds Float64 range. Higher-precision
    # evaluation must distinguish cancellation from a large actual residual.
    wide = JSimplex.SolveQualityScratch(Float64, 1)
    B = [1e308 -1e308]
    @test JSimplex.solve_quality!(wide, B, [2.0,2.0], [0.0], policy).reliable
    q = JSimplex.solve_quality!(wide, B, [2.0,2.0], [1e308], policy)
    @test !q.reliable && q.finite
    @test q.relative_error ≈ 0.2
    @test q.absolute_error == 1e308
    @test !JSimplex.solve_quality!(wide, [Inf 1.0], [0.0,1.0], [1.0], policy).finite
    tiny = floatmin(Float64)
    q = JSimplex.solve_quality!(wide, reshape([tiny],1,1), [tiny], [0.0], policy)
    @test !q.reliable
    @test q.relative_error == 1.0
    @test JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,1),
        ones(1,300), ones(300), [300.0], policy).reliable

    setprecision(BigFloat, 512) do
        B = BigFloat[1 1; 1 1+BigFloat(2)^-400]
        x = BigFloat[1,-1]
        rhs = BigFloat[0,-BigFloat(2)^-400]
        p = JSimplex.NumericalPolicy(BigFloat)
        saved = deepcopy(B)
        setprecision(BigFloat, 64) do
            s = JSimplex.SolveQualityScratch(BigFloat, 2)
            @test JSimplex.solve_quality!(s, B, x, rhs, p).reliable
            q = JSimplex.solve_quality!(s, B, x, BigFloat[0,0], p)
            @test !q.reliable
            @test q.absolute_error == -rhs[2]
            @test precision(B[2,2]) == 512 && B == saved
            @test precision(BigFloat) == 64
        end
    end
    setprecision(BigFloat, 8) do
        @test_throws ArgumentError JSimplex.NumericalPolicy(BigFloat)
    end
    @test_throws ArgumentError JSimplex.NumericalPolicy(Float64; solve_tolerance=Inf)
    @test_throws ArgumentError JSimplex.NumericalPolicy(Float64; max_refinements=-1)
    @test_throws ArgumentError JSimplex.NumericalPolicy(Float64; hypersparse=true)
end

@testset "Numerical strategy propagation" begin
    @test SolverOptions().simplex_strategy == :legacy
    adaptive = SolverOptions(simplex_strategy=:adaptive)
    @test adaptive.simplex_strategy == :adaptive
    @test SolverOptions(Float32, adaptive).simplex_strategy == :adaptive
    @test JSimplex._remaining_options(adaptive; iterations=5).simplex_strategy == :adaptive
    @test (@inferred JSimplex._context_numerical_policy(
        JSimplex.SolveContext(UInt64(0),Inf), adaptive)) isa JSimplex.NumericalPolicy{Float64}
    @test_throws ArgumentError SolverOptions(simplex_strategy=:unknown)
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        optimizer = JSimplex.Optimizer{T}()
        attr = JSimplex.MOI.RawOptimizerAttribute("simplex_strategy")
        @test JSimplex.MOI.supports(optimizer, attr)
        @test JSimplex.MOI.get(optimizer, attr) == :legacy
        JSimplex.MOI.set(optimizer, attr, :adaptive)
        @test JSimplex._solver_options(optimizer).simplex_strategy == :adaptive
        JSimplex.MOI.empty!(optimizer)
        @test JSimplex.MOI.get(optimizer, attr) == :adaptive
        @test JSimplex.MOI.get(JSimplex.Optimizer{T}(), attr) == :legacy
        @test_throws ArgumentError JSimplex.MOI.set(optimizer, attr, :unknown)
    end
    problem = read_mps(joinpath(@__DIR__,"fixtures","solver","netlib","adlittle.mps"))
    policy = JSimplex.NumericalPolicy(Float64; max_refinements=7)
    observed = Int[]
    diagnostics = JSimplex.SimplexDiagnostics(;
        observer=(reason,ws)->push!(observed,ws.progress.numerical_policy.max_refinements))
    result = JSimplex._solve_diagnosed(problem,diagnostics;
        options=SolverOptions(verbose=false,simplex_strategy=:adaptive), numerical_policy=policy)
    @test result.status == OPTIMAL
    @test !isempty(observed) && all(==(7),observed)
end
