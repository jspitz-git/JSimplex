using JSimplex.SparseArrays

integrity_exact(value::Real) = Rational{BigInt}(value)
integrity_exact(value::BigFloat) = setprecision(BigFloat, precision(value)) do
    Rational{BigInt}(value)
end

function integrity_model_values(problem)
    values = vcat(problem.A.nzval, problem.objective, [problem.objective_constant])
    for bounds in (problem.row_lower, problem.row_upper, problem.column_lower, problem.column_upper)
        append!(values, (bound_value(bound) for bound in bounds if isfinite(bound)))
    end
    return values
end

@testset "BigFloat transformations preserve stored values and precision" begin
    for construction_precision in (128, 256)
        problem = setprecision(BigFloat, construction_precision) do
            value = BigFloat(2)^60 + 1
            LinearProblem(sparse(reshape(BigFloat[value, 1], 1, 2)), BigFloat[value, 2];
                objective_constant=value, objective_sense=MAX_SENSE,
                row_lower=BigFloat[value], row_upper=BigFloat[value],
                column_lower=BigFloat[2, 0], column_upper=BigFloat[value, value],
                variable_domains=[SEMI_CONTINUOUS, INTEGER])
        end
        original_values = integrity_exact.(integrity_model_values(problem))
        original_precisions = precision.(integrity_model_values(problem))
        for working_precision in (24, 53, construction_precision, 512)
            setprecision(BigFloat, working_precision) do
                relaxed = @inferred JSimplex.relax_integrality(problem)
                @test integrity_exact.(relaxed.A.nzval) == original_values[1:2]
                @test integrity_exact.(relaxed.objective) == original_values[3:4]
                @test integrity_exact(relaxed.objective_constant) == original_values[5]
                @test bound_value(relaxed.column_lower[1]) == 0
                @test relaxed.column_upper == problem.column_upper
                @test precision.(relaxed.A.nzval) == fill(construction_precision, 2)
                @test precision.(relaxed.objective) == fill(construction_precision, 2)

                working = @inferred JSimplex._minimization_problem(relaxed)
                @test working.objective_sense == MIN_SENSE
                @test integrity_exact.(working.A.nzval) == original_values[1:2]
                @test integrity_exact.(working.objective) == -original_values[3:4]
                @test integrity_exact(working.objective_constant) == -original_values[5]
                @test precision.(working.objective) == fill(construction_precision, 2)
                @test precision(working.objective_constant) == construction_precision
                for field in (:row_lower, :row_upper, :column_lower, :column_upper)
                    @test getfield(working, field) == getfield(relaxed, field)
                    @test precision.(bound_value.(getfield(working, field))) ==
                          precision.(bound_value.(getfield(relaxed, field)))
                end

                presolved = @inferred JSimplex.identity_presolve(working)
                scaling = @inferred JSimplex.identity_scaling(presolved.problem)
                values = problem.objective
                for restored in (
                    @inferred(JSimplex.unscale_primal(scaling, values)),
                    @inferred(JSimplex.unscale_dual(scaling, values[1:1])),
                    @inferred(JSimplex.postsolve_primal(presolved, values)),
                )
                    @test integrity_exact.(restored) == original_values[3:(2 + length(restored))]
                    @test precision.(restored) == fill(construction_precision, length(restored))
                    @test restored !== values
                end
                @test integrity_exact.(integrity_model_values(problem)) == original_values
                @test precision.(integrity_model_values(problem)) == original_precisions
                @test precision(BigFloat) == working_precision
            end
        end
    end
end

