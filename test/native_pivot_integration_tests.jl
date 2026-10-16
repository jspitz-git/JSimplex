# OFFLINE Task3 candidate. No Julia execution until separate exact admission.
module NativePivotIntegrationTests
using Test, SparseArrays, JSimplex
const J = JSimplex

# Catches an option/factory route that drops selection or breaks public results.
# A future diagnostic driver brackets this function and observes native factories;
# the permanent test uses the real public solve, without injected numerical values.
function public_case(mode, symbol)
    problem = LinearProblem(sparse([1.0 1.0; 1.0 0.0; 0.0 1.0]), [-3.0, -2.0];
        row_upper=[4.0, 2.0, 3.0])
    inputs = (problem.A, problem.objective, problem.row_lower, problem.row_upper,
              problem.column_lower, problem.column_upper)
    saved = map(copy, inputs)
    options = SolverOptions(Float64; verbose=false, algorithm=:dual,
        simplex_strategy=:legacy, pricing=:steepest_edge, basis_update=mode,
        basis_refactorization=:native, native_pivot_policy=symbol,
        presolve=false, scaling=:off, partial_pricing=false,
        refactorization_interval=2, time_limit=5.0, iteration_limit=100)
    result = solve(problem; options)
    @test result.status == OPTIMAL
    @test result.primal == [2.0, 2.0]
    @test result.objective_value == -10.0
    @test options.native_pivot_policy === symbol
    @test all(isequal(a,b) for (a,b) in zip(inputs,saved))
    @test all(a === b for (a,b) in zip(inputs, (problem.A, problem.objective,
        problem.row_lower, problem.row_upper, problem.column_lower, problem.column_upper)))
    return result
end

# Catches reset of selection and collateral option changes in reconstruction.
function copied_options(a, b; changed...)
    for name in fieldnames(typeof(a))
        expected = haskey(changed,name) ? changed[name] : getfield(a,name)
        @test isequal(getfield(b,name),expected)
    end
end

# Catches a recovery factory reset, shared private factor/control ownership, or
# publication into the live workspace before the trial is accepted.
function recovery_case()
    problem = LinearProblem(sparse([1.0;;]), [1.0]; row_lower=[1.0])
    options = SolverOptions(verbose=false, native_pivot_policy=:threshold_one)
    w = J.initialize_workspace(problem, options)
    c = J.checkpoint_basis(w)
    factor = w.factorization
    native = factor.base.factorization
    controls = native.control
    control_bits = copy(reinterpret(UInt64,controls))
    live_arrays = (w.costs,w.lower,w.upper,w.primal,w.reduced_costs,w.pricing_weights,
                   w.basis.basic_indices,w.basis.states)
    live_values = map(copy,live_arrays)
    checkpoint_arrays = (c.costs,c.lower,c.upper,c.basis.basic_indices,c.basis.states)
    checkpoint_values = map(copy,checkpoint_arrays)
    old_refactors = w.refactorizations
    old_iterations = w.iterations
    trial = J._recovery_trial(w,c,J._guard_stop_callback(()->false))
    @test trial !== nothing
    @test w.factorization === factor
    @test factor.base.factorization === native
    @test native.control === controls
    @test reinterpret(UInt64,controls) == control_bits
    @test w.refactorizations == old_refactors + 1
    @test w.iterations == old_iterations
    @test all(isequal(a,b) for (a,b) in zip(live_arrays,live_values))
    @test all(a === b for (a,b) in zip(live_arrays, (w.costs,w.lower,w.upper,w.primal,
        w.reduced_costs,w.pricing_weights,w.basis.basic_indices,w.basis.states)))
    @test all(isequal(a,b) for (a,b) in zip(checkpoint_arrays,checkpoint_values))
    @test c.working_model == J._checkpoint_model(w)
    @test c.phase == J._checkpoint_phase(w)
    if trial !== nothing
        @test trial.factorization !== factor
        @test trial.factorization.base !== factor.base
        @test trial.factorization.base.factorization !== native
        @test trial.factorization.base.factorization.control !== controls
        @test trial.factorization.base.pivot_policy === J._NATIVE_PIVOT_ONE
        @test reinterpret(UInt64,trial.factorization.base.factorization.control) == control_bits
        @test trial.options.native_pivot_policy === :threshold_one
        @test trial.problem === w.problem
        @test trial.progress === w.progress
        @test trial.primal == [0.0,0.0]
        @test trial.basis.basic_indices == c.basis.basic_indices
        @test trial.basis.basic_indices !== c.basis.basic_indices
        @test trial.costs == c.costs && trial.costs !== c.costs
        @test trial.lower == c.lower && trial.lower !== c.lower
        @test trial.upper == c.upper && trial.upper !== c.upper
        @test trial.refactorizations == w.refactorizations
        @test trial.scratch.recovery_active
    end
    copied_options(options,J._phase_options(options,:primal);algorithm=:primal)
    copied_options(options,J._remaining_options(options;iterations=3,time_limit=11.0,algorithm=:primal);
        iteration_limit=options.iteration_limit-3,time_limit=11.0,algorithm=:primal)
    budget=(iteration_limit=31,iterations=4,time_limit_seconds=9.0)
    copied_options(options,J._lp_auxiliary_options(options,budget);
        iteration_limit=27,time_limit=9.0,scaling=:off,presolve=false)
    setprecision(BigFloat,256) do
        copied_options(options,J._copy_precision_options(BigFloat,options))
        copied_options(options,J._copy_precision_options(Float64,J._copy_precision_options(BigFloat,options)))
    end
    return trial
end

@testset "Native pivot policy public integration" begin
    for mode in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), symbol in (:default,:threshold_one)
        @testset "$mode / $symbol" begin
            public_case(mode,symbol)
        end
    end
end
@testset "Native pivot policy private recovery" begin
    recovery_case()
end
end
