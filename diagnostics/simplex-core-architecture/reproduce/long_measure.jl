# Live S0 reference. Run only through guarded_run.py after chronology calibration.
# Arguments: output.toml counted|plain dual|primal medium|sparse|dense iteration_limit
using JSimplex,LinearAlgebra,SparseArrays,TOML,SHA,Logging
const JS=JSimplex
const EXPECTED_SOURCE="/home/jspitz/.codex/worktrees/simplex-time-budget/JSimplex.jl/src"
realpath(dirname(pathof(JS)))==realpath(EXPECTED_SOURCE) || error("Wrong source baseline")
const OUTPUT=ARGS[1]
const MODE=Symbol(ARGS[2])
const ALGORITHM=Symbol(ARGS[3])
const KIND=Symbol(ARGS[4])
const STEP_LIMIT=parse(Int,ARGS[5])
MODE in (:plain,:counted) || error("Unknown measurement mode")
ALGORITHM in (:dual,:primal) || error("Unknown algorithm")
KIND in (:medium,:sparse,:dense) || error("Unknown input")
STEP_LIMIT>0 || error("Positive iteration limit required")
const MEDIUM_PATH="/home/jspitz/mps/medium.mps"
const MEDIUM_HASH="79c374a584b1463305cf4b0faee8920d0364df2dd5d0468a44ab58d9e9d49dc0"
include("long_counters.jl")
include("long_windows.jl")
include("long_metadata.jl")
module Bench
 const JS=Main.JSimplex
 include("entry_kernel_common.jl")
end
if MODE==:counted
 install_long_counters!(JS,dirname(pathof(JS)))
 install_long_event_sink!(JS)
 install_long_metadata!(JS,dirname(pathof(JS)))
end
const RECORDER=MODE==:counted ? LongRecorder(open(OUTPUT*".warm.windows.toml","w"),JS._lc_counts) : nothing
MODE==:counted && install_long_regions!(JS,dirname(pathof(JS)),RECORDER)
options_for(algorithm,steps)=JS.SolverOptions(;algorithm,basis_update=:huangfu_hall,
 basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
 simplex_strategy=:legacy,partial_pricing=false,iteration_limit=steps,
 time_limit=Inf,verbose=false)
fields(x)=Dict(string(k)=>string(getfield(x,k)) for k in fieldnames(typeof(x)))
save_report(data)=open(io->TOML.print(io,data),OUTPUT,"w")
function run_live(problem,options)
 diagnostics=MODE==:counted ? JS.SimplexDiagnostics(;observer=RECORDER) : nothing
 GC.gc(true)
 if MODE==:counted
  reset_long_recorder!(RECORDER)
  RECORDER.rows,RECORDER.columns=size(problem.A)
  RECORDER.nonzeros=nnz(problem.A)
 end
 tail=Dict{String,Int}()
 measured=@timed begin
  result=with_logger(NullLogger()) do
   JS._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
  end
  MODE==:counted && (tail=finish!(RECORDER))
  result
 end
 result=measured.value
 # Snapshot before the independent final audit invokes any instrumented helpers.
 counts=MODE==:counted ? long_counter_rows(JS) : Dict{String,Int64}()
 feasible=result.status==JS.OPTIMAL && !isnothing(result.primal) &&
  JS._original_primal_feasible(problem,result.primal,options.primal_tolerance)
 row=Dict("status"=>string(result.status),"message"=>result.message,
  "iterations"=>result.statistics.iterations,"refactorizations"=>result.statistics.refactorizations,
  "objective"=>string(result.objective_value),"original_primal_feasible"=>feasible,
  "primal_hash"=>isnothing(result.primal) ? "" : bytes2hex(sha256(reinterpret(UInt8,result.primal))),
  "seconds"=>measured.time,"compile_seconds"=>measured.compile_time,
  "bytes"=>measured.bytes,"allocations"=>Base.gc_alloc_count(measured.gcstats),
  "gc_seconds"=>measured.gctime,"recorder_tail"=>tail,
  "certificate_evidence"=>"OPTIMAL requires the solver's internal optimality certificate; the returned original primal is checked again outside timing",
  "counts"=>counts,
  "recorder_retained_bytes"=>MODE==:counted ? Base.summarysize(RECORDER) : 0)
 println("completed ",options.algorithm," ",row["status"]," iterations=",row["iterations"]," seconds=",row["seconds"]," compilation=",row["compile_seconds"]);flush(stdout)
 row
end
function main()
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 options=options_for(ALGORITHM,STEP_LIMIT)
 policy=JS.NumericalPolicy(Float64,options)
 @assert all(!getfield(policy,k) for k in fieldnames(typeof(policy)) if startswith(string(k),"adaptive_"))
 @assert !policy.incremental_primal && !policy.incremental_primal_pivots
 input_hash=KIND==:medium ? open(io->bytes2hex(sha256(io)),MEDIUM_PATH) : "owned-fixture-"*string(KIND)
 KIND==:medium && input_hash!=MEDIUM_HASH && error("Unexpected medium input digest")
 problem=KIND==:medium ? JS.read_mps(MEDIUM_PATH) : Bench.fixture(KIND)
 data=Dict{String,Any}("schema_version"=>1,"mode"=>string(MODE),"algorithm"=>string(ALGORITHM),
  "model"=>string(KIND),"input_sha256"=>input_hash,"source"=>dirname(pathof(JS)),
  "julia_version"=>string(VERSION),"blas_config"=>string(BLAS.get_config()),
  "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),
  "options"=>fields(options),"policy"=>fields(policy),"warmups"=>Dict[],
  "omitted_entry_probes"=>string.(collect(LONG_OMITTED_ENTRY_PROBES)),
  "counter_labels"=>LONG_COUNTER_LABELS,"section_labels"=>collect(string.(LONG_SECTIONS)),
  "dimension_semantics"=>"initialization/none uses input_model dimensions; subsequent windows use workspace dimensions; cleanup entry uses the original LP",
  "timing_semantics"=>"final window flush is inside timing; explicit final primal check and report serialization are outside; plain elapsed is authoritative",
  "phase_two_coverage"=>"requires post-exit audit of actual phase_two windows, not inferred from status",
  "solver_returned"=>false)
 save_report(data)
 # Warm fresh solves without retaining or reconstructing any solver workspace.
 # Both algorithms can execute during cleanup, regardless of the requested origin.
 for kind in (:sparse,:dense),algorithm in (:dual,:primal)
  row=run_live(Bench.fixture(kind),options_for(algorithm,10000))
  @assert row["status"]=="OPTIMAL" && row["original_primal_feasible"]
  row["model"]=string(kind);row["algorithm"]=string(algorithm)
  push!(data["warmups"],row);save_report(data)
 end
 if KIND==:medium
  row=run_live(problem,options_for(ALGORITHM,64))
  @assert row["status"] in ("OPTIMAL","ITERATION_LIMIT")
  row["model"]="medium-prefix";row["algorithm"]=string(ALGORITHM)
  push!(data["warmups"],row);save_report(data)
 end
 if MODE==:counted
  close(RECORDER.io)
  RECORDER.io=open(OUTPUT*".windows.toml","w")
 end
 println("starting fresh live reference ",MODE," ",ALGORITHM," ",KIND);flush(stdout)
 data["result"]=run_live(problem,options)
 data["solver_returned"]=true
 save_report(data)
end
try
 Base.invokelatest(main)
finally
 MODE==:counted && close(RECORDER.io)
end
