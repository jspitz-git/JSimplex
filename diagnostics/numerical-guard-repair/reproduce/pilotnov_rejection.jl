using JSimplex,Serialization
const OUTPUT=abspath(ARGS[4])
ispath(OUTPUT) && error("Choose a fresh output directory")
source=read(joinpath(dirname(pathof(JSimplex)),"dual_simplex.jl"),String)
a=findfirst("function _dual_iteration_unchecked!",source).start
b=findnext("\nfunction _dual_after_iteration!",source,a).start-1
body=source[a:b]
@eval JSimplex begin
    const FAILURE_SEQUENCE=Ref(0)
    function _record_dual_failure(ws,message)
        if ws.iterations>=690
            FAILURE_SEQUENCE[]+=1
            d=(problem=ws.problem,options=ws.options,basis=deepcopy(ws.basis),
                primal=copy(ws.primal),costs=copy(ws.costs),prices=copy(ws.reduced_costs),
                B=basis_matrix(ws),rho=copy(ws.scratch.rho),direction=copy(ws.scratch.row_solution),
                tableau=copy(ws.scratch.tableau_row),factor=deepcopy(ws.factorization),
                iteration=ws.iterations,row=ws.scratch.selected_row,
                entering=ws.scratch.selected_entering,message)
            Main.Serialization.serialize(joinpath($OUTPUT,"failure-$(FAILURE_SEQUENCE[]).bin"),d)
            println("FAILURE ",ws.iterations," ",message," row=",ws.scratch.selected_row);flush(stdout)
        end
        return DualTermination(NUMERICAL_ERROR,message)
    end
end
body=replace(body,"DualTermination(NUMERICAL_ERROR,"=>"_record_dual_failure(workspace,")
Base.include_string(JSimplex,body,"instrumented-dual-rejection")
include("capture.jl")
