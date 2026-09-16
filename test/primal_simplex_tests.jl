using JSimplex.SparseArrays

@testset "Primal simplex solves a model requiring phase I" begin
    problem = LinearProblem(sparse([1.0 1.0]), [1.0, 2.0]; row_lower=[1.0])
    before = deepcopy(problem)
    result = solve(problem; options=SolverOptions(algorithm=:primal, verbose=false))
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0, 0.0]
    @test result.objective_value ≈ 1.0
    for field in fieldnames(typeof(problem))
        @test getfield(problem, field) == getfield(before, field)
    end
end

@testset "Primal phase I and phase II across scalar types" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt})
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        lower = LinearProblem(sparse(T[1 1]), T[2, 1]; row_lower=T[1])
        result = @inferred solve(lower; options)
        @test result isa Solution{T}
        @test result.status == OPTIMAL
        @test result.primal ≈ T[0, 1]
        @test result.objective_value ≈ one(T)
        @test result.statistics.iterations >= 2

        upper = LinearProblem(sparse(T[1;;]), T[1]; row_upper=T[3],
                              objective_sense=MAX_SENSE)
        result = solve(upper; options)
        @test result.status == OPTIMAL
        @test result.primal ≈ T[3]
        @test result.objective_value ≈ T(3)

        infeasible = LinearProblem(sparse(T[1;;]), T[1];
                                   row_lower=T[2], column_upper=T[1])
        @test solve(infeasible; options).status == INFEASIBLE

        unbounded = LinearProblem(spzeros(T, 0, 1), T[-1])
        @test solve(unbounded; options).status == UNBOUNDED
    end
end

@testset "Primal simplex handles bounds, free variables, and empty models" begin
    options = SolverOptions(algorithm=:primal, verbose=false)
    bounded = LinearProblem(spzeros(0, 1), [-1.0]; column_upper=[2.0])
    result = solve(bounded; options)
    @test result.status == OPTIMAL
    @test result.primal == [2.0]
    @test result.objective_value == -2.0

    free = LinearProblem(sparse([1.0;;]), [2.0];
                         row_lower=[-3.0], row_upper=[-3.0],
                         column_lower=[nothing])
    result = solve(free; options)
    @test result.status == OPTIMAL
    @test result.primal ≈ [-3.0]
    @test result.objective_value ≈ -6.0

    empty = LinearProblem(spzeros(0, 0), Float64[]; objective_constant=7.0)
    result = solve(empty; options)
    @test result.status == OPTIMAL
    @test result.primal == Float64[]
    @test result.objective_value == 7.0

    binary = LinearProblem(spzeros(0, 1), [-1.0]; variable_domains=[BINARY])
    @test solve(binary; options).status == MIP_NOT_SUPPORTED
    relaxed = solve(binary; options, relax_integrality=true)
    @test relaxed.status == OPTIMAL
    @test relaxed.primal == [1.0]
end

@testset "Primal simplex honors limits across phases" begin
    problem = LinearProblem(sparse([1.0 1.0]), [2.0, 1.0]; row_lower=[1.0])
    for (limit, status) in ((0, ITERATION_LIMIT), (1, ITERATION_LIMIT), (2, OPTIMAL))
        result = solve(problem; options=SolverOptions(algorithm=:primal,
                                                      iteration_limit=limit, verbose=false))
        @test result.status == status
        @test result.statistics.iterations == limit
    end
    result = solve(problem; options=SolverOptions(algorithm=:primal,
                                                  time_limit=0.0, verbose=false))
    @test result.status == TIME_LIMIT
    @test result.statistics.iterations == 0
end

@testset "Phase I does not mistake a small reduced cost for infeasibility" begin
    problem = LinearProblem(sparse([1.0e-8;;]), [0.0]; row_lower=[1.0])
    result = solve(problem; options=SolverOptions(algorithm=:primal, verbose=false))
    @test result.status == OPTIMAL
    @test result.primal ≈ [1.0e8]
end

@testset "Phase I infeasibility requires a row-combination certificate" begin
    for T in (Float64, Rational{BigInt})
        feasible = LinearProblem(sparse(T[1;;]), T[0]; row_lower=T[1])
        infeasible = LinearProblem(sparse(T[1;;]), T[0];
                                   row_lower=T[2], column_upper=T[1])
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        feasible_workspace = JSimplex.initialize_workspace(feasible, options)
        infeasible_workspace = JSimplex.initialize_workspace(infeasible, options)
        @test !JSimplex._primal_infeasibility_certified(feasible_workspace, T[1])
        @test JSimplex._primal_infeasibility_certified(infeasible_workspace, T[1])
    end
end

@testset "Primal unboundedness requires a recession certificate" begin
    for T in (Float64, Rational{BigInt})
        options = SolverOptions(T; algorithm=:primal, verbose=false)
        unbounded = LinearProblem(spzeros(T, 0, 1), T[-1])
        bounded = LinearProblem(spzeros(T, 0, 1), T[-1]; column_upper=T[2])
        @test JSimplex._recession_direction_status(
            JSimplex.initialize_workspace(unbounded, options), T[1],
        ) == :certified
        @test JSimplex._recession_direction_status(
            JSimplex.initialize_workspace(bounded, options), T[1],
        ) == :invalid
    end
    phase_one = LinearProblem(sparse([1.0 0.0]), [0.0, -1.0]; row_lower=[1.0])
    @test solve(phase_one; options=SolverOptions(algorithm=:primal,
                                                  verbose=false)).status == UNBOUNDED
end

@testset "Primal simplex uses selectable basis factorizations and updates" begin
    problem = LinearProblem(sparse([1.0 1.0]), [2.0, 1.0]; row_lower=[1.0])
    for basis_update in (:pfi, :forrest_tomlin, :bartels_golub, :suhl_suhl),
        basis_refactorization in (:native, :markowitz)
        options = SolverOptions(; algorithm=:primal, basis_update,
                                 basis_refactorization,
                                 refactorization_interval=1, verbose=false)
        result = solve(problem; options)
        @test result.status == OPTIMAL
        @test result.primal ≈ [0.0, 1.0]
        @test result.objective_value ≈ 1.0
        @test result.statistics.refactorizations >= 2
    end
end
