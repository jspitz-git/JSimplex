using JSimplex, Serialization, TOML, SHA
for algorithm in ("dual","primal")
    path=joinpath(ARGS[1],"medium-"*algorithm*"-handoff.bin")
    d=deserialize(path)
    r=copy(d.provenance)
    r["handoff_sha256"]=bytes2hex(open(sha256,path))
    r["target_original_primal_feasible"]=JSimplex._original_primal_feasible(d.problem,d.target_primal,d.options.primal_tolerance)
    r["original_target_objective"]=JSimplex._restored_objective(d.problem,d.target_primal)
    open(joinpath(ARGS[2],algorithm*"-handoff.toml"),"w") do io;TOML.print(io,r;sorted=true);end
    println(algorithm,": ",r["saved_certificate_status"]," original feasible=",r["target_original_primal_feasible"])
end
