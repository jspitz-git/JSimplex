using JSimplex, LinearAlgebra

# Continue the saved Windows reduced optimum on the original LP. For example:
#   julia --project=. diagnostics/runtime_projection_continuation.jl /path/to/runtime.mps
# JSIMPLEX_DIAG_TIME_LIMIT overrides the 240-second continuation cap.
const J = JSimplex
length(ARGS) == 1 || error("pass the path to runtime.mps")
BLAS.set_num_threads(1)

original = J.relax_integrality(read_mps(only(ARGS)))
presolved = J.presolve_problem(original)
presolved isa J.PresolveResult || error("presolve did not return a reduced LP")
scaled, scaling = J.scale_problem(presolved.problem)
rows, columns = size(scaled.A)
basic = zeros(Int, rows)
states = Vector{J.VariableState}(undef, rows + columns)
values = zeros(Float64, rows + columns)
open(joinpath(@__DIR__, "runtime_original_cost_fresh.tsv")) do io
    readline(io)
    for line in eachline(io)
        fields = split(line, '\t')
        index, row = parse(Int, fields[1]), parse(Int, fields[2])
        states[index] = getproperty(J, Symbol(fields[3]))
        values[index] = parse(Float64, fields[6])
        row > 0 && (basic[row] = index)
    end
end

restored = J.restore_basis(presolved, J.Basis(basic, states))
target = J.postsolve_primal(presolved,
    J.unscale_primal(scaling, values[1:columns]))
options = SolverOptions(verbose=false, basis_update=:suhl_suhl,
    basis_refactorization=:native, refactorization_interval=50)
workspace = J.initialize_workspace(J._minimization_problem(original), options)
workspace.basis = restored
J.recompute!(workspace; refactorize=true)
println("before pinf=", J.primal_infeasibility_summary(workspace),
    " dinf=", J.dual_infeasibility_summary(workspace))
exchanges = J._project_postsolve_basis!(workspace, target, () -> false)
isnothing(exchanges) && error("basis projection could not be completed")
println("exchanges=", exchanges,
    " after pinf=", J.primal_infeasibility_summary(workspace),
    " dinf=", J.dual_infeasibility_summary(workspace))
println("max structural diff=",
    maximum(abs.(workspace.primal[1:length(target)] .- target)))
flush(stdout)

prior_iterations = 44_145  # Iterations in the saved reduced optimum.
workspace.iterations = prior_iterations
cap_seconds = parse(Float64, get(ENV, "JSIMPLEX_DIAG_TIME_LIMIT", "240"))
start_ns = time_ns()
run = J._solve_continuous_dual!(workspace,
    () -> (time_ns() - start_ns) / 1e9 >= cap_seconds)
println("production_projected_status=", run.status,
    " iterations=", run.iterations,
    " cleanup_iterations=", run.iterations - prior_iterations,
    " refactorizations=", run.refactorizations,
    " elapsed=", (time_ns() - start_ns) / 1e9,
    " message=", run.message)
