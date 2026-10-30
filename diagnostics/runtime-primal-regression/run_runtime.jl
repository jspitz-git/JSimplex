# Full solve with the options used for the runtime.mps regression.
# julia --project=. --startup-file=no run_runtime.jl path/to/runtime.mps
using JSimplex, LinearAlgebra

length(ARGS) == 1 || error("Expected one argument: path/to/runtime.mps")
println("JSimplex: ", pathof(JSimplex))
println("Julia: ", VERSION, ", architecture: ", Sys.ARCH,
        ", BLAS threads: ", BLAS.get_num_threads())
problem = read_mps(ARGS[1]; format=:free)
@time solution = solve(problem;
    options=SolverOptions(iteration_limit=1_000_000,
                          time_limit=36000.0,
                          basis_update=:huangfu_hall,
                          basis_refactorization=:native,
                          pricing=:steepest_edge,
                          algorithm=:primal,
                          refactorization_interval=240),
    relax_integrality=true)
@show solution.status solution.message
if solution.status == OPTIMAL
    @show solution.objective_value
end
@show solution.statistics.iterations solution.statistics.elapsed_seconds
