# UNEXECUTED; exactly one phase in a separately admitted ordinary Julia process.
using Test, LinearAlgebra, SparseArrays, TOML, PrecompileTools
PrecompileTools.verbose[] && error("Unexpected precompile verbosity")
using JSimplex
include(joinpath(@__DIR__,"recorder.jl"))
length(ARGS)==3 || error("Exactly output/project/phase required")
ARGS[3] in ("red300","green300","red600","green600") || error("Invalid phase")
# All includes resolve BEFORE main is defined or invoked. No late module/global lookup.
if startswith(ARGS[3],"red")
    include(joinpath(@__DIR__,"red.jl"))
else
    include(joinpath(@__DIR__,"split-suite.jl"))
    include(joinpath(ARGS[2],"test/split-bg-tests.jl"))
end
const GREEN_FUNCTIONS=(:lifecycles,:rejection_and_aliases,:export_modes,:focused_updates,
    :block_boundaries,:storage_failure_boundaries,:new_scratch_aliases,:split_allocator_differentials)
function exact_tree(root,expected)
    length(root.children)==length(expected["groups"]) || return false
    root.passed==root.failed==root.errored==root.broken==0 || return false
    isempty(root.failures) || return false
    for (t,e) in zip(root.children,expected["groups"])
        isempty(t.children) || return false
        (t.description,t.passed,t.failed,t.errored,t.broken)==
            (e["name"],e["pass"],e["fail"],e["error"],e["broken"]) || return false
        length(t.failures)==t.failed+t.errored || return false
    end
    return true
end
function main()
    output,project,phase=ARGS
    phase in ("red300","green300","red600","green600") || error("Invalid phase")
    mode=startswith(phase,"red") ? "red" : "green"
    raw=Dict{String,Any}("phase"=>phase,"complete"=>false,"fatal"=>"")
    root=RecordedTests.Capture("root")
    try
        realpath(pathof(JSimplex))==realpath(joinpath(project,"src/JSimplex.jl")) || error("Wrong package source")
        Threads.nthreads()==BLAS.get_num_threads()==1 || error("Thread count")
        raw["loaded"]=Dict(string(nameof(m))=>realpath(pathof(m)) for m in
            (JSimplex,SparseArrays,LinearAlgebra,TOML,Test,PrecompileTools))
        raw["threads"]=Threads.nthreads();raw["blas_threads"]=BLAS.get_num_threads()
        println(stderr,"BEGIN split BG driver ",phase);flush(stderr)
        if mode=="red"
            Test.@with_testset root begin
                run_split_bg_red()
            end
        else
            Test.@with_testset root begin
                println(stderr,"BEGIN split storage");flush(stderr)
                SplitStorageTests._sbu_structural_tests()
                println(stderr,"END split storage");flush(stderr)
                for name in GREEN_FUNCTIONS
                    println(stderr,"BEGIN ",name);flush(stderr)
                    getfield(SplitBGTests,name)()
                    println(stderr,"END ",name);flush(stderr)
                end
            end
        end
        raw["complete"]=true
    catch e
        raw["fatal"]=sprint(showerror,e,catch_backtrace());println(stderr,"FATAL DRIVER: ",raw["fatal"]);flush(stderr)
    finally
        raw["tests"]=RecordedTests.dictionary(root)
        p=joinpath(output,"raw.toml");ispath(p) && error("raw exists")
        open(p,"w") do io;TOML.print(io,raw);flush(io);end
    end
    expected=TOML.parsefile(joinpath(@__DIR__,"expected-tests.toml"))[mode]
    valid=raw["complete"] && isempty(raw["fatal"]) && exact_tree(root,expected)
    valid || (println(stderr,"GROUP/COUNT MISMATCH OR FATAL");flush(stderr))
    exit(valid ? (mode=="red" ? 1 : 0) : 2)
end
main()
