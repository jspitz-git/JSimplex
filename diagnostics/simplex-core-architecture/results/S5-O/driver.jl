using Test, JSimplex, SparseArrays, LinearAlgebra, SHA, TOML
const O_COUNTS=zeros(Int,3) # PRE setup/handoff, completed case
const O_RECORD=Ref{Any}(nothing) # one fixed post-unwind scalar record
const O_ROOT=abspath(ARGS[1])
const O_OUT=abspath(ARGS[2])
ispath(O_OUT) && error("output already exists")
mkdir(O_OUT)
const O_TEST=joinpath(O_ROOT,"test","adaptive_pricing_lifecycle_tests.jl")
const O_TEXT=read(O_TEST,String)
const O_EXPECTED=TOML.parsefile(joinpath(@__DIR__,"expected.toml"))
const O_PREFIX=String(Vector{UInt8}(codeunits(O_TEXT)[1:19080]))
const O_SUFFIX=String(Vector{UInt8}(codeunits(O_TEXT)[19081:end]))
@assert bytes2hex(sha256(O_TEXT))==O_EXPECTED["candidate"]
@assert bytes2hex(sha256(O_PREFIX))==O_EXPECTED["prefix"]
@assert bytes2hex(sha256(O_SUFFIX))==O_EXPECTED["suffix"]
@assert realpath(dirname(pathof(JSimplex)))==realpath(joinpath(O_ROOT,"src"))
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const O_HELPERS=join(map(O_EXPECTED["helpers"]) do h
    positions=findall(h["text"],O_PREFIX)
    actual=O_PREFIX[only(positions)]
    @assert bytes2hex(sha256(actual))==h["sha256"]
    actual
end,"\n")
const O_INSERTIONS=TOML.parsefile(joinpath(@__DIR__,"insertions.toml"))["insertions"]
function o_instrument(s)
    for p in O_INSERTIONS
        @assert length(findall(p["anchor"],s))==1
        s=replace(s,p["anchor"]=>p["insert"]*p["anchor"])
    end
    inverse=s
    for p in reverse(O_INSERTIONS)
        inverse=replace(inverse,p["insert"]*p["anchor"]=>p["anchor"])
    end
    @assert inverse==O_SUFFIX
    @assert bytes2hex(sha256(s))==O_EXPECTED["executed"]
    return s
end
const O_EXECUTED=o_instrument(O_SUFFIX)
write(joinpath(O_OUT,"executed-suffix.jl"),O_EXECUTED)
write(joinpath(O_OUT,"actual-helpers.jl"),O_HELPERS)
include_string(Main,O_HELPERS,O_TEST)
const O_RESULT=@testset "S5-O focused actual pending observer test" begin
    include_string(Main,O_EXECUTED,O_TEST)
    @test O_COUNTS==[1,1,1]
    @test !isnothing(O_RECORD[]) && collect(string.(keys(O_RECORD[].checks)))==O_EXPECTED["checks"]
    if !isnothing(O_RECORD[])
        open(joinpath(O_OUT,"case.toml"),"w") do io
            TOML.print(io,Dict("checks"=>Dict(string(k)=>v for (k,v) in pairs(O_RECORD[].checks)),
                "observations"=>Dict(string(k)=>v for (k,v) in pairs(O_RECORD[].observations))))
        end
    end
end
const O_TC=Test.get_test_counts(O_RESULT)
const O_REPORT=Dict("passes"=>O_TC.passes+O_TC.cumulative_passes,
    "fails"=>O_TC.fails+O_TC.cumulative_fails,"errors"=>O_TC.errors+O_TC.cumulative_errors,
    "broken"=>O_TC.broken+O_TC.cumulative_broken,"entry_counts"=>O_COUNTS,
    "test_sha256"=>bytes2hex(sha256(O_TEXT)),"prefix_sha256"=>bytes2hex(sha256(O_PREFIX)),
    "suffix_sha256"=>bytes2hex(sha256(O_SUFFIX)),"executed_sha256"=>bytes2hex(sha256(O_EXECUTED)),
    "helpers_sha256"=>bytes2hex(sha256(O_HELPERS)),"source_root"=>O_ROOT,"module_path"=>pathof(JSimplex),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
open(joinpath(O_OUT,"report.toml"),"w") do io
    TOML.print(io,O_REPORT)
end
