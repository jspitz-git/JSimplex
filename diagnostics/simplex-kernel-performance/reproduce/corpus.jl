include("measure.jl")
label=first(ARGS)
manifest=TOML.parsefile("diagnostics/basis-selective-preparation/reproduce/external-inputs.toml")
report_path=joinpath(@__DIR__,"../results",label*"-corpus.toml")
records=length(ARGS)>1 ? TOML.parsefile(report_path)["cases"] : Dict{String,Any}[]
for entry in manifest["cases"]
    length(ARGS)>1 && entry["id"] != ARGS[2] && continue
    entry["id"] == "miplib/pk1" && continue
    @assert bytes2hex(open(sha256,entry["path"])) == entry["sha256"]
    entry["id"] == "mps/fast0507" && continue
    large = false
    for algorithm in ("primal","dual"), strategy in (large ? (:legacy,) : (:legacy,:adaptive)),
        manager in (large ? (:pfi,) : (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub))
        name=replace(entry["id"],"/"=>"-")*"-"*algorithm*"-"*string(strategy)*"-"*string(manager)
        output=joinpath(pwd(),".superpowers/kernel-performance",label*"-"*name)
        measure(entry["path"],algorithm,"10000","120",output;manager,strategy)
        record=TOML.parsefile(output*".toml")
        @assert record["status"]=="OPTIMAL"
        @assert record["original_primal_certified"]
        @assert isapprox(record["objective"],entry["objective"];rtol=1e-8,atol=1e-7)
        record["case"]=name
        push!(records,record)
        open(joinpath(@__DIR__,"../results",label*"-corpus.toml"),"w") do io
            TOML.print(io,Dict("cases"=>records))
        end
    end
end
