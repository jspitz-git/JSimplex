# Run the established external matrix and record the complete measured source digest.
using JSimplex, SHA, TOML
function production_digest()
    root=dirname(dirname(pathof(JSimplex)))
    files=["Project.toml"]
    for (directory,_,names) in walkdir(joinpath(root,"src")), name in names
        endswith(name,".jl") && push!(files,relpath(joinpath(directory,name),root))
    end
    context=SHA.SHA2_256_CTX()
    for name in sort(files)
        SHA.update!(context,codeunits(name*"\0"))
        SHA.update!(context,read(joinpath(root,name)))
    end
    bytes2hex(SHA.digest!(context))
end
measured_digest=production_digest()
include(joinpath(@__DIR__,"../../basis-selective-preparation/reproduce/external.jl"))
@assert production_digest()==measured_digest
report=TOML.parsefile(ARGS[2]);report["production_sha256"]=measured_digest
open(ARGS[2],"w") do io
    TOML.print(io,report)
end