@testset "BigFloat copies do not round before subsequent arithmetic" begin
    values = setprecision(BigFloat, 256) do
        BigFloat[134217737]
    end
    setprecision(BigFloat, 24) do
        scaling = JSimplex.Scaling(BigFloat[3], BigFloat[3])
        @test JSimplex.unscale_primal(scaling, values) == BigFloat[44739244]
        @test JSimplex.unscale_dual(scaling, values) == BigFloat[44739244]
        factor = JSimplex.PFIFactorization(sparse(reshape(BigFloat[3], 1, 1)))
        # Generic forward LU divides by the unit lower diagonal before U;
        # that arithmetic may round. The transpose solve divides by 3 first.
        JSimplex.forward_solve(factor, values)
        @test JSimplex.transpose_solve(factor, values) == BigFloat[44739244]
        replacement = JSimplex.PFIFactorization(sparse(BigFloat[1 0; 0 1]))
        JSimplex.replace_column!(replacement, [BigFloat(3), only(values)], 1)
        @test JSimplex.forward_solve(replacement, BigFloat[1, 0])[2] == BigFloat(-44739244)
        @test JSimplex.transpose_solve(replacement, BigFloat[0, 1])[1] == BigFloat(-44739244)
        pivot = JSimplex.PFIFactorization(sparse(reshape(BigFloat[1], 1, 1)))
        JSimplex.replace_column!(pivot, values, 1)
        @test only(JSimplex.forward_solve(pivot, BigFloat[1])) == ldexp(BigFloat(16777215), -51)
        @test integrity_exact.(values) == [134217737 // big(1)]
        @test precision.(values) == [256]
    end
end

@testset "Cross-precision solves certify the stored original objective" begin
    for construction_precision in (128, 256), working_precision in (24, 53, 128, 256),
        exponent in (27, 60), sense in (MIN_SENSE, MAX_SENSE), interval in (1, 20),
        constant in (0, -3)
        problem = setprecision(BigFloat, construction_precision) do
            magnitude = BigFloat(2)^exponent
            LinearProblem(sparse(BigFloat[1 1]), BigFloat[magnitude + 1, magnitude];
                row_lower=BigFloat[1], row_upper=BigFloat[1],
                objective_constant=BigFloat(constant), objective_sense=sense)
        end
        before = integrity_exact.(integrity_model_values(problem))
        before_precisions = precision.(integrity_model_values(problem))
        setprecision(BigFloat, working_precision) do
            result = @inferred solve(problem;
                options=SolverOptions(BigFloat; refactorization_interval=interval))
            @test result isa Solution{BigFloat}
            @test result.status in (OPTIMAL, NUMERICAL_ERROR)
            working_precision == construction_precision && @test result.status == OPTIMAL
            if result.status == OPTIMAL
                expected_primal = sense == MAX_SENSE ? BigFloat[1, 0] : BigFloat[0, 1]
                expected_objective = big(2)^exponent + (sense == MAX_SENSE) + constant
                @test result.primal == expected_primal
                @test sum(integrity_exact.(problem.objective) .* integrity_exact.(result.primal)) +
                      integrity_exact(problem.objective_constant) == expected_objective
                # Evaluation uses solve-time precision and the original sense/constant.
                @test result.objective_value == BigFloat(expected_objective)
            else
                @test isnothing(result.primal)
                @test isnothing(result.objective_value)
            end
            @test integrity_exact.(integrity_model_values(problem)) == before
            @test precision.(integrity_model_values(problem)) == before_precisions
            @test precision(BigFloat) == working_precision
        end
    end
end

@testset "Reduced precision cannot lose the original objective constant" begin
    for construction_precision in (128, 256), working_precision in (24, 53, construction_precision),
        sense in (MIN_SENSE, MAX_SENSE), interval in (1, 20)
        problem = setprecision(BigFloat, construction_precision) do
            magnitude = BigFloat(2)^60
            LinearProblem(spzeros(BigFloat, 0, 1), BigFloat[magnitude + 1];
                column_lower=BigFloat[1], column_upper=BigFloat[1],
                objective_constant=-magnitude, objective_sense=sense)
        end
        setprecision(BigFloat, working_precision) do
            result = @inferred solve(problem;
                options=SolverOptions(BigFloat; refactorization_interval=interval))
            @test result isa Solution{BigFloat}
            @test result.status in (OPTIMAL, NUMERICAL_ERROR)
            working_precision == construction_precision && @test result.status == OPTIMAL
            if result.status == OPTIMAL
                @test result.primal == BigFloat[1]
                @test result.objective_value == BigFloat(1)
            else
                @test isnothing(result.primal)
                @test isnothing(result.objective_value)
            end
        end
    end
end

@testset "Identity restoration retains high-precision fixed variables" begin
    problem = setprecision(BigFloat, 256) do
        value = BigFloat(2)^60 + 1
        LinearProblem(spzeros(BigFloat, 0, 1), BigFloat[0];
            column_lower=BigFloat[value], column_upper=BigFloat[value])
    end
    setprecision(BigFloat, 24) do
        result = @inferred solve(problem)
        @test result.status == OPTIMAL
        @test integrity_exact(only(result.primal)) == big(2)^60 + 1
        @test precision(only(result.primal)) == 256
        @test result.objective_value == 0
    end
end

@testset "Original objective sense and constants across scalar types" begin
    for T in (Float32, Float64, Rational{BigInt}), sense in (MIN_SENSE, MAX_SENSE), interval in (1, 20)
        problem = LinearProblem(sparse(T[1 1]), T[3, 2]; row_lower=T[1], row_upper=T[1],
            objective_constant=T(1 // 2), objective_sense=sense,
            variable_domains=[INTEGER, CONTINUOUS])
        before = integrity_exact.(integrity_model_values(problem))
        result = @inferred solve(problem; relax_integrality=true,
            options=SolverOptions(T; refactorization_interval=interval))
        @test result isa Solution{T}
        @test result.status == OPTIMAL
        @test result.primal == (sense == MAX_SENSE ? T[1, 0] : T[0, 1])
        @test result.objective_value == (sense == MAX_SENSE ? T(7 // 2) : T(5 // 2))
        @test integrity_exact.(integrity_model_values(problem)) == before
    end
end

@testset "BigFloat options retain supplied tolerance values and precision" begin
    modes = (RoundNearest, RoundDown, RoundUp, RoundToZero, RoundFromZero)
    fields = (:primal_tolerance, :dual_tolerance, :zero_tolerance)
    for construction_precision in (128, 256)
        problem, options = setprecision(BigFloat, construction_precision) do
            tolerance = BigFloat(2)^-24 - BigFloat(2)^-80
            problem = LinearProblem(sparse(reshape(BigFloat[1], 1, 1)), BigFloat[0])
            options = SolverOptions(BigFloat; primal_tolerance=tolerance,
                dual_tolerance=2tolerance, zero_tolerance=tolerance / 4,
                iteration_limit=17, time_limit=2.5, refactorization_interval=1)
            problem, options
        end
        original = map(field -> integrity_exact(getfield(options, field)), fields)
        for working_precision in (24, 53, construction_precision, 512), mode in modes
            setprecision(BigFloat, working_precision) do
                setrounding(BigFloat, mode) do
                    copied = @inferred SolverOptions(BigFloat, options)
                    explicit = @inferred SolverOptions(BigFloat;
                        primal_tolerance=options.primal_tolerance,
                        dual_tolerance=options.dual_tolerance,
                        zero_tolerance=options.zero_tolerance)
                    workspace = @inferred JSimplex.initialize_workspace(problem, options)
                    @inferred JSimplex.recompute!(workspace; refactorize=true)
                    for candidate in (copied, explicit, workspace.options)
                        @test map(field -> integrity_exact(getfield(candidate, field)), fields) == original
                        @test map(field -> precision(getfield(candidate, field)), fields) ==
                              (construction_precision, construction_precision, construction_precision)
                    end
                    @test copied.iteration_limit == workspace.options.iteration_limit == 17
                    @test copied.time_limit == workspace.options.time_limit == 2.5
                    @test copied.refactorization_interval == workspace.options.refactorization_interval == 1
                    @test map(field -> integrity_exact(getfield(options, field)), fields) == original
                    @test map(field -> precision(getfield(options, field)), fields) ==
                          (construction_precision, construction_precision, construction_precision)
                    @test precision(BigFloat) == working_precision
                    @test rounding(BigFloat) == mode
                end
            end
        end
    end
end

@testset "Cross-precision status uses the supplied tolerance" begin
    modes = (RoundNearest, RoundDown, RoundUp, RoundToZero, RoundFromZero)
    for kind in (:primal, :dual, :zero), working_precision in (24, 53, 256),
        mode in modes, interval in (1, 20)
        problem, options = setprecision(BigFloat, 256) do
            gap = BigFloat(2)^(kind == :zero ? -20 : -24)
            tolerance = gap - BigFloat(2)^-80
            if kind == :primal
                problem = LinearProblem(sparse(reshape(BigFloat[1], 1, 1)), BigFloat[0];
                    row_lower=BigFloat[gap], column_lower=BigFloat[0], column_upper=BigFloat[0])
                options = SolverOptions(BigFloat; primal_tolerance=tolerance,
                    refactorization_interval=interval)
            elseif kind == :dual
                problem = LinearProblem(sparse(BigFloat[1 1]), BigFloat[0, -gap];
                    row_lower=BigFloat[1], row_upper=BigFloat[1])
                options = SolverOptions(BigFloat; dual_tolerance=tolerance,
                    refactorization_interval=interval)
            else
                problem = LinearProblem(sparse(reshape(BigFloat[gap], 1, 1)), BigFloat[1];
                    row_lower=BigFloat[1])
                options = SolverOptions(BigFloat; zero_tolerance=tolerance,
                    refactorization_interval=interval)
            end
            problem, options
        end
        original_values = integrity_exact.(integrity_model_values(problem))
        setprecision(BigFloat, working_precision) do
            setrounding(BigFloat, mode) do
                result = @inferred solve(problem; options)
                @test result isa Solution{BigFloat}
                if kind == :primal
                    @test result.status == INFEASIBLE
                else
                    @test result.status in (OPTIMAL, NUMERICAL_ERROR)
                    working_precision == 256 && @test result.status == OPTIMAL
                    if kind == :zero && mode == RoundNearest
                        @test result.status == OPTIMAL
                    end
                    if result.status == OPTIMAL
                        @test result.primal == (kind == :dual ? BigFloat[0, 1] : BigFloat[1048576])
                        @test result.objective_value == (kind == :dual ? BigFloat(2)^-24 * -1 : BigFloat(1048576))
                    end
                end
                if result.status != OPTIMAL
                    @test isnothing(result.primal)
                    @test isnothing(result.objective_value)
                end
                @test integrity_exact.(integrity_model_values(problem)) == original_values
                @test precision(options.primal_tolerance) == 256
                @test precision(options.dual_tolerance) == 256
                @test precision(options.zero_tolerance) == 256
                @test precision(BigFloat) == working_precision
                @test rounding(BigFloat) == mode
            end
        end
    end
end

@testset "Explicit BigFloat pivot tolerances retain their stored cutoff" begin
    modes = (RoundNearest, RoundDown, RoundUp, RoundToZero, RoundFromZero)
    gap, below, above = setprecision(BigFloat, 256) do
        gap = BigFloat(2)^-24
        gap, gap - BigFloat(2)^-80, gap + BigFloat(2)^-80
    end
    for working_precision in (24, 53, 256), mode in modes, sign in (-1, 1)
        setprecision(BigFloat, working_precision) do
            setrounding(BigFloat, mode) do
                basis = sparse(reshape(BigFloat[1], 1, 1))
                factor = JSimplex.PFIFactorization(basis)
                for refactorize in (false, true)
                    refactorize && JSimplex.refactorize!(factor, basis)
                    accepted = try
                        JSimplex.replace_column!(factor, BigFloat[sign * gap], 1; zero_tolerance=below)
                    catch error
                        error
                    end
                    @test accepted === factor
                    @test_throws JSimplex.LinearAlgebra.ZeroPivotException JSimplex.replace_column!(
                        factor, BigFloat[sign * gap], 1; zero_tolerance=gap)
                    @test_throws JSimplex.LinearAlgebra.ZeroPivotException JSimplex.replace_column!(
                        factor, BigFloat[sign * gap], 1; zero_tolerance=above)
                end
                @test integrity_exact(below) == 1 // big(2)^24 - 1 // big(2)^80
                @test integrity_exact(above) == 1 // big(2)^24 + 1 // big(2)^80
                @test precision(below) == precision(above) == 256
                @test precision(BigFloat) == working_precision
                @test rounding(BigFloat) == mode
            end
        end
    end
end

@testset "Tolerance conversion and validation across scalar types" begin
    for T in (Float32, Float64, Rational{BigInt})
        source = SolverOptions(T; primal_tolerance=T(1 // 4), dual_tolerance=T(1 // 8),
            zero_tolerance=T(1 // 16))
        copied = @inferred SolverOptions(T, source)
        converted = @inferred SolverOptions(Float64, source)
        @test copied.primal_tolerance === source.primal_tolerance
        @test copied.dual_tolerance === source.dual_tolerance
        @test copied.zero_tolerance === source.zero_tolerance
        @test converted.primal_tolerance === 0.25
        @test converted.dual_tolerance === 0.125
        @test converted.zero_tolerance === 0.0625
        factor = JSimplex.PFIFactorization(sparse(reshape(T[1], 1, 1)))
        @test JSimplex.replace_column!(factor, T[1 // 2], 1; zero_tolerance=1 // 4) === factor
        @test_throws JSimplex.LinearAlgebra.ZeroPivotException JSimplex.replace_column!(
            factor, T[1 // 2], 1; zero_tolerance=1 // 2)
    end
    for invalid in (-1, 0, Inf, NaN)
        @test_throws ArgumentError SolverOptions(BigFloat; primal_tolerance=BigFloat(invalid))
        @test_throws ArgumentError SolverOptions(BigFloat; dual_tolerance=BigFloat(invalid))
        @test_throws ArgumentError SolverOptions(BigFloat; zero_tolerance=BigFloat(invalid))
    end
end
