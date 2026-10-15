# Prospective driver only. No numerical execution during admission preparation.
using Test, TOML, LinearAlgebra, SparseArrays, JSimplex
const PHASE, OUTPUT, PROJECT = ARGS
const ROWS = Dict{String,Any}[]
mutable struct CaptureSet <: Test.AbstractTestSet
    description::String
    pass::Int
    fail::Int
    error::Int
    broken::Int
end
CaptureSet(s;kwargs...) = CaptureSet(s,0,0,0,0)
Test.record(s::CaptureSet,::Test.Pass) = (s.pass+=1)
Test.record(s::CaptureSet,r::Test.Fail) = (s.fail+=1;show(stdout,r);println())
Test.record(s::CaptureSet,r::Test.Error) = (s.error+=1;show(stdout,r);println())
Test.record(s::CaptureSet,::Test.Broken) = (s.broken+=1)
function Test.record(s::CaptureSet,t::CaptureSet)
    s.pass+=t.pass;s.fail+=t.fail;s.error+=t.error;s.broken+=t.broken
end
function Test.finish(s::CaptureSet)
    Test.get_testset_depth()>0 && Test.record(Test.get_testset(),s)
    return s
end
require(v,message) = v || error(message)
function save(name,data)
    path=joinpath(OUTPUT,name)
    ispath(path) && error("Output already exists: $path")
    open(path,"w") do io; TOML.print(io,data);flush(io);end
end
function group(f,name,expected)
    save("started-$(length(ROWS)+1).toml",Dict("name"=>name,"expected"=>collect(expected)))
    s=@testset CaptureSet "$name" begin f() end
    counts=(s.pass,s.fail,s.error,s.broken)
    row=Dict{String,Any}("name"=>name,"pass"=>s.pass,"fail"=>s.fail,"error"=>s.error,"broken"=>s.broken,"expected"=>collect(expected),"counts_match"=>counts==expected)
    push!(ROWS,row);save("group-$(length(ROWS)).toml",row)
    require(counts==expected,"Unexpected group result; stop without retry: $name")
end
function main()
    fatal="";completed=false
    try
        require(PHASE in ("red","green"),"Unknown phase")
        require(abspath(pathof(JSimplex))==joinpath(PROJECT,"src","JSimplex.jl"),"Wrong loaded source")
        require(Threads.nthreads()==1 && BLAS.get_num_threads()==1,"Thread configuration")
        require(precision(BigFloat)==256 && rounding(BigFloat)==RoundNearest,"Ambient arithmetic differs")
        if PHASE=="red"
            include(joinpath(PROJECT,"red.jl"))
            group("reference-contract",(0,3,0,0)) do
                Base.invokelatest(() -> getfield(Main,:run_direct_lu_red)())
            end
        else
            include(joinpath(PROJECT,"correctness.jl"))
            for (name,fn,count) in (("exports",:test_exports,130),("rejections",:test_export_rejections,66),
                ("orientation",:test_scale_selection,12),("normalization",:test_normalization_and_scaling,200),
                ("lifecycles",:test_lifecycles,18272),("fallback",:test_fallback_transitions,288))
                group(name,(count,0,0,0)) do; Base.invokelatest(() -> getfield(Main,fn)());end
            end
            for (name,count) in (("markowitz-sparse.jl",62),("markowitz-fill.jl",8),
                ("markowitz-triangular.jl",144),("prepared.jl",195),("lifecycle.jl",96),("stability.jl",84))
                group(name,(count,0,0,0)) do; include(joinpath(@__DIR__,"focused",name));end
            end
        end
        completed=true
    catch error
        fatal=sprint(showerror,error,catch_backtrace())
        println(stderr,fatal)
    finally
        save("raw.toml",Dict("phase"=>PHASE,"loaded_path"=>abspath(pathof(JSimplex)),
            "completed"=>completed,"fatal"=>fatal,"groups"=>ROWS,"all_expected"=>completed && all(r["counts_match"] for r in ROWS),
            "total_pass"=>sum(r["pass"] for r in ROWS;init=0),"total_fail"=>sum(r["fail"] for r in ROWS;init=0),
            "total_error"=>sum(r["error"] for r in ROWS;init=0),"total_broken"=>sum(r["broken"] for r in ROWS;init=0)))
    end
    completed || exit(2)
    exit(PHASE=="red" ? 1 : 0)
end
main()
