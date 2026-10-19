using JSimplex, LinearAlgebra, SparseArrays, TOML, PrecompileTools, Profile
const J=JSimplex
const PHASE,OUTPUT,PROJECT=ARGS
include("helpers.jl")
function summary(t,outputs)
    f,clocks,modes=t.value
    Dict{String,Any}("bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
        "compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time,
        "outputs"=>[token.(x) for x in outputs],"modes"=>string.(collect(modes)))
end
function profile_once(F,backend,side,f,outputs)
    Profile.Allocs.clear()
    Profile.Allocs.start(sample_rate=1.0)
    t=try
        @timed lifecycle(F,backend,side,f,outputs)
    finally
        Profile.Allocs.stop()
    end
    data=Profile.Allocs.fetch()
    require(length(data.allocs)<=200000,"Unexpected allocation profile size")
    # Decode and aggregate only after profiling has stopped. Preserve every
    # distinct type/size/full symbolic stack, including C/runtime/harness frames.
    counts=Dict{Tuple{String,Int,String},Int}()
    for a in data.allocs
        stack=join((string(s.func," | ",s.file,":",s.line," | C=",s.from_c," | inline=",s.inlined) for s in a.stacktrace),"\n")
        key=(string(a.type),a.size,stack);counts[key]=get(counts,key,0)+1
    end
    records=[Dict("type"=>k[1],"size"=>k[2],"stack"=>k[3],"count"=>v) for (k,v) in sort!(collect(counts);by=first)]
    count=length(data.allocs);bytes=sum((a.size for a in data.allocs);init=0)
    Profile.Allocs.clear()
    return t,records,count,bytes
end
function side_run(backend,side,f,input,id)
    F=J.BartelsGolubFactorization;outputs=[zeros(f.n) for _ in 1:24]
    for _ in 1:3
        lifecycle(F,backend,side,f,outputs)
    end
    t=@timed lifecycle(F,backend,side,f,outputs)
    ordinary=summary(t,outputs);t=nothing
    t,records,count,bytes=profile_once(F,backend,side,f,outputs)
    profiled=summary(t,outputs)
    row=Dict("id"=>id,"fixture"=>f.name,"backend"=>string(typeof(backend).parameters[1]),
        "side"=>string(typeof(side).parameters[1]),"warm_lifecycles"=>3,"sample_rate"=>1.0,
        "ordinary"=>ordinary,"profiled"=>profiled,"allocations"=>records,
        "profile_count"=>count,"profile_bytes"=>bytes,"inputs_unchanged"=>unchanged(f,input))
    save("profile-$id.toml",row)
    require(row["inputs_unchanged"] && ordinary["outputs"]==profiled["outputs"] && ordinary["modes"]==profiled["modes"],"Profile changed output/input")
    require(ordinary["compile_seconds"]==ordinary["recompile_seconds"]==profiled["compile_seconds"]==profiled["recompile_seconds"]==0,"Compilation in observed lifecycle")
    return row
end
function main()
    complete=false;fatal="";done=0;loaded=Dict{String,String}()
    try
        require(PHASE=="profile300","Unexpected phase")
        require(realpath(pathof(J))==realpath(joinpath(PROJECT,"src/JSimplex.jl")),"Wrong module")
        require(Threads.nthreads()==BLAS.get_num_threads()==1 && !PrecompileTools.verbose[],"Threads/precompile")
        loaded=Dict(string(nameof(m))=>realpath(pathof(m)) for m in (J,LinearAlgebra,SparseArrays,TOML,PrecompileTools,Profile))
        println(stderr,"BEGIN BG export allocation provenance");flush(stderr)
        # Initialize profile start/stop/decode on an empty interval; no solver work.
        Profile.Allocs.clear();Profile.Allocs.start(sample_rate=1.0);Profile.Allocs.stop();Profile.Allocs.fetch();Profile.Allocs.clear()
        inputs=TOML.parsefile(joinpath(@__DIR__,"inputs.toml"))["fixtures"]
        for input in inputs, backend in (Val(:native),Val(:markowitz))
            f=decode_fixture(input)
            a=side_run(backend,Val(:reference),f,input,done+1);done+=1
            b=side_run(backend,Val(:candidate),f,input,done+1);done+=1
            require(a["ordinary"]["outputs"]==b["ordinary"]["outputs"] && a["ordinary"]["modes"]==b["ordinary"]["modes"],"Paired output disagreement")
        end
        complete=true
    catch e
        fatal=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL PROFILE: ",fatal);flush(stderr)
    finally
        Profile.Allocs.stop()
        save("raw.toml",Dict("complete"=>complete,"fatal"=>fatal,"records"=>done,"phase"=>PHASE,
            "loaded"=>loaded,"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
    end
    complete || exit(2)
end
main()
