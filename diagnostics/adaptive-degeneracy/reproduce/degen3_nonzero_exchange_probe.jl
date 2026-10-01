# Diagnostic-only test of a finite nonzero artificial exchange.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
a=first(findfirst("function _remove_artificials!",source))
b=first(findnext("\n\"\"\"Eliminate basic artificials",source,a))-1
body=source[a:b]
needle="        abs(phase.primal[leaving]) <= phase.options.primal_tolerance || return false"
@assert count(needle,body)==1
body=replace(body,needle=>"        println(\"ARTIFICIAL row=\",row,\" column=\",leaving,\" value=\",phase.primal[leaving])")
needle="        movement = phase.primal[leaving]/column[row]"
body=replace(body,needle=>needle*"\n        println(\"EXCHANGE entering=\",entering,\" state=\",phase.basis.states[entering],\" pivot=\",column[row],\" movement=\",movement)")
lines=split(body,'\n')
for i in eachindex(lines)
    lines[i]=replace(lines[i],"return false"=>"(println(\"REJECT: \",$(repr(lines[i])));return false)")
end
Base.include_string(JSimplex,join(lines,'\n'),"diagnostic_nonzero_artificial.jl")
function replay(prefix)
    phase=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    original=deserialize(prefix*"-original.bin")
    println("PREFIX ",prefix)
    println("RESULT ",JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false),
        " iteration=",original.iterations," original_point=",JSimplex._legacy_primal_point_certified(original))
end
for prefix in ARGS;Base.invokelatest(replay,prefix);end
