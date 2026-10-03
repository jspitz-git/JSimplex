using SparseArrays
import MathOptInterface as MOI

@testset "Public Huangfu-Hall selection" begin
    # Removing the public mode must fail before any numeric factorization occurs.
    accepts = try
        SolverOptions(basis_update=:huangfu_hall).basis_update === :huangfu_hall
    catch
        false
    end
    @test accepts == (Int === Int64)
    if Int !== Int64
        @test_throws ArgumentError SolverOptions(basis_update=:huangfu_hall)
    end
    if accepts
        options = SolverOptions(basis_update=:huangfu_hall, verbose=false)
        @test options isa SolverOptions{Float64,:huangfu_hall,:native}
        @test SolverOptions(Float64, options).basis_update === :huangfu_hall
        factor = JSimplex._basis_factorization(sparse([2.0 1; 1 3]), options)
        @test factor isa JSimplex.HuangfuHallFactorization
        @test JSimplex.forward_solve(factor, [1.0, 4.0]) ≈ [-0.2, 1.4]
        for T in (Float32, BigFloat, Rational{BigInt})
            @test SolverOptions(T; basis_update=:huangfu_hall) isa SolverOptions{T,:huangfu_hall,:native}
            @test SolverOptions(T, options).basis_update === :huangfu_hall
        end
        @test_throws ArgumentError SolverOptions(basis_update=:huangfu_hall,
            basis_refactorization=:markowitz)

        optimizer = JSimplex.Optimizer()
        update = MOI.RawOptimizerAttribute("basis_update")
        backend = MOI.RawOptimizerAttribute("basis_refactorization")
        @test MOI.supports(optimizer, update)
        MOI.set(optimizer, update, :huangfu_hall)
        @test MOI.get(optimizer, update) === :huangfu_hall
        @test_throws ArgumentError MOI.set(optimizer, backend, :markowitz)
        @test MOI.get(optimizer, backend) === :native
        @test MOI.get(optimizer, update) === :huangfu_hall
        MOI.empty!(optimizer)
        @test MOI.get(optimizer, update) === :huangfu_hall
        MOI.set(optimizer, update, :pfi)
        MOI.set(optimizer, backend, :markowitz)
        @test_throws ArgumentError MOI.set(optimizer, update, :huangfu_hall)
        @test MOI.get(optimizer, update) === :pfi
        single = JSimplex.Optimizer{Float32}()
        MOI.set(single, update, :huangfu_hall)
        @test MOI.get(single, update) === :huangfu_hall
    end
end
