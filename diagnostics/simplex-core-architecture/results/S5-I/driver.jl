using Test, JSimplex, SparseArrays, LinearAlgebra, SHA, TOML
const I_COUNTS=zeros(Int,3) # setup, transfer, completed case; no numerical calls
const I_ROWS=Vector{Any}(undef,2) # fixed post-case scalar/counter records only
const I_ROOT=abspath(ARGS[1])
const I_OUT=abspath(ARGS[2])
ispath(I_OUT) && error("output already exists")
mkdir(I_OUT)
const I_TEST=joinpath(I_ROOT,"test","simplex_precision_state_tests.jl")
const I_TEXT=read(I_TEST,String)
const I_MARKER="\n# BEGIN ACTIVE JOURNAL INTERRUPTION COVERAGE\n"
const I_SPLIT=only(findall(I_MARKER,I_TEXT))
const I_PREFIX=I_TEXT[1:first(I_SPLIT)-1]
const I_SUFFIX=I_TEXT[first(I_SPLIT):end]
const I_EXPECTED=TOML.parsefile(joinpath(@__DIR__,"expected.toml"))
@assert bytes2hex(sha256(I_TEXT))==I_EXPECTED["candidate"]
@assert bytes2hex(sha256(I_PREFIX))==I_EXPECTED["prefix"]
@assert bytes2hex(sha256(I_SUFFIX))==I_EXPECTED["suffix"]
@assert realpath(dirname(pathof(JSimplex)))==realpath(joinpath(I_ROOT,"src"))
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const I_INSERTIONS=TOML.parsefile(joinpath(@__DIR__,"insertions.toml"))["insertions"]
function instrument_suffix(s)
    for p in I_INSERTIONS
        @assert length(findall(p["anchor"],s))==1
        s=replace(s,p["anchor"]=>p["insert"]*p["anchor"])
    end
    inverse=s
    for p in reverse(I_INSERTIONS)
        inverse=replace(inverse,p["insert"]*p["anchor"]=>p["anchor"])
    end
    @assert inverse==I_SUFFIX
    return s
end
const I_EXECUTED=instrument_suffix(I_SUFFIX)
write(joinpath(I_OUT,"executed-suffix.jl"),I_EXECUTED)
const I_RESULT=@testset "S5-I focused actual test suffix" begin
    include_string(Main,I_EXECUTED,I_TEST)
    @test I_COUNTS==[2,2,2]
    @test Tuple(r.mode for r in I_ROWS)==("stop","throw")
end
const I_TC=Test.get_test_counts(I_RESULT)
const I_REPORT=Dict("passes"=>I_TC.passes+I_TC.cumulative_passes,
    "fails"=>I_TC.fails+I_TC.cumulative_fails,"errors"=>I_TC.errors+I_TC.cumulative_errors,
    "broken"=>I_TC.broken+I_TC.cumulative_broken,"entry_counts"=>I_COUNTS,
    "test_sha256"=>bytes2hex(sha256(I_TEXT)),"prefix_sha256"=>bytes2hex(sha256(I_PREFIX)),
    "suffix_sha256"=>bytes2hex(sha256(I_SUFFIX)),"executed_sha256"=>bytes2hex(sha256(I_EXECUTED)),
    "source_root"=>I_ROOT,"module_path"=>pathof(JSimplex),
    "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
    "kernel_keys"=>collect(string.(JSimplex.SIMPLEX_KERNEL_KEYS)),"event_keys"=>collect(string.(JSimplex.SIMPLEX_EVENT_REASONS)),
    "cases"=>[Dict(string(k)=>(v isa Tuple ? collect(v) : v) for (k,v) in pairs(r)) for r in I_ROWS])
open(joinpath(I_OUT,"report.toml"),"w") do io
    TOML.print(io,I_REPORT)
end
