module OptionalPresolveCompositionTests

using Test, JSimplex, SparseArrays, LinearAlgebra
const J = JSimplex

function optional_options(T, kind; algorithm=:dual)
    return SolverOptions(T; verbose=false, scaling=:off, pricing=:devex,
        algorithm, presolve_row_sparsification=kind === :row,
        presolve_column_merging=kind === :merge,
        presolve_column_dominance=kind === :dominance)
end

# The isolated fourth/fifth variable must be removed by ORIGINAL presolve.
# Its nonzero fixing also tests the objective-constant shift through composition.
function with_fixed_column(T, matrix, costs, row_lower, row_upper;
                           lower=zeros(T, length(costs)), upper=fill(T(4), length(costs)))
    m, n = size(matrix)
    A = [sparse(T.(matrix)) spzeros(T, m, 1);
         spzeros(T, 1, n) sparse(reshape(T[1], 1, 1))]
    return LinearProblem(A, vcat(T.(costs), T(5));
        row_lower=vcat(T.(row_lower), T(2)), row_upper=vcat(T.(row_upper), T(2)),
        column_lower=vcat(T.(lower), T(2)), column_upper=vcat(T.(upper), T(2)),
        objective_constant=T(7 // 4))
end

function composition_fixture(T, kind)
    if kind === :merge
        p = with_fixed_column(T, [1 1 1; 1 1 -1], [1, 1, 1], [3, -1], [5, 2])
        points = (T[1, 1, 1, 2], T[2, 1, 1, 2])
    elseif kind === :row
        p = with_fixed_column(T, [3 5 7; 3 5 11; 2 -3 5], [0, 0, -1],
            [15, 3, -5], [15, 20, 8]; upper=T[3,1,1])
        points = (T[1, 1, 1, 2], T[3, 1 // 2, 1 // 2, 2])
    elseif kind === :dominance
        p = with_fixed_column(T, [1 1 1; 1 1 -1], [1, 2, 1],
            [3, -1], [5, 2]; upper=T[10,10,4])
        points = (T[1, 0, 2, 2], T[0, 1, 2, 2])
    else
        error("unknown composition fixture")
    end
    return p, points
end

same_model(p, q) = p.A.colptr == q.A.colptr && p.A.rowval == q.A.rowval &&
    J._PresolveWork.samevalues(p.A.nzval, q.A.nzval) &&
    all(J._PresolveWork.samevalues(getfield(p, name), getfield(q, name)) for name in
        (:objective, :row_lower, :row_upper, :column_lower, :column_upper)) &&
    J._PresolveWork.samevalue(p.objective_constant, q.objective_constant)

function same_objective(actual, expected, options)
    @test !isnothing(actual)
    isnothing(actual) && return
    @test isapprox(actual, expected;
        atol=options.primal_tolerance, rtol=options.primal_tolerance)
end

function reduced_run(p, options)
    problem = J._minimization_problem(p)
    policy = J._automatic_numerical_policy(problem, options)
    progress = J.SimplexProgressContext(problem; numerical_policy=policy, witness_problem=problem)
    return J._solve_continuous_dual(problem, options; progress)
end

function check_public(p::LinearProblem{T}, kind, plain) where T
    for algorithm in (:dual, :primal)
        options = optional_options(T, kind; algorithm)
        solution = solve(p; options)
        @test solution.status == OPTIMAL
        solution.status == OPTIMAL || continue
        @test J._original_primal_feasible(p, solution.primal, options.primal_tolerance)
        @test solution.primal[end] == T(2)
        same_objective(solution.objective_value, plain.objective_value, options)
        same_objective(J._restored_objective(p, solution.primal), plain.objective_value, options)
    end
end

# This deliberately uses the actual base result and its populated metadata,
# rather than identity_presolve: every successful chain crosses the original
# history boundary after tail/optional restoration.
function check_composition(p::LinearProblem{T}, points, kind; options=optional_options(T, kind)) where T
    before = deepcopy(p)
    n = size(p.A, 2)
    @test length(unique(p.objective)) > 1
    for x in points
        @test J._original_primal_feasible(p, x, options.primal_tolerance)
    end
    @test dot(p.objective, first(points)) != dot(p.objective, last(points))

    plain_options = SolverOptions(T; verbose=false, presolve=false, scaling=:off, pricing=:devex)
    plain = solve(p; options=plain_options)
    @test plain.status == OPTIMAL
    plain.status == OPTIMAL || return
    @test J._original_primal_feasible(p, plain.primal, options.primal_tolerance)

    history = J._PostsolveHistory(T)
    base = J._presolve_for_solve(p, options.primal_tolerance; history)
    @test base isa J.PresolveResult
    base isa J.PresolveResult || return
    @test !isempty(base.postsolve_stack)
    @test !isempty(history.metadata)
    @test length(history.metadata) == length(base.postsolve_stack)
    @test all(m.step === s for (m, s) in zip(history.metadata, base.postsolve_stack))
    @test size(base.problem.A, 2) < n
    history_length = length(history.metadata)

    result = J._with_optional_presolve(base, history, options)
    @test result isa J._OptionalPresolveResult
    result isa J._OptionalPresolveResult || return
    @test length(result.base_steps) == length(base.postsolve_stack)
    @test all(a === b for (a, b) in zip(result.base_steps, base.postsolve_stack))
    @test length(history.metadata) == history_length
    if kind === :row
        @test !isnothing(result.row_step)
        @test !isempty(result.row_step.operations)
        @test isnothing(result.column_step)
        @test isempty(result.fixing_steps)
    elseif kind === :merge
        @test !isnothing(result.column_step)
        @test length(result.column_step.undo) == 1
        @test length(result.column_step.kept) < result.column_step.columns
        @test isempty(result.fixing_steps)
    else
        @test isnothing(result.column_step)
        @test !isempty(result.fixing_steps)
        @test any(step -> step isa J.PresolveMap &&
            any(!isnothing, step.removed_values), result.fixing_steps)
    end
    if T === BigFloat && !isnothing(result.column_step)
        undo = first(result.column_step.undo)
        donor = undo.op.donor
        @test undo.donor_lower.value !== base.problem.column_lower[donor].value
        @test precision(undo.donor_lower.value) == precision(base.problem.column_lower[donor].value)
    end

    run = reduced_run(result.problem, options)
    @test run.status == OPTIMAL
    @test !isnothing(run.basis) && !isnothing(run.dual)
    run.status == OPTIMAL || return
    primal_only = J.postsolve_primal(result, run.primal)
    @test J._original_primal_feasible(p, primal_only, options.primal_tolerance)
    same_objective(J._restored_objective(p, primal_only), plain.objective_value, options)

    basis, restored = J._postsolve_with_dual(history, result,
        J.identity_scaling(result.problem), run, options)
    @test isempty(history.metadata) && isempty(history.propagation)
    @test isnothing(result.tail_history) ||
        (isempty(result.tail_history.metadata) && isempty(result.tail_history.propagation))
    @test !isnothing(basis) && !isnothing(restored)
    (isnothing(basis) || isnothing(restored)) && return
    @test length(restored) == n
    @test J._original_primal_feasible(p, restored, options.primal_tolerance)
    same_objective(J._restored_objective(p, restored), plain.objective_value, options)

    # Recompute/refactor/clean up on the complete ORIGINAL model, then invoke
    # its certificate explicitly. A successful provisional hint is insufficient.
    policy = J._automatic_numerical_policy(p, options)
    context = J.SolveContext(time_ns(), Inf, nothing, policy)
    final = J.cleanup_original(p, basis, options, context,
        run.iterations, run.refactorizations; target_primal=restored)
    @test final.status == OPTIMAL
    final.status == OPTIMAL || return
    @test final.refactorizations > run.refactorizations
    @test J._original_primal_feasible(p, final.primal, options.primal_tolerance)
    same_objective(J._restored_objective(p, final.primal), plain.objective_value, options)
    workspace = J.initialize_from_basis(J._minimization_problem(p), final.basis, options; policy)
    @test J._original_optimality_certified(workspace, final.primal)
    check_public(p, kind, plain)
    @test same_model(p, before)
    return result
end

@testset "Actual optional reductions compose with nonempty original history" begin
    for T in (Float32, Float64, BigFloat), kind in (:merge, :row, :dominance)
        @testset "$T / $kind" begin
            p, points = composition_fixture(T, kind)
            check_composition(p, points, kind)
        end
    end
end

@testset "Signed multiple merges restore reverse order and original certificate" begin
    # Target the merge helper directly so ordinary singleton presolve cannot
    # consume the proportional group before its two signed undo records exist.
    for T in (Float32, Float64, BigFloat)
        p = LinearProblem(sparse(T[1 2 -1]), T[1, 2, -1];
            row_lower=T[4], row_upper=T[7], column_lower=T[0, 1, -2],
            column_upper=T[2, 3, 1], objective_constant=T(3))
        before = deepcopy(p)
        options = optional_options(T, :merge)
        history = J._PostsolveHistory(T)
        result = J._with_optional_presolve(J.identity_presolve(p), history, options)
        @test result isa J._OptionalPresolveResult
        result isa J._OptionalPresolveResult || continue
        @test length(result.column_step.undo) == 2
        @test sort([undo.op.alpha for undo in result.column_step.undo]) == [-1, 2]
        @test all(undo.op.anchor == 1 for undo in result.column_step.undo)
        @test first(result.column_step.undo).op.upper_after ==
            last(result.column_step.undo).op.upper_before
        run = reduced_run(result.problem, options)
        @test run.status == OPTIMAL
        run.status == OPTIMAL || continue
        basis, restored = J._postsolve_with_dual(history, result,
            J.identity_scaling(result.problem), run, options)
        @test !isnothing(basis) && !isnothing(restored)
        (isnothing(basis) || isnothing(restored)) && continue
        @test J._original_primal_feasible(p, restored, options.primal_tolerance)
        same_objective(J._restored_objective(p, restored), T(7), options)
        final = J.cleanup_original(p, basis, options, J.SolveContext(time_ns(), Inf),
            run.iterations, run.refactorizations; target_primal=restored)
        @test final.status == OPTIMAL
        final.status == OPTIMAL || continue
        workspace = J.initialize_from_basis(p, final.basis, options)
        @test J._original_optimality_certified(workspace, final.primal)
        same_objective(J._restored_objective(p, final.primal), T(7), options)
        plain = solve(p; options=SolverOptions(T; presolve=false, verbose=false, scaling=:off))
        @test plain.status == OPTIMAL
        plain.status == OPTIMAL && same_objective(plain.objective_value, T(7), options)
        @test same_model(p, before)
    end
end

@testset "Stored BigFloat history and merge undo survive narrower ambient precision" begin
    p, points, options = setprecision(BigFloat, 256) do
        model, witnesses = composition_fixture(BigFloat, :merge)
        model, witnesses, optional_options(BigFloat, :merge)
    end
    setprecision(BigFloat, 96) do
        @test precision(first(p.A.nzval)) == 256
        @test precision(options.primal_tolerance) == 256
        before=deepcopy(p)
        history=J._PostsolveHistory(BigFloat)
        base=J._presolve_for_solve(p,options.primal_tolerance;history)
        result=J._with_optional_presolve(base,history,options)
        @test result isa J._OptionalPresolveResult
        @test !isempty(base.postsolve_stack) && !isnothing(result.column_step)
        @test size(result.problem.A)==(2,2)
        # Known exact reduced witness. This tests mixed-precision presolve and
        # restoration directly; it does not require a separate mixed-precision
        # simplex run to choose a particular point or basis.
        x=BigFloat[1,2];y=BigFloat[1,0]
        b=J.Basis([1,2],[J.BASIC,J.BASIC,J.AT_LOWER,J.AT_LOWER])
        @test J._original_primal_feasible(result.problem,x,options.primal_tolerance)
        @test J._original_witness_certified(result.problem,options,b,x,y)
        run=J.DualRunResult{BigFloat}(OPTIMAL,J._restored_objective(result.problem,x),x,0,0,"exact test witness",b,y)
        rb,rx=J._postsolve_with_dual(history,result,J.identity_scaling(result.problem),run,options)
        @test !isnothing(rb) && !isnothing(rx)
        @test J._original_primal_feasible(p,rx,options.primal_tolerance)
        @test J._original_witness_certified(p,options,rb,rx,BigFloat[1,0,0])
        # Original objective evaluation is deliberately conservative when stored
        # precision exceeds ambient precision; do not weaken that safeguard.
        exact_objective=J._exact_rational(p.objective_constant)+sum(J._exact_rational(c)*J._exact_rational(v) for (c,v) in zip(p.objective,rx))
        @test exact_objective==59//4
        @test isnothing(J._restored_objective(p,rx))
        @test first(result.column_step.undo).donor_lower.value !== base.problem.column_lower[2].value
        @test precision(first(result.column_step.undo).donor_lower.value)==precision(base.problem.column_lower[2].value)
        @test same_model(p,before)
        @test isempty(history.metadata) && isempty(result.tail_history.metadata)
        @test precision(BigFloat) == 96
    end
end

end # module
