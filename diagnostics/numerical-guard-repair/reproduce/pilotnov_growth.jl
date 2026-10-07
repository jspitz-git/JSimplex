using JSimplex,Serialization
const OUTPUT=abspath(ARGS[4])
ispath(OUTPUT) && error("Choose a fresh output directory")
source=read(joinpath(dirname(pathof(JSimplex)),"dual_simplex.jl"),String)
a=findfirst("function _dual_iteration_unchecked!",source).start
b=findnext("\nfunction _dual_after_iteration!",source,a).start-1
body=source[a:b]
@eval JSimplex begin
    const GROWTH_SEQUENCE=Ref(0)
    function _record_growth_pivot(ws,entering,row,pivot,primal_step,dual_step)
        ws.iterations<=700 || return
        GROWTH_SEQUENCE[]+=1
        d=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
            primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
            B=basis_matrix(ws),rho=copy(ws.scratch.rho),direction=copy(ws.scratch.row_solution),
            iteration=ws.iterations,entering,row,pivot,primal_step,dual_step,
            row_pivot=ws.scratch.tableau_row[entering])
        Main.Serialization.serialize(joinpath($OUTPUT,"pivot-$(GROWTH_SEQUENCE[]).bin"),d)
    end
end
body=replace(body,"    update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)"=>
    "    _record_growth_pivot(workspace,entering_index,leaving_row,pivot,primal_step,dual_step)\n    update_duals!(workspace, tableau_row, leaving_index, entering_index, dual_step)")
Base.include_string(JSimplex,body,"instrumented-pilotnov-growth")
include("capture.jl")
