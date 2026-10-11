# Full-solve/prefix calibration: both algorithms, fresh live state, no restart.
using JSimplex,LinearAlgebra,SparseArrays,TOML,Statistics,SHA,Logging
const BASELINE_SOURCE=ARGS[2]
module CountedSource
 Base.include(@__MODULE__,Main.BASELINE_SOURCE*"/JSimplex.jl")
end
include("long_counters.jl")
include("long_windows.jl")
include("long_metadata.jl")
install_long_counters!(CountedSource.JSimplex,BASELINE_SOURCE)
install_long_event_sink!(CountedSource.JSimplex)
install_long_metadata!(CountedSource.JSimplex,BASELINE_SOURCE)
const WINDOW_IO=open(ARGS[1]*".windows.toml","w")
const RECORDER=LongRecorder(WINDOW_IO,CountedSource.JSimplex._lc_counts)
install_long_regions!(CountedSource.JSimplex,BASELINE_SOURCE,RECORDER)
module PlainBench
 const JS=Main.JSimplex
 include("entry_kernel_common.jl")
end
module CountedBench
 const JS=Main.CountedSource.JSimplex
 include("entry_kernel_common.jl")
end
options_for(J,algorithm,steps)=J.SolverOptions(;algorithm,basis_update=:huangfu_hall,
 basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
 simplex_strategy=:legacy,partial_pricing=false,iteration_limit=steps,
 time_limit=Inf,verbose=false)
function solve_case(bench,p,algorithm,steps;trace=false)
 J=bench.JS;counted=isdefined(J,:_lc_counts)
 options=options_for(J,algorithm,steps)
 names=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();events=Dict{String,Int}()
 latest=Ref{Any}(nothing)
 observer=(event,ws)->begin
  latest[]=ws
  name=string(event);SHA.update!(names,codeunits(name*"\n"))
  events[name]=get(events,name,0)+1
  if event in (:pivot_completed,:flip_completed)
   SHA.update!(states,reinterpret(UInt8,[ws.progress.iteration_offset,ws.iterations,ws.scratch.selected_row,ws.scratch.selected_entering]))
   SHA.update!(states,reinterpret(UInt8,[ws.scratch.last_primal_step,ws.scratch.last_dual_step]))
   for a in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
    SHA.update!(states,reinterpret(UInt8,a))
   end
  end
  nothing
 end
 diag=if trace
  J.SimplexDiagnostics(;observer=counted ? LongTraceObserver(RECORDER,observer) : observer)
 elseif counted
  J.SimplexDiagnostics(;observer=RECORDER)
 else
  nothing
 end
 GC.gc(true)
 counted && reset_long_recorder!(RECORDER)
 tail=Dict{String,Int}()
 timed=@timed begin
  result=with_logger(NullLogger()) do
   J._solve_diagnosed(p,diag;options,relax_integrality=true)
  end
  counted && (tail=finish!(RECORDER))
  result
 end
 result=timed.value
 counts=counted ? long_counter_rows(J) : Dict{String,Int64}()
 @assert result.status in (J.OPTIMAL,J.ITERATION_LIMIT)
 if result.status==J.OPTIMAL
  @assert J._original_primal_feasible(p,result.primal,options.primal_tolerance)
 end
 state=isnothing(latest[]) ? "" : bench.state_hash(latest[])
 latest[]=nothing # no retained workspace across cases
 row=Dict("algorithm"=>string(algorithm),"counted"=>counted,"trace"=>trace,
  "status"=>string(result.status),"iterations"=>result.statistics.iterations,
  "objective"=>string(result.objective_value),
  "primal_hash"=>isnothing(result.primal) ? "" : bytes2hex(sha256(reinterpret(UInt8,result.primal))),
  "seconds"=>timed.time,"compile_seconds"=>timed.compile_time,"bytes"=>timed.bytes,
  "allocations"=>Base.gc_alloc_count(timed.gcstats),"gc_seconds"=>timed.gctime,
  "events_hash"=>bytes2hex(SHA.digest!(names)),"states_hash"=>bytes2hex(SHA.digest!(states)),
  "last_callback_state"=>state,"events"=>events,"recorder_tail"=>tail,
  "recorder_retained_bytes"=>counted ? Base.summarysize(RECORDER) : 0,
  "counts"=>counts)
 println(algorithm," counted=",counted," trace=",trace," ",row["status"]," seconds=",row["seconds"]," compile=",row["compile_seconds"]);flush(stdout)
 row
