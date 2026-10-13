using Test, JSimplex, SparseArrays, LinearAlgebra, SHA, TOML
const AA_COUNTS=zeros(Int,4) # case, INITIAL setup, crash, testset entries
const AA_RECORD=Ref{Any}(nothing) # one fixed post-unwind scalar record
const AA_ROOT=abspath(ARGS[1])
const AA_OUT=abspath(ARGS[2])
ispath(AA_OUT) && error("output already exists")
mkdir(AA_OUT)
const AA_TEST=joinpath(AA_ROOT,"test","simplex_start_state_tests.jl")
const AA_TEXT=read(AA_TEST,String)
const AA_EXPECTED=TOML.parsefile(joinpath(@__DIR__,"expected.toml"))
const AA_PREFIX=String(Vector{UInt8}(codeunits(AA_TEXT)[1:4774]))
const AA_SUFFIX=String(Vector{UInt8}(codeunits(AA_TEXT)[4775:end]))
@assert bytes2hex(sha256(AA_TEXT))==AA_EXPECTED["candidate"]
@assert bytes2hex(sha256(AA_PREFIX))==AA_EXPECTED["prefix"]
@assert bytes2hex(sha256(AA_SUFFIX))==AA_EXPECTED["suffix"]
@assert realpath(dirname(pathof(JSimplex)))==realpath(joinpath(AA_ROOT,"src"))
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const AA_INSERTIONS=TOML.parsefile(joinpath(@__DIR__,"insertions.toml"))["insertions"]
function aa_instrument(s)
    for p in AA_INSERTIONS
        @assert length(findall(p["anchor"],s))==1
        s=replace(s,p["anchor"]=>p["before"]*p["anchor"]*p["after"])
    end
    inverse=s
    for p in reverse(AA_INSERTIONS)
        inverse=replace(inverse,p["before"]*p["anchor"]*p["after"]=>p["anchor"])
    end
    @assert inverse==AA_SUFFIX
    @assert bytes2hex(sha256(s))==AA_EXPECTED["executed"]
    return s
end
const AA_EXECUTED=aa_instrument(AA_SUFFIX)
write(joinpath(AA_OUT,"executed-suffix.jl"),AA_EXECUTED)
function aa_record_dict(x)
    names=("iterations","refactorizations","crash_pivot","refactor_other","crash_fallback","crash_accepted","callbacks")
    return Dict(names[i]=>x[i] for i in 1:7)
end
function aa_save_case(x)
    path=joinpath(AA_OUT,"case.toml")
    ispath(path) && error("case already exists")
    open(path,"w") do io
        TOML.print(io,x)
    end
end
function aa_run()
    result=nothing
    try
        result=@testset "S5-AA focused actual crash fallback observer test" begin
            include_string(Main,AA_EXECUTED,AA_TEST)
            @test AA_COUNTS==[1,1,1,1]
            @test !isnothing(AA_RECORD[]) && Set(keys(AA_RECORD[]["checks"]))==Set(AA_EXPECTED["checks"])
        end
    finally
        tc=isnothing(result) ? nothing : Test.get_test_counts(result)
        report=Dict("passes"=>isnothing(tc) ? -1 : tc.passes+tc.cumulative_passes,
            "fails"=>isnothing(tc) ? -1 : tc.fails+tc.cumulative_fails,
            "errors"=>isnothing(tc) ? -1 : tc.errors+tc.cumulative_errors,
            "broken"=>isnothing(tc) ? -1 : tc.broken+tc.cumulative_broken,
            "entry_counts"=>AA_COUNTS,"test_sha256"=>bytes2hex(sha256(AA_TEXT)),
            "prefix_sha256"=>bytes2hex(sha256(AA_PREFIX)),"suffix_sha256"=>bytes2hex(sha256(AA_SUFFIX)),
            "executed_sha256"=>bytes2hex(sha256(AA_EXECUTED)),"source_root"=>AA_ROOT,
            "module_path"=>pathof(JSimplex),"julia_threads"=>Threads.nthreads(),
            "blas_threads"=>BLAS.get_num_threads())
        open(joinpath(AA_OUT,"report.toml"),"w") do io
            TOML.print(io,report)
        end
    end
end
aa_run()
