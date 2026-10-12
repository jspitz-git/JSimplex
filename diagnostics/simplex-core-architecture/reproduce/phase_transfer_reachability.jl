using JSimplex, Test, SparseArrays, LinearAlgebra, TOML, SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const FILE=joinpath(ROOT,"test/native_phase_transfer_tests.jl")
const SOURCE=read(FILE,String)
const TITLES=["Artificial exchanges certify native reconstruction before export","Reliable artificial exchanges need no reconstruction recovery"]
function extract(title)
 marker="@testset \""*title*"\" begin"
 marker*first(split(split(SOURCE,marker;limit=2)[2],"\n@testset";limit=2))
end
const HELPER="function artificial_exchange_roundoff_fixture"*first(split(split(SOURCE,"function artificial_exchange_roundoff_fixture";limit=2)[2],"\n@testset";limit=2))
const ORIGINAL=join(extract.(TITLES),"\n")
const ACTIVE=Ref{Any}(nothing)
const EVENTS=Dict[]
const RECORDS=Dict[]
fields(x)=Dict(string(k)=>repr(getfield(x,k)) for k in fieldnames(typeof(x)))
function bounds(v)
 Dict("finite"=>isfinite.(v),"values"=>[isfinite(b) ? Float64(JS.bound_value(b)) : 0.0 for b in v])
end
function snapshot(ws)
 ws isa JS.SimplexWorkspace || return Dict("workspace"=>false,"type"=>string(typeof(ws)))
 A=ws.problem.A
 Dict("workspace"=>true,"scalar"=>string(eltype(ws.primal)),"factor"=>string(typeof(ws.factorization)),
 "m"=>size(A,1),"n"=>size(A,2),"colptr"=>copy(A.colptr),"rowval"=>copy(A.rowval),"nzval"=>Float64.(A.nzval),
 "basis"=>copy(ws.basis.basic_indices),"states"=>string.(ws.basis.states),"primal"=>Float64.(ws.primal),
 "costs"=>Float64.(ws.costs),"rho"=>Float64.(ws.scratch.rho),"prices"=>Float64.(ws.reduced_costs),
 "lower"=>bounds(ws.lower),"upper"=>bounds(ws.upper),"iterations"=>ws.iterations,"refactorizations"=>ws.refactorizations,
 "solve_tolerance"=>Float64(ws.progress.numerical_policy.solve_tolerance),"primal_tolerance"=>Float64(ws.options.primal_tolerance))
end
function diagnostics_for_capture()
 JS.SimplexDiagnostics(;kernel_timing=true,observer=(event,ws)->begin
  context=ACTIVE[]
  if !isnothing(context)
   role=ws===context[1] ? "phase" : ws===context[2] ? "original" : "temporary"
   push!(EVENTS,Dict("event"=>string(event),"role"=>role,"state"=>snapshot(ws)))
  end
  nothing
 end)
end
function observed_remove!(phase,mapping,original,policy,stop)
 @assert isnothing(ACTIVE[])
 d=phase.progress.diagnostics
 rec=Dict("scalar"=>string(eltype(phase.primal)),"manager"=>string(phase.options.basis_update),"max_refinements"=>policy.max_refinements,
 "options"=>fields(phase.options),"policy"=>fields(policy),"original_options"=>fields(original.options),
 "mapping"=>Dict("original_to_phase"=>copy(mapping.original_to_phase),"phase_to_original"=>copy(mapping.phase_to_original),"artificial_columns"=>copy(mapping.artificial_columns)),
 "before_phase"=>snapshot(phase),"before_original"=>snapshot(original))
 start=length(EVENTS);work=copy(d.kernel_calls);counts=copy(d.counts);ACTIVE[]=(phase,original)
 try
  accepted=JS.remove_artificials!(phase,mapping,original,policy,stop)
  rec["accepted"]=accepted
  return accepted
 finally
  ACTIVE[]=nothing
  rec["after_phase"]=snapshot(phase);rec["after_original"]=snapshot(original)
  rec["events"]=copy(EVENTS[start+1:end])
  rec["kernels"]=Dict(string(k)=>v-get(work,k,0) for (k,v) in d.kernel_calls)
  rec["counts"]=Dict(string(k)=>v-get(counts,k,0) for (k,v) in d.counts)
  push!(RECORDS,rec)
 end
end
# Keep the two original oracle bodies; route their single production call through
# read-only capture and supply the passive recorder to the original fixture.
const EXECUTED=replace(ORIGINAL,
 "phase,mapping,original,policy=artificial_exchange_roundoff_fixture(T,manager)"=>
 "diagnostics=diagnostics_for_capture()\n        phase,mapping,original,policy=artificial_exchange_roundoff_fixture(T,manager;diagnostics)",
 "JSimplex.SimplexDiagnostics()"=>"diagnostics_for_capture()",
 "JSimplex.remove_artificials!"=>"observed_remove!")
const PRECISION=precision(BigFloat)
const ROUNDING=rounding(BigFloat)
const SUBNORMALS=get_zero_subnormals()
@assert !ispath(only(ARGS))
try
 Base.include_string(@__MODULE__,HELPER,FILE)
 @testset "S6-X original phase-transfer oracle" begin
  Base.include_string(@__MODULE__,EXECUTED,FILE)
 end
finally
 open(only(ARGS),"w") do io
  TOML.print(io,Dict("source"=>pathof(JS),"test_sha256"=>bytes2hex(sha256(SOURCE)),"helper"=>HELPER,"original_oracle"=>ORIGINAL,"executed_oracle"=>EXECUTED,
  "records"=>RECORDS,"julia_version"=>string(VERSION),"arch"=>string(Sys.ARCH),"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
  "globals_preserved"=>precision(BigFloat)==PRECISION && rounding(BigFloat)==ROUNDING && get_zero_subnormals()==SUBNORMALS))
 end
end
