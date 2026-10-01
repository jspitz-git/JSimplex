# Report artificial-value evolution at the captured removal boundary.
using JSimplex,Serialization,LinearAlgebra
BLAS.set_num_threads(1)
function values_report(ws,map,label)
    basic=[j for j in ws.basis.basic_indices if map.phase_to_original[j]==0]
    art=ws.primal[map.artificial_columns]
    large=sort([(ws.primal[j],j) for j in basic];by=x->abs(x[1]),rev=true)
    println(label," iteration=",ws.iterations," sum=",sum(art)," positive_sum=",sum(max.(art,0.0)),
        " negative_sum=",sum(min.(art,0.0))," maxabs=",maximum(abs,art;init=0.0),
        " above_tolerance=",count(x->abs(x)>ws.options.primal_tolerance,art),
        " basic_count=",length(basic)," largest=",first(large,min(5,length(large))))
    flush(stdout)
end
function replay(prefix)
    phase=deserialize(prefix*"-phase.bin");map=deserialize(prefix*"-map.bin")
    original=deserialize(prefix*"-original.bin")
    println("PREFIX ",prefix)
    values_report(phase,map,"INITIAL")
    println("RESULT ",JSimplex.remove_artificials!(phase,map,original,phase.progress.numerical_policy,()->false))
    values_report(phase,map,"FINAL")
end
source=read(joinpath(dirname(pathof(JSimplex)),"simplex_phase_one.jl"),String)
a=first(findfirst("function _remove_artificials!",source))
b=first(findnext("\n\"\"\"Eliminate basic artificials",source,a))-1
body=source[a:b]
needle="        movement = phase.primal[leaving]/column[row]"
body=replace(body,needle=>needle*"\n        println(\"EXCHANGE row=\",row,\" entering=\",entering,\" artificial=\",phase.primal[leaving],\" pivot=\",column[row],\" direction_norm=\",maximum(abs,column),\" movement=\",movement)")
needle="        phase.basis.basic_indices[row]=entering"
body=replace(body,needle=>"        Main.values_report(phase,map,\"PREDICTED\")\n"*needle)
needle="        _phase_refactor!(phase,original,stop)"
body=replace(body,needle=>needle*"\n        Main.values_report(phase,map,\"RECONSTRUCTED\")")
needle="        _simplex_event!(phase,:artificial_removed)"
body=replace(body,needle=>needle*"\n        Main.values_report(phase,map,\"CERTIFIED\")")
Base.include_string(JSimplex,body,"diagnostic_artificial_evolution.jl")
for prefix in ARGS;Base.invokelatest(replay,prefix);end
