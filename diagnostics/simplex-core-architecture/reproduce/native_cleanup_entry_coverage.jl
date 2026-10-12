using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const OUT=only(ARGS)
@assert !ispath(OUT)
const GLOBALS=(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
@assert GLOBALS==(256,RoundNearest,RoundNearest,false) && Threads.nthreads()==BLAS.get_num_threads()==1
const SOURCE=read(joinpath(ROOT,"test/primal_perturbation_integration_tests.jl"),String)
function definition(path,name)
    source=read(joinpath(ROOT,path),String)
    found=match(Regex("(?ms)^function "*name*"\\(.*?^end\\n"),source)
    @assert !isnothing(found)
    found.match
end
const MONITOR=definition("test/primal_perturbation_tests.jl","primal_stalled_monitor")
const HELPER=definition("test/primal_perturbation_integration_tests.jl","shifted_primal_workspace")
const START=findfirst("# Exercise native cleanup's first public entry",SOURCE)
@assert !isnothing(START)
const NEW=SOURCE[first(START):end]
const metadata=Dict{String,Any}("source"=>pathof(JSimplex),"root"=>ROOT,"test_sha256"=>bytes2hex(sha256(SOURCE)),
    "new_sha256"=>bytes2hex(sha256(NEW)),"helper_sha256"=>bytes2hex(sha256(HELPER)),
    "monitor_sha256"=>bytes2hex(sha256(MONITOR)),"exception"=>"none","julia_version"=>string(VERSION),
    "arch"=>string(Sys.ARCH),"threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads())
try
    @testset "Native entry coverage actual source" begin
        @test occursin("callback_calls[] == 1",NEW)
        @test occursin("d.kernel_calls == before.kernel_calls",NEW)
        @test occursin("ws.scratch.perturbations === journal",NEW)
        include_string(Main,MONITOR,"actual-primal-stalled-monitor.jl")
        include_string(Main,HELPER,"actual-shifted-primal-workspace.jl")
        include_string(Main,NEW,"actual-native-entry-coverage.jl")
        @test GLOBALS==(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
    end
catch exception
    metadata["exception"]=sprint(showerror,exception)
    rethrow()
finally
    metadata["globals_preserved"]=GLOBALS==(precision(BigFloat),rounding(BigFloat),rounding(Float64),get_zero_subnormals())
    open(OUT,"w") do io
        TOML.print(io,Dict("metadata"=>metadata))
    end
end
