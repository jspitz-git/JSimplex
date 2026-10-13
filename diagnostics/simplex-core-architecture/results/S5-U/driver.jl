using Test, JSimplex, SparseArrays, LinearAlgebra, SHA, TOML
const U_COUNTS=zeros(Int,3) # case entry, initializer entry, testset entry
const U_RECORD=Ref{Any}(nothing) # one fixed post-unwind scalar record
const U_ROOT=abspath(ARGS[1])
const U_OUT=abspath(ARGS[2])
ispath(U_OUT) && error("output already exists")
mkdir(U_OUT)
const U_TEST=joinpath(U_ROOT,"test","simplex_precision_tests.jl")
const U_TEXT=read(U_TEST,String)
const U_EXPECTED=TOML.parsefile(joinpath(@__DIR__,"expected.toml"))
const U_PREFIX=String(Vector{UInt8}(codeunits(U_TEXT)[1:7647]))
const U_SUFFIX=String(Vector{UInt8}(codeunits(U_TEXT)[7648:end]))
@assert bytes2hex(sha256(U_TEXT))==U_EXPECTED["candidate"]
@assert bytes2hex(sha256(U_PREFIX))==U_EXPECTED["prefix"]
@assert bytes2hex(sha256(U_SUFFIX))==U_EXPECTED["suffix"]
@assert realpath(dirname(pathof(JSimplex)))==realpath(joinpath(U_ROOT,"src"))
@assert Threads.nthreads()==1 && BLAS.get_num_threads()==1
const U_INSERTIONS=TOML.parsefile(joinpath(@__DIR__,"insertions.toml"))["insertions"]
function u_instrument(s)
    for p in U_INSERTIONS
        @assert length(findall(p["anchor"],s))==1
        s=replace(s,p["anchor"]=>p["before"]*p["anchor"]*p["after"])
    end
    inverse=s
    for p in reverse(U_INSERTIONS)
        inverse=replace(inverse,p["before"]*p["anchor"]*p["after"]=>p["anchor"])
    end
    @assert inverse==U_SUFFIX
    @assert bytes2hex(sha256(s))==U_EXPECTED["executed"]
    return s
end
const U_EXECUTED=u_instrument(U_SUFFIX)
write(joinpath(U_OUT,"executed-suffix.jl"),U_EXECUTED)
function u_work_record(x)
    return Dict(string(k)=>(v isa Symbol ? string(v) : v) for (k,v) in pairs(x))
end
function u_run()
    result=nothing
    try
        result=@testset "S5-U focused actual supplied-basis stop test" begin
            include_string(Main,U_EXECUTED,U_TEST)
            @test U_COUNTS==[1,1,1]
            @test !isnothing(U_RECORD[]) && collect(string.(keys(U_RECORD[].checks)))==U_EXPECTED["checks"]
        end
    finally
        if !isnothing(U_RECORD[])
            x=U_RECORD[]
            open(joinpath(U_OUT,"case.toml"),"w") do io
                TOML.print(io,Dict("checks"=>Dict(string(k)=>v for (k,v) in pairs(x.checks)),
                    "observations"=>Dict(string(k)=>v for (k,v) in pairs(x.observations)),
                    "at_throw"=>u_work_record(x.at_throw),"after_unwind"=>u_work_record(x.after_unwind)))
            end
        end
        tc=isnothing(result) ? nothing : Test.get_test_counts(result)
        report=Dict("passes"=>isnothing(tc) ? -1 : tc.passes+tc.cumulative_passes,
            "fails"=>isnothing(tc) ? -1 : tc.fails+tc.cumulative_fails,
            "errors"=>isnothing(tc) ? -1 : tc.errors+tc.cumulative_errors,
            "broken"=>isnothing(tc) ? -1 : tc.broken+tc.cumulative_broken,
            "entry_counts"=>U_COUNTS,"test_sha256"=>bytes2hex(sha256(U_TEXT)),
            "prefix_sha256"=>bytes2hex(sha256(U_PREFIX)),"suffix_sha256"=>bytes2hex(sha256(U_SUFFIX)),
            "executed_sha256"=>bytes2hex(sha256(U_EXECUTED)),"source_root"=>U_ROOT,
            "module_path"=>pathof(JSimplex),"julia_threads"=>Threads.nthreads(),
            "blas_threads"=>BLAS.get_num_threads())
        open(joinpath(U_OUT,"report.toml"),"w") do io
            TOML.print(io,report)
        end
    end
end
u_run()
