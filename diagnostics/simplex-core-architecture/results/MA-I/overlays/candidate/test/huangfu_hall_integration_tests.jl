using SparseArrays, LinearAlgebra
import MathOptInterface as MOI

@testset "Huangfu-Hall public solves" begin
    upper = LinearProblem(sparse([1.0 1; 1 0; 0 1]), [-3.0, -2.0]; row_upper=[4.0, 2.0, 3.0])
    lower = LinearProblem(sparse([1.0 1; -1 1]), [1.0, 2.0]; row_lower=[3.0, 1.0], column_lower=[0.0, 1.0])
    for algorithm in (:primal, :dual), strategy in (:legacy, :adaptive), presolve in (false, true), backend in (:native,:markowitz)
        options = SolverOptions(; algorithm, basis_update=:huangfu_hall, basis_refactorization=backend,
            simplex_strategy=strategy, presolve, verbose=false, refactorization_interval=2)
        for (problem, objective) in ((upper, -10.0), (lower, 5.0))
            result = solve(problem; options)
            @test result.status == OPTIMAL
            @test result.objective_value ≈ objective
            @test JSimplex._original_primal_feasible(problem, result.primal, options.primal_tolerance)
        end
    end
    for algorithm in (:primal, :dual), backend in (:native,:markowitz)
        source = MOI.Utilities.Model{Float64}()
        x = MOI.add_variables(source, 2)
        for v in x; MOI.add_constraint(source, v, MOI.GreaterThan(0.0)); end
        affine(a) = MOI.ScalarAffineFunction(MOI.ScalarAffineTerm.(a, x), 0.0)
        MOI.add_constraint(source, affine([1.0, 1.0]), MOI.GreaterThan(3.0))
        MOI.add_constraint(source, affine([-1.0, 1.0]), MOI.GreaterThan(1.0))
        objective = affine([1.0, 2.0])
        MOI.set(source, MOI.ObjectiveSense(), MOI.MIN_SENSE)
        MOI.set(source, MOI.ObjectiveFunction{typeof(objective)}(), objective)
        optimizer = JSimplex.Optimizer()
        MOI.set(optimizer, MOI.RawOptimizerAttribute("basis_update"), :huangfu_hall)
        MOI.set(optimizer, MOI.RawOptimizerAttribute("basis_refactorization"), backend)
        MOI.set(optimizer, MOI.RawOptimizerAttribute("algorithm"), algorithm)
        MOI.set(optimizer, MOI.RawOptimizerAttribute("presolve"), false)
        MOI.set(optimizer, MOI.Silent(), true)
        indices, _ = MOI.optimize!(optimizer, source)
        @test MOI.get(optimizer, MOI.TerminationStatus()) == MOI.OPTIMAL
        @test MOI.get(optimizer, MOI.ObjectiveValue()) ≈ 5.0
        @test [MOI.get(optimizer, MOI.VariablePrimal(), indices[v]) for v in x] ≈ [1.0, 2.0]
    end
end

@testset "Huangfu-Hall policy and failure boundaries" begin
    options = SolverOptions(basis_update=:huangfu_hall, verbose=false)
    B = SparseMatrixCSC{Float64,Int32}(sparse([2.0 1; 1 3]))
    @test try
        f = JSimplex.HuangfuHallFactorization(B)
        JSimplex.refactorize!(f, B)
        JSimplex.forward_solve(f, [1.0, 4.0]) ≈ [-0.2, 1.4]
    catch
        false
    end
    @test JSimplex._copy_precision_options(BigFloat, options).basis_update === :huangfu_hall
    exception = try
        JSimplex._hh_pack_update([Inf], JSimplex.HHUnitWorkspace(1), 1.0)
        nothing
    catch err
        err
    end
    @test JSimplex._is_numerical_exception(exception)
    p = LinearProblem(sparse([1.0 1; -1 1]), [1.0, 2.0]; row_lower=[3.0, 1.0])
    for keyword in (:precision_boosting, :lp_refinement)
        policy = JSimplex.NumericalPolicy(Float64; (keyword=>true,)...)
        @test JSimplex._solve_diagnosed(p, nothing; options, numerical_policy=policy).status == OPTIMAL
    end
    policy = JSimplex.NumericalPolicy(Float64; hypersparse=true)
    basis = JSimplex.Basis([1, 2], [JSimplex.BASIC, JSimplex.BASIC, JSimplex.AT_LOWER, JSimplex.AT_LOWER])
    ws = JSimplex.initialize_from_basis(p, basis, options; policy)
    @test !JSimplex._pipeline_sparse_available!(ws)
    for algorithm in (:primal, :dual)
        o = SolverOptions(basis_update=:huangfu_hall, verbose=false, algorithm=algorithm, presolve=false)
        result = JSimplex._solve_diagnosed(p, nothing; options=o, numerical_policy=policy)
        @test result.status == OPTIMAL
        @test result.objective_value ≈ 5.0
    end
    f = JSimplex.HuangfuHallFactorization(sparse([2.0 1; 1 3]))
    for transposed in (false, true)
        rhs = [1.0, 4.0]
        @test try
            JSimplex._pipeline_dense_basis!(rhs, f, rhs, transposed)
            rhs ≈ [-0.2, 1.4]
        catch
            false
        end
    end
end
