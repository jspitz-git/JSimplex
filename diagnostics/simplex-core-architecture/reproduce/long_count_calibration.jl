# Pilot: count-only lower bound before adding chronology. Not a long-run gate.
using JSimplex,Test,LinearAlgebra,SparseArrays,TOML,Statistics,SHA
const BASELINE_SOURCE=ARGS[2]
module CountedSource
 Base.include(@__MODULE__,Main.BASELINE_SOURCE*"/JSimplex.jl")
end
include("long_counters.jl")
install_long_counters!(CountedSource.JSimplex,BASELINE_SOURCE)
module PlainBench
 const JS=Main.JSimplex
 include("entry_kernel_common.jl")
end
module CountedBench
 const JS=Main.CountedSource.JSimplex
 include("entry_kernel_common.jl")
end
function run_batch(bench,kind;batch=32)
 J=bench.JS
 p=bench.fixture(kind)
 options=J.SolverOptions(;algorithm=:dual,basis_update=:huangfu_hall,
  basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
  simplex_strategy=:legacy,partial_pricing=false,iteration_limit=10000,verbose=false)
 workspaces=[J.initialize_workspace(p,options) for _ in 1:batch]
 for ws in workspaces
  @assert isnothing(J.make_dual_feasible!(ws,J._guard_stop_callback(()->false)))
 end
 start_iterations=sum(ws.iterations for ws in workspaces)
 context=J.SolveContext(time_ns(),Inf,nothing)
 stop=J._guard_stop_callback(()->J.time_limit_reached(context))
 counted=isdefined(J,:_lc_counts)
 counted && reset_long_counters!(J)
 GC.gc(true)
 timed=@timed for ws in workspaces
  terminal=J._dual_optimize!(ws,stop)
  terminal.status==J.OPTIMAL || error("Unexpected kernel termination")
 end
 counts=counted ? long_counter_rows(J) : Dict{String,Int64}()
 hashes=[bench.state_hash(ws) for ws in workspaces]
 @assert all(==(first(hashes)),hashes)
 for ws in workspaces
  @assert J._original_primal_feasible(p,ws.primal[1:size(p.A,2)],options.primal_tolerance)
 end
 return Dict("model"=>string(kind),"counted"=>counted,"batch"=>batch,
  "steps"=>sum(ws.iterations for ws in workspaces)-start_iterations,
  "state_hash"=>first(hashes),"seconds"=>timed.time,"compile_seconds"=>timed.compile_time,
  "bytes"=>timed.bytes,"allocations"=>Base.gc_alloc_count(timed.gcstats),
  "gc_seconds"=>timed.gctime,"counts"=>counts)
end
function main(output)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 records=Dict[];gates=Dict[]
 for kind in (:sparse,:dense)
  # Event/state cross-check is separate from authoritative count-only timings.
  a=PlainBench.run_kernel(PlainBench.fixture(kind),:huangfu_hall;trace=true)
  b=CountedBench.run_kernel(CountedBench.fixture(kind),:huangfu_hall;trace=true)
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
    "count_only_pilot_pass"=>ratio<=1.05,"pairs"=>5,"batch"=>32,
    "same_allocations"=>all(a["bytes"]==b["bytes"] && a["allocations"]==b["allocations"] for (a,b) in zip(plain,counted)))
  push!(gates,gate);println(gate);flush(stdout)
 end
 open(output,"w") do io
  TOML.print(io,Dict("pilot_only"=>true,"source"=>BASELINE_SOURCE,
   "limitations"=>"Dual HH small kernels only; full chronology and medium/both-algorithm calibration still required.",
   "gates"=>gates,"samples"=>records))
 end
end
Base.invokelatest(main,ARGS[1])
