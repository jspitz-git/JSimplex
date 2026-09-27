using JSimplex, TOML, LinearAlgebra
BLAS.set_num_threads(1)
problem=read_mps(joinpath(dirname(dirname(pathof(JSimplex))),"test/fixtures/solver/afiro.mps"))
options=SolverOptions(algorithm=:primal,simplex_strategy=:legacy,pricing=:steepest_edge,basis_update=:bartels_golub,basis_refactorization=:native,refactorization_interval=80,time_limit=Inf,verbose=false)
# Three distinct callback types, identical numerical input and event behavior.
struct ObserverA end
struct ObserverB end
struct ObserverC end
(::ObserverA)(reason,ws)=nothing
(::ObserverB)(reason,ws)=nothing
(::ObserverC)(reason,ws)=nothing
rows=Dict{String,Any}[]
for (label,observer) in [("none",nothing),("A",ObserverA()),("B",ObserverB()),("C",ObserverC()),("A_repeat",ObserverA())]
    global diagnostics=isnothing(observer) ? nothing : JSimplex.SimplexDiagnostics(;observer)
    GC.gc()
    stats=@timed @eval JSimplex._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
    result=stats.value
    @assert result.status==OPTIMAL
    @assert isapprox(result.objective_value,-464.7531428571429;atol=1e-7,rtol=1e-8)
    @assert JSimplex._original_primal_feasible(problem,result.primal,options.primal_tolerance)
    push!(rows,Dict("case"=>label,"seconds"=>stats.time,"compile_seconds"=>stats.compile_time,"recompile_seconds"=>stats.recompile_time,"allocated_bytes"=>stats.bytes,"iterations"=>result.statistics.iterations,"objective"=>result.objective_value))
    println(last(rows));flush(stdout)
    open(ARGS[1],"w") do io; TOML.print(io,Dict("source"=>pathof(JSimplex),"julia"=>string(VERSION),"samples"=>rows));end
end
