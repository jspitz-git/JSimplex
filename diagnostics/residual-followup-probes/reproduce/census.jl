using JSimplex,LinearAlgebra,Logging,TOML,SHA
const JS=JSimplex

# Process-local timing wrappers preserve each original body. Nested time is
# subtracted to distinguish assembly, validation, quality work and correction.
@eval JS begin
 const _rprobe_calls=zeros(Int,6)
 const _rprobe_ns=zeros(UInt64,6)
 const _rprobe_exclusive=zeros(UInt64,6)
 const _rprobe_children=zeros(UInt64,32)
 const _rprobe_depth=Ref(0)
 @inline function _rprobe_begin()
  d=(_rprobe_depth[]+=1);_rprobe_children[d]=0
  (time_ns(),d)
 end
 @inline function _rprobe_end(id,token)
  t,d=token;elapsed=time_ns()-t
  _rprobe_calls[id]+=1;_rprobe_ns[id]+=elapsed
  _rprobe_exclusive[id]+=elapsed-_rprobe_children[d]
  d>1 && (_rprobe_children[d-1]+=elapsed)
  _rprobe_depth[]-=1
  nothing
 end
 function _rprobe_reset()
  @assert _rprobe_depth[]==0
  fill!(_rprobe_calls,0);fill!(_rprobe_ns,0);fill!(_rprobe_exclusive,0)
 end
end
function instrument(name,file,id)
 source=read(joinpath(dirname(pathof(JS)),file),String)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 body=ex.args[2];token=gensym(:token)
 ex.args[2]=quote
  local $token=_rprobe_begin()
  try
   $body
  finally
   _rprobe_end($id,$token)
  end
 end
 Core.eval(JS,ex)
end
for (name,file,id) in ((:_basis_matrix!,"simplex.jl",1),(:_validate_basis,"simplex.jl",2),(:_assemble_basis_matrix,"simplex.jl",3),(:_compensated_solve_quality!,"simplex_numerics.jl",:(transposed ? 5 : 4)),(:_try_native_dual_correction!,"legacy_dual_correction.jl",6))
 instrument(name,file,id)
end

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
 JS._rprobe_reset();GC.gc();t=@timed with_logger(NullLogger()) do;JS._solve_diagnosed(problem,d;options,relax_integrality=true);end
 r=t.value;checkpoint(latest[])
 report=Dict("status"=>string(r.status),"iterations"=>r.statistics.iterations,"refactorizations"=>r.statistics.refactorizations,
  "seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),
  "events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),"objective"=>r.objective_value,
  "original_feasible"=>JS._original_primal_feasible(problem,r.primal,options.primal_tolerance),
  "events"=>Dict(string(k)=>v for (k,v) in d.counts),"source"=>pathof(JS),"input_sha256"=>bytes2hex(open(sha256,input)))
 report["timing"]=[Dict("kernel"=>["basis_matrix","validate_basis","assemble_basis","quality_forward","quality_transpose","native_correction"][i],"calls"=>JS._rprobe_calls[i],"inclusive_seconds"=>JS._rprobe_ns[i]/1e9,"exclusive_seconds"=>JS._rprobe_exclusive[i]/1e9) for i in 1:6]
 open(out,"w") do io;TOML.print(io,report);end
 @assert r.status==OPTIMAL && report["original_feasible"]
 @assert report["events_hash"]=="6330422d394b22e155e2ecd58fb96fd3a89035a8d86ed6b07722c348bd59ccdb"
 @assert report["states_hash"]=="1af4c4c85c63a500a038b6101718f969d8a0ab11fb5a978ee2ba77e1621eb743"
 println(report)
end
Base.invokelatest(main,only(ARGS))
