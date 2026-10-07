using JSimplex, Serialization
# Instrument only rejection exits in the unchanged stabilizer. No accepted
# pivot or recovery decision is changed; failed candidates own their snapshots.
source = read(joinpath(dirname(pathof(JSimplex)), "dual_simplex.jl"), String)
first_byte = findfirst("function _stabilize_small_dual_pivot!(workspace::SimplexWorkspace{Float64},", source).start
last_byte = findnext("\n_stabilize_small_dual_pivot!(::SimplexWorkspace", source, first_byte).start - 1
body = source[first_byte:last_byte]
const OUTPUT = abspath(ARGS[4])
ispath(OUTPUT) && error("Choose a fresh output directory")
@eval JSimplex begin
    const SMALL_REJECTIONS = Ref(0)
    function _record_small_rejection(ws, entering, pivot, coefficient, delta, line)
        SMALL_REJECTIONS[] += 1
        data = (problem=ws.problem, options=ws.options, basis=deepcopy(ws.basis),
            primal=copy(ws.primal), costs=copy(ws.costs), prices=copy(ws.reduced_costs),
            lower=copy(ws.lower), upper=copy(ws.upper), B=basis_matrix(ws),
            iteration=ws.iterations, offset=ws.progress.iteration_offset,
            entering, pivot, coefficient, delta, line)
        Main.Serialization.serialize(joinpath($OUTPUT, "small-rejection-$(SMALL_REJECTIONS[]).bin"), data)
        println("SMALL_REJECTION line=", line, " iteration=", ws.iterations,
                " pivot=", pivot, " entering=", entering)
        flush(stdout)
        return false
    end
end
instrumented = join([replace(line, "return false" =>
    "return _record_small_rejection(workspace, entering_index, pivot, tableau_coefficient, delta, $number)")
    for (number,line) in enumerate(split(body,'\n'))], '\n')
Base.include_string(JSimplex, instrumented, "instrumented-small-pivot")
# capture.jl creates OUTPUT before invoking the solver.
include("capture.jl")
open(joinpath(OUTPUT, "instrumented-function.txt"), "w") do io
    for (number,line) in enumerate(split(body,'\n'))
        println(io, number, ": ", line)
    end
end
