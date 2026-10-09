using JSimplex,LinearAlgebra,Logging,TOML,SHA
const JS=JSimplex
function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 options=SolverOptions(algorithm=:dual,basis_update=:huangfu_hall,basis_refactorization=:native,
  refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,
  partial_pricing=false,time_limit=Inf,iteration_limit=1_000_000,verbose=false)
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();latest=Ref{Any}(nothing)
 ints=zeros(Int,4);steps=zeros(Float64,2)
 function checkpoint(ws)
  for a in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
   SHA.update!(states,reinterpret(UInt8,a))
  end
 end
 observer=(event,ws)->begin
  if event in (:pivot_completed,:flip_completed)
   ints[1]=ws.progress.iteration_offset;ints[2]=ws.iterations;ints[3]=ws.scratch.selected_row;ints[4]=ws.scratch.selected_entering
   steps[1]=ws.scratch.last_primal_step;steps[2]=ws.scratch.last_dual_step
   SHA.update!(events,reinterpret(UInt8,ints));SHA.update!(events,reinterpret(UInt8,steps))
   ws.iterations%80==0 && checkpoint(ws)
  end
  latest[]=ws;nothing
 end
 warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
 with_logger(NullLogger()) do;JS._solve_diagnosed(warm,JS.SimplexDiagnostics(;observer);options,relax_integrality=true);end
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();latest[]=nothing
 input="/home/jspitz/mps/runtime.mps";problem=read_mps(input);d=JS.SimplexDiagnostics(;observer)
 GC.gc();t=@timed with_logger(NullLogger()) do;JS._solve_diagnosed(problem,d;options,relax_integrality=true);end
 r=t.value;checkpoint(latest[])
 report=Dict("status"=>string(r.status),"iterations"=>r.statistics.iterations,"refactorizations"=>r.statistics.refactorizations,
  "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),
  "events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),"objective"=>r.objective_value,
  "original_feasible"=>JS._original_primal_feasible(problem,r.primal,options.primal_tolerance),
  "events"=>Dict(string(k)=>v for (k,v) in d.counts),"source"=>pathof(JS),"input_sha256"=>bytes2hex(open(sha256,input)))
 open(out,"w") do io;TOML.print(io,report);end
 @assert r.status==OPTIMAL && report["original_feasible"]
 @assert report["events_hash"]=="6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb"
 @assert report["states_hash"]=="1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743"
 println(report)
end
Base.invokelatest(main,only(ARGS))