end
function main(output,kind)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 # Each model belongs to its module; both are immutable inputs, not solver state.
 plain=kind==:medium ? PlainBench.JS.read_mps("/home/jspitz/mps/medium.mps") : PlainBench.fixture(kind)
 counted=kind==:medium ? CountedBench.JS.read_mps("/home/jspitz/mps/medium.mps") : CountedBench.fixture(kind)
 steps=kind==:medium ? 64 : 10000
 results=Dict("source"=>BASELINE_SOURCE,"model"=>string(kind),"prefix_limit"=>steps,"pairs"=>6,
  "omitted_entry_probes"=>string.(collect(LONG_OMITTED_ENTRY_PROBES)),
  "counter_labels"=>LONG_COUNTER_LABELS,"section_labels"=>collect(string.(LONG_SECTIONS)),
  "samples"=>Dict[],"traces"=>Dict[],"warmups"=>Dict[],"gates"=>Dict[],"options"=>Dict[],"policies"=>Dict[])
 save()=open(io->TOML.print(io,results),output,"w")
 for algorithm in (:dual,:primal)
  options=options_for(PlainBench.JS,algorithm,steps)
  policy=PlainBench.JS.NumericalPolicy(Float64,options)
  push!(results["options"],Dict(string(k)=>string(getfield(options,k)) for k in fieldnames(typeof(options))))
  push!(results["policies"],Dict(string(k)=>string(getfield(policy,k)) for k in fieldnames(typeof(policy))))
  a=solve_case(PlainBench,plain,algorithm,steps;trace=true)
  b=solve_case(CountedBench,counted,algorithm,steps;trace=true)
  for key in ("status","iterations","objective","primal_hash","events_hash","states_hash","last_callback_state","events")
   @assert a[key]==b[key] key
  end
  push!(results["traces"],Dict("plain"=>a,"counted"=>b));save()
  for (bench,p) in ((PlainBench,plain),(CountedBench,counted))
   push!(results["warmups"],solve_case(bench,p,algorithm,steps))
  end
  rows=Dict[]
  for pair in 1:6
   order=isodd(pair) ? ((PlainBench,plain),(CountedBench,counted)) : ((CountedBench,counted),(PlainBench,plain))
   for (bench,p) in order
    row=solve_case(bench,p,algorithm,steps);row["pair"]=pair
    @assert row["compile_seconds"]==0
    for key in ("status","iterations","objective","primal_hash");@assert row[key]==a[key] key;end
    push!(rows,row);push!(results["samples"],row);save()
   end
  end
  plain_rows=filter(x->!x["counted"],rows);counted_rows=filter(x->x["counted"],rows)
  overhead=median(x["seconds"] for x in counted_rows)/median(x["seconds"] for x in plain_rows)-1
  retention=length(unique(x["recorder_retained_bytes"] for x in counted_rows))==1
  gate=Dict("algorithm"=>string(algorithm),"median_overhead"=>overhead,
   "constant_recorder_retention"=>retention,"pass"=>overhead<=0.05 && retention)
  push!(results["gates"],gate);save();println(gate);flush(stdout)
 end
end
try
 kinds=split(ARGS[3],',')
 for kind in kinds
  output=length(kinds)==1 ? ARGS[1] : ARGS[1]*"-"*kind*".toml"
  Base.invokelatest(main,output,Symbol(kind))
 end
finally
 close(WINDOW_IO)
end
