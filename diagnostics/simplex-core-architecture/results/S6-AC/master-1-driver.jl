using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)));const FILE=joinpath(ROOT,"test/native_phase_transfer_tests.jl")
const SOURCE=read(FILE,String);const MODE=ARGS[1];const OUT=ARGS[2]
const TITLE="Artificial exchanges certify native reconstruction before export"
extract(title)=begin
 marker="@testset \""*title*"\" begin"
 marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2))
end
const TARGET=extract(TITLE)
const PREFIX=first(split(SOURCE,"\n@testset";limit=2))
const NATIVE="function artificial_exchange_roundoff_fixture"*first(split(split(SOURCE,"function artificial_exchange_roundoff_fixture";limit=2)[2],"\n@testset";limit=2))
const SELECTED=MODE=="red" ? "" : TARGET*(MODE=="green" ? "\n"*extract("Artificial exchange recovery preserves cancellation and policy limits")*"\n"*extract("Reliable artificial exchanges need no reconstruction recovery") : "")
const GLOBALS=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
const FAILURE=ErrorException("S6-AC forwarded operation sentinel")
struct ThrowingPhaseInner end
JS._ordinary_forward_solve!(d,::ThrowingPhaseInner,r)=throw(FAILURE)
JS.forward_solve!(d,::ThrowingPhaseInner,r)=throw(FAILURE)
JS.transpose_solve!(d,::ThrowingPhaseInner,r)=throw(FAILURE)
JS.replace_column!(::ThrowingPhaseInner,d,row;kwargs...)=throw(FAILURE)
JS.refactorize!(::ThrowingPhaseInner,B)=throw(FAILURE)
JS._invalidate_prepared_destination!(::ThrowingPhaseInner,d)=throw(FAILURE)
function accounting_microtests()
 @testset "Pre-forward attempt accounting" begin
  for kind in (:ordinary,:prepared,:transpose,:update,:refactor,:invalidate)
   f=PhaseReconstructionFactor(ThrowingPhaseInner(),Float64)
   d=zeros(6);rhs=f.unit_rhs
   kind==:refactor && (f.updated=true)
   caught=try
    kind==:ordinary ? JS._ordinary_forward_solve!(d,f,rhs) :
    kind==:prepared ? JS.forward_solve!(d,f,rhs) :
    kind==:transpose ? JS.transpose_solve!(d,f,rhs) :
    kind==:update ? JS.replace_column!(f,rhs,6;zero_tolerance=0.0) :
    kind==:refactor ? JS.refactorize!(f,Matrix{Float64}(I,6,6)) :
    JS._invalidate_prepared_destination!(f,d)
    nothing
   catch e
    e
   end
   @test caught===FAILURE
   field=kind in (:ordinary,:prepared) ? :ftran_calls : kind==:transpose ? :btran_calls : kind==:update ? :update_calls : kind==:refactor ? :refactor_calls : :invalidations
   @test getfield(f,field)==1
   @test !f.armed && f.hits==0
  end
  f=PhaseReconstructionFactor(ThrowingPhaseInner(),Float64)
  @test_throws ErrorException JS.copy_basis_factorization(f)
  @test f.ftran_calls==f.btran_calls==f.update_calls==f.refactor_calls==0
 end
end
@assert !ispath(OUT)
try
 @testset "Phase reconstruction structural contract" begin
  @test occursin("phase_reconstruction_fixture(T,manager;diagnostics)",TARGET)
  @test occursin("factor.invalidations==5",TARGET) && occursin("diagnostics.kernel_calls[:ftran]-ftran_before==6",TARGET)
 end
 if MODE!="red"
  @assert MODE in ("green","master")
  Base.include_string(@__MODULE__,PREFIX*"\n"*NATIVE,FILE)
  Base.include_string(@__MODULE__,SELECTED,FILE)
  Base.invokelatest(accounting_microtests)
  @testset "Ambient state preserved" begin
   @test GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
  end
 end
finally
 open(OUT,"w") do io
  TOML.print(io,Dict("source"=>pathof(JS),"mode"=>MODE,"test_sha256"=>bytes2hex(sha256(SOURCE)),"target"=>TARGET,"prefix"=>PREFIX,"native_helper"=>NATIVE,"selected"=>SELECTED,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())))
 end
end
