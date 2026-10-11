# Isolate remaining owned-observer cost after the sink fix; not a gate rerun.
using JSimplex,Test,LinearAlgebra,SparseArrays,TOML,Statistics,SHA
const JS=JSimplex
include("long_counters.jl")
include("long_windows.jl")
install_long_counters!(JS,dirname(pathof(JS)))
install_long_event_sink!(JS)
struct OwnedNoop <: AbstractLongObserver end
(::OwnedNoop)(event,ws)=nothing
const WINDOW_IO=open(ARGS[1]*".windows.toml","w")
const RECORDER=LongRecorder(WINDOW_IO,JS._lc_counts)
install_long_regions!(JS,dirname(pathof(JS)),RECORDER)
module Bench
 const JS=Main.JSimplex
 include("entry_kernel_common.jl")
end
make_diagnostics(::Val{:none})=nothing
make_diagnostics(::Val{:counts})=JS.SimplexDiagnostics()
make_diagnostics(::Val{:noop})=JS.SimplexDiagnostics(;observer=OwnedNoop())
make_diagnostics(::Val{:recorder})=JS.SimplexDiagnostics(;observer=RECORDER)
function run_batch(mode::Val{Mode};batch=64) where Mode
 reset_long_recorder!(RECORDER)
 p=Bench.fixture(:sparse)
 options=JS.SolverOptions(;algorithm=:dual,basis_update=:huangfu_hall,
  basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
  simplex_strategy=:legacy,partial_pricing=false,iteration_limit=10000,verbose=false)
 workspaces=[JS.initialize_workspace(p,options;progress=JS.SimplexProgressContext(p;
  diagnostics=make_diagnostics(mode))) for _ in 1:batch]
 for ws in workspaces
  @assert isnothing(JS.make_dual_feasible!(ws,JS._guard_stop_callback(()->false)))
 end
 start_iterations=sum(ws.iterations for ws in workspaces)
 context=JS.SolveContext(time_ns(),Inf,nothing)
 stop=JS._guard_stop_callback(()->JS.time_limit_reached(context))
 GC.gc(true);reset_long_recorder!(RECORDER)
 RECORDER.phase=:phase_two;RECORDER.algorithm=:dual
 RECORDER.rows,RECORDER.columns=size(p.A);RECORDER.nonzeros=nnz(p.A);RECORDER.section=3
 timed=@timed for ws in workspaces
  terminal=JS._dual_optimize!(ws,stop)
  terminal.status==JS.OPTIMAL || error("Unexpected termination")
 end
 counts=long_counter_rows(JS)
 @assert all(counts[string(name)]==0 for (name,section) in LONG_REGIONS)
 @assert RECORDER.windows==0 # no I/O or cold-region clocks inside this kernel
 @assert Mode==:recorder ? RECORDER.accepted==9batch : RECORDER.accepted==0
 tail=finish!(RECORDER)
 hashes=[Bench.state_hash(ws) for ws in workspaces]
 @assert all(==(first(hashes)),hashes)
 return Dict("mode"=>string(Mode),"batch"=>batch,"steps"=>sum(ws.iterations for ws in workspaces)-start_iterations,
  "state_hash"=>first(hashes),"seconds"=>timed.time,"compile_seconds"=>timed.compile_time,
  "bytes"=>timed.bytes,"allocations"=>Base.gc_alloc_count(timed.gcstats),
  "gc_seconds"=>timed.gctime,"counts"=>counts)
end
function main(output)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 modes=(Val(:none),Val(:counts),Val(:noop),Val(:recorder))
 for mode in modes;run_batch(mode);end
 rows=Dict[]
 for round in 1:5
  for index in circshift(collect(1:4),round-1)
   row=run_batch(modes[index]);row["round"]=round
   @assert row["compile_seconds"]==0
   push!(rows,row)
  end
 end
 for key in ("steps","state_hash","counts")
  @assert all(row[key]==rows[1][key] for row in rows) key
 end
 summaries=[Dict("mode"=>mode,"median_seconds"=>median(row["seconds"] for row in rows if row["mode"]==mode)) for mode in ("none","counts","noop","recorder")]
 for row in summaries;println(row);end
 open(output,"w") do io;TOML.print(io,Dict("samples"=>rows,"summaries"=>summaries,"source"=>dirname(pathof(JS))));end
end
try
 Base.invokelatest(main,ARGS[1])
finally
 close(WINDOW_IO)
end
