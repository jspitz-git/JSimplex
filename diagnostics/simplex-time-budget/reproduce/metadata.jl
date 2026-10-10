using JSimplex,Serialization,TOML,SHA
records=[]
for origin in ("dual","primal")
 path="/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-$(origin)-handoff.bin"
 d=deserialize(path);o=d.options;p=JSimplex.NumericalPolicy(Float64,o)
 push!(records,Dict("origin"=>origin,"sha256"=>bytes2hex(open(sha256,path)),"iterations"=>d.iterations,"refactorizations"=>d.refactorizations,"options"=>Dict(string(k)=>string(getfield(o,k)) for k in fieldnames(typeof(o))),"policy"=>Dict(string(k)=>string(getfield(p,k)) for k in fieldnames(typeof(p)))))
 d=nothing;GC.gc(true)
end
open(only(ARGS),"w") do io;TOML.print(io,Dict("handoffs"=>records));end
