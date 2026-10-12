using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/native_phase_transfer_tests.jl")
const SOURCE=read(FILE,String)
const HELPER="function artificial_exchange_roundoff_fixture"*first(split(split(SOURCE,"function artificial_exchange_roundoff_fixture";limit=2)[2],"\n@testset";limit=2))
const OLD_MATRIX="A=sparse(T[8 -2 0 1 -3 2; 2 6 1 2 -2 -2; 1 -2 3 0 -1 3;\n               3 -1 0 5 -2 -2; 0 0 -1 0 6 -3; 0 0 -1 -2 -1 8])"
@assert occursin(OLD_MATRIX,HELPER)
const QUALIFIED_HELPER=replace(HELPER,"artificial_exchange_roundoff_fixture"=>"reliable_exchange_fixture",OLD_MATRIX=>"A=sparse(Matrix{T}(I,6,6))")
const MARKER="@testset \"Reliable artificial exchanges need no reconstruction recovery\" begin"
const ORIGINAL=MARKER*first(split(split(SOURCE,MARKER;limit=2)[2],"\n@testset";limit=2))
const RECORDS=Dict[]
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
function state(ws)
 Dict("basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"primal"=>Float64.(ws.primal),"iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
 "colptr"=>copy(ws.problem.A.colptr),"rowval"=>copy(ws.problem.A.rowval),"nzval"=>Float64.(ws.problem.A.nzval),"costs"=>Float64.(ws.costs),"factor"=>string(typeof(ws.factorization)))
end
function observed_remove!(phase,map,original,policy,stop)
 d=phase.progress.diagnostics;work=copy(d.kernel_calls);counts=copy(d.counts)
 r=Dict("manager"=>string(phase.options.basis_update),"options"=>fields(phase.options),"policy"=>fields(policy),"before_phase"=>state(phase),"before_original"=>state(original),"original_to_phase"=>copy(map.original_to_phase),"phase_to_original"=>copy(map.phase_to_original),"artificials"=>copy(map.artificial_columns))
 accepted=false
 try
  accepted=JS.remove_artificials!(phase,map,original,policy,stop)
  r["accepted"]=accepted
 finally
  r["after_phase"]=state(phase);r["after_original"]=state(original)
  r["kernels"]=Dict(string(k)=>v-get(work,k,0) for (k,v) in d.kernel_calls)
  r["counts"]=Dict(string(k)=>v-get(counts,k,0) for (k,v) in d.counts)
  push!(RECORDS,r)
 end
 @test original.basis.basic_indices==collect(1:6)
 @test original.primal[1:6]==Float32[1,1,0,0,0,0]
 feasible=JS._original_primal_feasible(original,original.primal[1:6])
 r["post_original_certificate"]=feasible
 @test feasible
 return accepted
end
const EXECUTED=replace(ORIGINAL,"artificial_exchange_roundoff_fixture"=>"reliable_exchange_fixture","JSimplex.SimplexDiagnostics()"=>"JSimplex.SimplexDiagnostics(;kernel_timing=true)","JSimplex.remove_artificials!"=>"observed_remove!")
const GLOBALS=(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
@assert !ispath(only(ARGS))
try
 Base.include_string(@__MODULE__,QUALIFIED_HELPER,FILE)
 @testset "S6-Z reliable exact exchange qualification" begin
  Base.include_string(@__MODULE__,EXECUTED,FILE)
  @test GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())
 end
finally
 open(only(ARGS),"w") do io
  TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),"helper"=>HELPER,"qualified_helper"=>QUALIFIED_HELPER,"original_oracle"=>ORIGINAL,"executed_oracle"=>EXECUTED,
   "records"=>RECORDS,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"globals_preserved"=>GLOBALS==(precision(BigFloat),rounding(BigFloat),get_zero_subnormals())))
 end
end
