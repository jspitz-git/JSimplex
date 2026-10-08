# Diagnostic-only instrumentation: capture ratio inputs without changing decisions.
using JSimplex, Serialization
const OUTPUT=abspath(ARGS[4])
ispath(OUTPUT) && error("Choose a fresh output directory")
source=read(joinpath(dirname(pathof(JSimplex)),"dual_simplex.jl"),String)
a=findfirst("function _dual_iteration_unchecked!",source).start
b=findnext("\nfunction _dual_after_iteration!",source,a).start-1
body=source[a:b]
@eval JSimplex begin
    const RATIO_SEQUENCE=Ref(0)
    function _capture_ratio_input(ws,row,orientation,delta,entering,flips,exhausted)
        ws.iterations <= 700 || return
        RATIO_SEQUENCE[]+=1
        d=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
           primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
           lower=copy(ws.lower),upper=copy(ws.upper),B=basis_matrix(ws),
           rho=copy(ws.scratch.rho),tableau=copy(ws.scratch.tableau_row),
           iteration=ws.iterations,row,orientation,delta,entering,flips=copy(flips),exhausted,
           rejected=copy(ws.scratch.rejected_entering),policy=ws.progress.numerical_policy)
        Main.Serialization.serialize(joinpath($OUTPUT,"ratio-$(RATIO_SEQUENCE[]).bin"),d)
    end
end
needle="    workspace.scratch.selected_entering = entering_index"
@assert count(needle,body)==1
body=replace(body,needle=>"    _capture_ratio_input(workspace,leaving_row,orientation,delta,entering_index,flips,exhausted)\n"*needle)
mkpath(OUTPUT)
write(joinpath(OUTPUT,"instrumented-source.jl"),body)
# The shared capture entry point requires a fresh directory; reserve provenance beside it.
source_path=joinpath(dirname(OUTPUT),basename(OUTPUT)*"-instrumented-source.jl")
mv(joinpath(OUTPUT,"instrumented-source.jl"),source_path)
rm(OUTPUT)
Base.include_string(JSimplex,body,"pilotnov-ratio-capture")
include(joinpath(@__DIR__,"../../numerical-guard-repair/reproduce/capture.jl"))
