# Observe exact removal failures without modifying numerical operations.
path=joinpath(@__DIR__,"broad_corpus.jl")
Base.include_string(Main,first(split(read(path,String),"\nhashes=instrument!()")),path)
function capture_removal(phase,mapping,original,label)
    prefix=CAPTURE_PREFIX[]*"-"*label
    detach(phase,prefix*"-phase.bin");detach(original,prefix*"-original.bin")
    serialize(prefix*"-map.bin",mapping)
    println("REMOVAL ",label," iteration=",phase.iterations," basic_artificials=",
        count(j->mapping.phase_to_original[j]==0,phase.basis.basic_indices)," prefix=",prefix)
    flush(stdout)
end
hashes=instrument!()
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
needle="        removed=remove_artificials!(phase,map,ws,policy,guard)"
@assert count(needle,source)==1
source=replace(source,needle=>"        Main.capture_removal(phase,map,ws,\"boundary\")\n"*needle)
a=first(findfirst("function _remove_artificials!",source))
b=first(findnext("\n\"\"\"Eliminate basic artificials",source,a))-1
body=source[a:b];lines=split(body,'\n')
for i in eachindex(lines)
    if occursin("return false",lines[i])
        label="rejected-line-"*string(i)
        lines[i]=replace(lines[i],"return false"=>"(Main.capture_removal(phase,map,original,$(repr(label))); println($(repr(lines[i])));return false)")
    end
end
source=source[1:a-1]*join(lines,'\n')*source[b+1:end]
source=replace(source,"        _crash_numerical_exception(exception) || rethrow()"=>
    "        println(\"PHASE EXCEPTION \",sprint(showerror,exception,catch_backtrace()));flush(stdout)\n        _crash_numerical_exception(exception) || rethrow()")
hashes["phase_capture"]=bytes2hex(sha256(source))
Base.include_string(JSimplex,source,"diagnostic_degen3_removal.jl")
Base.invokelatest(main,ARGS,hashes)
