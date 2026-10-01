# Replay the captured artificial exchange without repeating Phase I.
using JSimplex,Serialization,LinearAlgebra,SparseArrays,TOML
BLAS.set_num_threads(1)
const PREFIX=ARGS[1]
function snapshot_report(ws,label)
    B=JSimplex.basis_matrix(ws);rhs=JSimplex._basis_primal_rhs(ws)
    policy=ws.progress.numerical_policy
    q=JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),B,ws.primal[ws.basis.basic_indices],rhs,policy)
    dq=JSimplex.solve_quality!(JSimplex.SolveQualityScratch(Float64,length(rhs)),B,ws.scratch.rho,ws.costs[ws.basis.basic_indices],policy;transposed=true)
    violations=[(max(JSimplex._lower_violation(ws.lower[j],ws.primal[j]),JSimplex._upper_violation(ws.upper[j],ws.primal[j])),j,ws.primal[j]) for j in eachindex(ws.primal)]
    sort!(violations;rev=true)
    println(label," iter=",ws.iterations," finite=",JSimplex._finite_workspace(ws)," feasible=",JSimplex._start_primal_feasible(ws),
        " point=",JSimplex._legacy_primal_point_certified(ws)," primal_quality=",q," dual_quality=",dq," violations=",first(violations,5));flush(stdout)
    serialize(PREFIX*"-"*label*".bin",ws)
end
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
a=first(findfirst("function _remove_artificials!",source));b=first(findnext("\n\"\"\"Eliminate basic artificials",source,a))-1
body=source[a:b]
needle="        movement = phase.primal[leaving]/column[row]"
body=replace(body,needle=>needle*"\n        println(\"EXCHANGE row=\",row,\" leaving=\",leaving,\" entering=\",entering,\" artificial=\",phase.primal[leaving],\" pivot=\",column[row],\" movement=\",movement)\n        Main.snapshot_report(phase,\"before\")")
needle="        _phase_refactor!(phase,original,stop)"
body=replace(body,needle=>"        Main.snapshot_report(phase,\"predicted\")\n"*needle*"\n        Main.snapshot_report(phase,\"recomputed\")")
Base.include_string(JSimplex,body,"diagnostic_exchange_replay.jl")
function main()
    phase=deserialize(PREFIX*"-phase.bin");original=deserialize(PREFIX*"-original.bin");map=deserialize(PREFIX*"-map.bin")
    println("RESULT ",JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false))
end
Base.invokelatest(main)
