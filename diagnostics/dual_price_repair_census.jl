using JSimplex, Logging, TOML
source=read("src/dual_simplex.jl",String)
@eval JSimplex const repair_probe_counts = zeros(Int,2)
for (i,name) in enumerate(("_try_refine_dual_prices!","_try_refine_dual_pivot!"))
    start=findfirst("function $name(workspace::SimplexWorkspace{Float64}",source).start
    stop=findnext("\n$name(::SimplexWorkspace",source,start).start
    definition=source[start:prevind(source,stop)]
    definition=replace(definition,"stop_requested)\n"=>"stop_requested)\n    repair_probe_counts[$i] += 1\n";count=1)
    Base.include_string(JSimplex,definition,"throwaway-repair-census.jl")
end
rows=Dict{String,Any}[]
with_logger(NullLogger()) do
    for (name,path) in (("afiro","test/fixtures/solver/afiro.mps"),("adlittle","test/fixtures/solver/netlib/adlittle.mps"))
        p=read_mps(path)
        for method in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), interval in (1,20)
            fill!(JSimplex.repair_probe_counts,0)
            result=solve(p;options=SolverOptions(;algorithm=:dual,basis_update=method,refactorization_interval=interval,presolve=false,scaling=:off,verbose=false,iteration_limit=10_000))
            row=Dict("dataset"=>name,"method"=>string(method),"interval"=>interval,
                "status"=>string(result.status),"iterations"=>result.statistics.iterations,
                "price_repairs"=>JSimplex.repair_probe_counts[1],"pivot_repairs"=>JSimplex.repair_probe_counts[2])
            push!(rows,row);println(row);flush(stdout)
        end
    end
end
open(io->TOML.print(io,Dict("rows"=>rows);sorted=true),"diagnostics/dual-price-repair-census.toml","w")
