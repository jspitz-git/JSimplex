# Capture the actual phase-removal boundary and identify the rejecting check.
path=joinpath(@__DIR__,"broad_corpus.jl")
source=read(path,String)
Base.include_string(Main,first(split(source,"\nhashes=instrument!()")),path)
const BOUNDARY_PREFIX=ARGS[4]*"-boundary"
function capture_boundary(phase,mapping,original,policy)
    detach(phase,BOUNDARY_PREFIX*"-phase.bin")
    detach(original,BOUNDARY_PREFIX*"-original.bin")
    serialize(BOUNDARY_PREFIX*"-map.bin",mapping)
    println("BOUNDARY iteration=",phase.iterations," artificials=",length(mapping.artificial_columns),
        " basic_artificials=",count(j->mapping.phase_to_original[j]==0,phase.basis.basic_indices));flush(stdout)
end
hashes=instrument!()
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
needle="        removed=remove_artificials!(phase,map,ws,policy,guard)"
@assert count(needle,source)==1
source=replace(source,needle=>"        Main.capture_boundary(phase,map,ws,policy)\n"*needle)
lines=split(source,'\n')
for i in eachindex(lines)
    if occursin("return false",lines[i])
        lines[i]=replace(lines[i],"return false"=>"(println(\"REJECT simplex_phase_one:$i\"); return false)")
    end
end
source=join(lines,'\n')
# The catch's return has already been tagged above; print any caught exception.
source=replace(source,"        exception === guard.exception && rethrow()"=>
    "        println(\"PHASE EXCEPTION \",sprint(showerror,exception,catch_backtrace())); flush(stdout)\n        exception === guard.exception && rethrow()")
Base.include_string(JSimplex,source,"diagnostic_phase_rejection.jl")
Base.invokelatest(main,ARGS,hashes)
