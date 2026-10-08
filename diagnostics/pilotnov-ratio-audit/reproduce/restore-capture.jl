# Capture original-space restoration without changing solver decisions.
using JSimplex, Serialization
const RESTORE_OUTPUT = abspath(ARGS[1])
ispath(RESTORE_OUTPUT) && error("Choose a fresh report prefix")
source = read(joinpath(dirname(pathof(JSimplex)), "solver.jl"), String)
start = findfirst("function _solve_diagnosed", source).start
body = source[start:end]
needle = "    objective = _restored_objective(problem, primal)"
@assert count(needle, body) == 1
body = replace(body, needle => "    Main.Serialization.serialize(Main.RESTORE_OUTPUT * \".bin\", (;problem, continuous_problem, presolved, scaling, run, primal, reduced, retried_original, typed_options))\n" * needle)
write(RESTORE_OUTPUT * "-source.jl", body)
Base.include_string(JSimplex, body, "pilotnov-restore-capture")
include("pilotnov.jl")
Base.invokelatest(main, RESTORE_OUTPUT * ".toml", "huangfu_hall", "markowitz")
