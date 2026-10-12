using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const ROOT=dirname(dirname(pathof(JSimplex)))
const FILE=joinpath(ROOT,"test/native_phase_transfer_tests.jl")
const SOURCE=read(FILE,String)
const MODE=ARGS[1]
const OUT=ARGS[2]
const TITLE="Reliable artificial exchanges need no reconstruction recovery"
const NEIGHBOR="Artificial exchange recovery preserves cancellation and policy limits"
function extract(title)
 marker="@testset \""*title*"\" begin"
 marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2))
end
function helper(name)
 marker="function "*name
 occursin(marker,SOURCE) ? marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2)) : ""
end
const TARGET=extract(TITLE)
const NEWHELPER=helper("reliable_artificial_exchange_fixture")
const NATIVEHELPER=helper("artificial_exchange_roundoff_fixture")
const SELECTED=MODE=="red" ? "" : TARGET*(MODE=="green" ? "\n"*extract(NEIGHBOR) : "")
const GLOBALS=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
@assert !ispath(OUT)
try
 @testset "Reliable exchange structural contract" begin
  @test occursin("policy=reliable_artificial_exchange_fixture(Float32,manager;",TARGET)
  @test occursin("A=sparse(Matrix{T}(I,6,6))",NEWHELPER)
 end
 if MODE!="red"
  @assert MODE in ("green","master")
  Base.include_string(@__MODULE__,NEWHELPER*"\n"*NATIVEHELPER,FILE)
  Base.include_string(@__MODULE__,SELECTED,FILE)
  @testset "Ambient state preserved" begin
   @test GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
  end
 end
finally
 open(OUT,"w") do io
  TOML.print(io,Dict("source"=>pathof(JSimplex),"mode"=>MODE,"test_sha256"=>bytes2hex(sha256(SOURCE)),"target"=>TARGET,"new_helper"=>NEWHELPER,"native_helper"=>NATIVEHELPER,"selected"=>SELECTED,
  "julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())))
 end
end
