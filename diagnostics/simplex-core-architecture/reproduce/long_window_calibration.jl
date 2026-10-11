# Pilot: counter + chronological recorder cost. Medium/both-algorithm gate remains.
using JSimplex,Test,LinearAlgebra,SparseArrays,TOML,Statistics,SHA
const BASELINE_SOURCE=ARGS[2]
module CountedSource
 Base.include(@__MODULE__,Main.BASELINE_SOURCE*"/JSimplex.jl")
end
include("long_counters.jl")
install_long_counters!(CountedSource.JSimplex,BASELINE_SOURCE)
include("long_windows.jl")
install_long_event_sink!(CountedSource.JSimplex)
include("long_metadata.jl")
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
include("long_trace_check.jl")
function run_batch(bench,kind;batch=32)
 J=bench.JS
 counted=isdefined(J,:_lc_counts)
 counted && reset_long_recorder!(RECORDER)
 p=bench.fixture(kind)
 options=J.SolverOptions(;algorithm=:dual,basis_update=:huangfu_hall,
  basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
  simplex_strategy=:legacy,partial_pricing=false,iteration_limit=10000,verbose=false)
 workspaces=[J.initialize_workspace(p,options;progress=J.SimplexProgressContext(p;
  diagnostics=counted ? J.SimplexDiagnostics(;observer=RECORDER) : nothing)) for _ in 1:batch]
 for ws in workspaces
  @assert isnothing(J.make_dual_feasible!(ws,J._guard_stop_callback(()->false)))
 end
 start_iterations=sum(ws.iterations for ws in workspaces)
 context=J.SolveContext(time_ns(),Inf,nothing)
 stop=J._guard_stop_callback(()->J.time_limit_reached(context))
 GC.gc(true)
 if counted
  reset_long_recorder!(RECORDER)
  RECORDER.phase=:phase_two;RECORDER.algorithm=:dual
  RECORDER.rows,RECORDER.columns=size(p.A);RECORDER.nonzeros=nnz(p.A)
  RECORDER.section=3;RECORDER.base_section=3
 end
 timed=@timed for ws in workspaces
  terminal=J._dual_optimize!(ws,stop)
  terminal.status==J.OPTIMAL || error("Unexpected kernel termination")
 end
 counts=counted ? long_counter_rows(J) : Dict{String,Int64}()
 tail=counted ? finish!(RECORDER) : Dict{String,Int}()
 hashes=[bench.state_hash(ws) for ws in workspaces]
 @assert all(==(first(hashes)),hashes)
 for ws in workspaces
  @assert J._original_primal_feasible(p,ws.primal[1:size(p.A,2)],options.primal_tolerance)
 end
 return Dict("model"=>string(kind),"counted"=>counted,"batch"=>batch,
  "steps"=>sum(ws.iterations for ws in workspaces)-start_iterations,
  "state_hash"=>first(hashes),"seconds"=>timed.time,"compile_seconds"=>timed.compile_time,
  "bytes"=>timed.bytes,"allocations"=>Base.gc_alloc_count(timed.gcstats),
  "gc_seconds"=>timed.gctime,"counts"=>counts,"recorder_tail"=>tail)
end
function main(output)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 records=Dict[];gates=Dict[];traces=Dict[]
 for kind in (:sparse,:dense)
  # The actual recorder and trace run together, outside authoritative timings.
  a=verify_long_trace(PlainBench,kind)
  b=verify_long_trace(CountedBench,kind;recorder=RECORDER)
  push!(traces,Dict("model"=>string(kind),"plain"=>a,"counted"=>b))
  for key in ("entry_state_hash","state_hash","completion_states_hash","events_hash","event_counts","steps","refactorizations")
   @assert a[key]==b[key] key
  end
  run_batch(PlainBench,kind);run_batch(CountedBench,kind)
  samples=Dict[]
  for pair in 1:5
   for bench in (isodd(pair) ? (PlainBench,CountedBench) : (CountedBench,PlainBench))
    row=run_batch(bench,kind);row["pair"]=pair
    @assert row["compile_seconds"]==0
    @assert row["state_hash"]==a["state_hash"]
    @assert row["steps"]==row["batch"]*a["steps"]
    push!(records,row);push!(samples,row)
   end
  end
  plain=filter(r->!r["counted"],samples);counted=filter(r->r["counted"],samples)
  ratio=median(r["seconds"] for r in counted)/median(r["seconds"] for r in plain)
  gate=Dict("model"=>string(kind),"median_overhead"=>ratio-1,
    "chronology_pilot_pass"=>ratio<=1.05,"pairs"=>5,"batch"=>32,
    "same_allocations"=>all(a["bytes"]==b["bytes"] && a["allocations"]==b["allocations"] for (a,b) in zip(plain,counted)))
  push!(gates,gate);println(gate);flush(stdout)
 end
 open(output,"w") do io
  TOML.print(io,Dict("pilot_only"=>true,"source"=>BASELINE_SOURCE,
   "limitations"=>"Dual HH small kernels only; medium/both-algorithm calibration still required; final recorder flush excluded from kernel timing and reported separately. Trace covers observer callbacks. Separate fixed counters retain committed recovery reasons and discarded metadata totals; per-reason generic event history is omitted.",
   "gates"=>gates,"samples"=>records,"traces"=>traces))
 end
end
try
 Base.invokelatest(main,ARGS[1])
finally
 close(WINDOW_IO)
end
