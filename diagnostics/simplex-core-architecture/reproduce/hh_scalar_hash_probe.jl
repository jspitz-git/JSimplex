# Isolate BigFloat serialization fingerprint mismatch; no timing comparison.
using JSimplex, SparseArrays, LinearAlgebra, Serialization, SHA, TOML
const JS=JSimplex
source=read(joinpath(@__DIR__,"hh_scalar_components.jl"),String)
for name in ("fixture","fingerprint")
    pos=first(findfirst("function $name(",source))
    Core.eval(Main,first(Meta.parse(source,pos)))
end
function canonical(B)
    io=IOBuffer()
    print(io,size(B),"\n",B.colptr,"\n",B.rowval,"\n")
    for x in B.nzval;print(io,precision(x),":",Rational{BigInt}(x),"\n");end
    bytes2hex(sha256(take!(io)))
end
function main(output)
    @assert Threads.nthreads()==BLAS.get_num_threads()==1
    rows=Dict[]
    for n in (8,32),dense in (false,true)
        control=fixture(BigFloat,n,dense);snapshot=deepcopy(control)
        firsthash=fingerprint(control);secondhash=fingerprint(control)
        for backend in (:native,:markowitz)
            B=fixture(BigFloat,n,dense);before=deepcopy(B);serialized_before=fingerprint(B)
            f=JS.HuangfuHallFactorization(B,Val(backend))
            exact=isequal(B,before) && isequal(B,snapshot)
            @assert exact && canonical(B)==canonical(before)==canonical(snapshot)
            push!(rows,Dict("dimension"=>n,"dense"=>dense,"backend"=>string(backend),
                "input_unchanged"=>exact,"canonical_hash"=>canonical(B),
                "repeated_serialization_equal"=>firsthash==secondhash,
                "serialized_before"=>serialized_before,"serialized_after"=>fingerprint(B),
                "serialized_equal_copy"=>fingerprint(deepcopy(B))==fingerprint(B)))
        end
    end
    open(io->TOML.print(io,Dict("complete"=>true,"rows"=>rows,"scope"=>"Separate BigFloat hash diagnosis, no cost rerun")),output,"w")
    println("BigFloat canonical input equality passed all 8 backend fixtures")
end
Base.invokelatest(main,ARGS[1])
