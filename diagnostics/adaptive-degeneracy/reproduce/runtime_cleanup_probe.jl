using JSimplex,Serialization,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
const JS=JSimplex
function mismatch(ws,row,entering,a,b,limit)
 println("MISMATCH row=",row," entering=",entering," row_pivot=",a," column_pivot=",b," bound=",limit," updates=",length(ws.factorization.updates));flush(stdout)
end
s=read(joinpath(dirname(pathof(JS)),"dual_simplex.jl"),String)
a="        if !_pivot_agrees(row_pivot, pivot, agreement)"
@assert count(a,s)==1
s=replace(s,a=>a*"\n            Main.mismatch(workspace,leaving_row,entering_index,row_pivot,pivot,agreement)")
Base.include_string(JS,s,"diagnostic_cleanup_pivots.jl")
s=read(joinpath(dirname(pathof(JS)),"simplex_pivot.jl"),String)
a="                        if !isnothing(terminal) && terminal.status == NUMERICAL_ERROR"
@assert count(a,s)==1
s=replace(s,a=>a*"\n                            println(\"RETRY_TERMINAL \",terminal.message);flush(stdout)")
a="            refresh_pending = false"
@assert count(a,s)==1
s=replace(s,a=>"            println(\"REJECTION \",rejection);flush(stdout)\n"*a)
Base.include_string(JS,s,"diagnostic_cleanup_retry.jl")
function probe()
 ws=deserialize(".superpowers/adaptive-degeneracy/runtime-failure-repair/jump-primal-final.bin")
 old=ws.progress
 ws.progress=JS.SimplexProgressContext(ws.problem;scaling=old.scaling,numerical_policy=old.numerical_policy)
 j=ws.scratch.perturbations;isnothing(j) || (j.workspace_id=objectid(ws))
 println("STATE iteration=",ws.iterations," options=",ws.options.algorithm," updates=",length(ws.factorization.updates)," perturbed=",ws.perturbed," journal=",isnothing(j) ? nothing : (j.active,j.level)," pinf=",JS.primal_infeasibility(ws)," dinf=",JS.dual_infeasibility(ws))
 start=time_ns();stop=()->(time_ns()-start)/1e9>120
 terminal=JS.dual_iteration!(ws,stop)
 println("RESULT ",terminal," iterations=",ws.iterations)
end
Base.invokelatest(probe)
