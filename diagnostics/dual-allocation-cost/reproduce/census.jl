using JSimplex,LinearAlgebra,Logging,TOML,SHA,Statistics,Serialization
const JS=JSimplex
const LABELS=["dual_iteration","leaving_pricing","tableau_pricing","ratio_total","harris","bfrt_selection","flips_empty","flips_nonempty","weight_maintenance","validate_edge","native_correction","native_tableau","recompute","basis_update","row_residual","direction_residual","finite_workspace","dual_values","primal_values","point_certificate","ftran","btran","weight_ftran","flip_ftran","dse_update","small_pivot_guard_skipped","small_pivot_recovery","wide_dual_prices","wide_basis_solution","wide_price_recovery","wide_tableau","wide_pivot_recovery","wide_direction_recovery","observer"]
@eval JS begin
 mutable struct _DACStats
  calls::Matrix{Int};ns::Matrix{UInt64};bytes::Matrix{Int};allocs::Matrix{Int}
  exclusive_ns::Matrix{UInt64};exclusive_bytes::Matrix{Int};exclusive_allocs::Matrix{Int}
  child_ns::Vector{UInt64};child_bytes::Vector{Int};child_allocs::Vector{Int}
  depth::Int;phase::Int
 end
 const _dac=_DACStats(zeros(Int,34,6),zeros(UInt64,34,6),zeros(Int,34,6),zeros(Int,34,6),zeros(UInt64,34,6),zeros(Int,34,6),zeros(Int,34,6),zeros(UInt64,128),zeros(Int,128),zeros(Int,128),0,1)
 @inline function _dac_begin(id)
  s=_dac;s.depth+=1;d=s.depth
  s.child_ns[d]=0;s.child_bytes[d]=0;s.child_allocs[d]=0
  return (Base.gc_num(),time_ns(),d,s.phase)
 end
 @inline function _dac_end(id,token)
  g,t,d,p=token;s=_dac;elapsed=time_ns()-t
  diff=Base.GC_Diff(Base.gc_num(),g);n=Base.gc_alloc_count(diff);b=diff.allocd
  s.calls[id,p]+=1;s.ns[id,p]+=elapsed;s.bytes[id,p]+=b;s.allocs[id,p]+=n
  s.exclusive_ns[id,p]+=elapsed-s.child_ns[d]
  s.exclusive_bytes[id,p]+=b-s.child_bytes[d];s.exclusive_allocs[id,p]+=n-s.child_allocs[d]
  if d>1;s.child_ns[d-1]+=elapsed;s.child_bytes[d-1]+=b;s.child_allocs[d-1]+=n;end
  s.depth-=1;nothing
 end
 function _dac_reset()
  for x in (_dac.calls,_dac.ns,_dac.bytes,_dac.allocs,_dac.exclusive_ns,_dac.exclusive_bytes,_dac.exclusive_allocs)
   fill!(x,0)
  end
  @assert _dac.depth==0
  _dac.phase=1
 end
 Base.@noinline function _dac_empty()
  token=_dac_begin(1)
  try;nothing;finally;_dac_end(1,token);end
 end
end
function instrument(name,file,id)
 source=read(joinpath(dirname(pathof(JS)),file),String)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 body=ex.args[2];tag=gensym(:tag);token=gensym(:token)
 ex.args[2]=quote
  local $tag=$id
  local $token=_dac_begin($tag)
  try
   $body
  finally
   _dac_end($tag,$token)
  end
 end
 Core.eval(JS,ex)
end
for (name,file,id) in ((:_dual_iteration_unchecked!,"dual_simplex.jl",1),(:dual_edge_selection,"dual_simplex.jl",2),(:price!,"dual_simplex.jl",3),(:_configured_dual_ratio_test,"dual_ratio.jl",4),(:dual_ratio_test,"dual_simplex.jl",5),(:_bound_flipping_ratio_test,"dual_simplex.jl",6),(:_apply_bound_flips!,"dual_simplex.jl",:(isempty(flips) ? 7 : 8)),(:update_dual_pricing_weights!,"dual_simplex.jl",9),(:_validate_dual_edge!,"simplex_pricing.jl",10),(:_try_native_dual_correction!,"legacy_dual_correction.jl",11),(:_try_native_dual_tableau!,"legacy_dual_correction.jl",12),(:recompute!,"simplex.jl",13),(:_replace_pivot_column!,"simplex_pivot.jl",14),(:_dual_row_residual_ratio,"dual_simplex.jl",15),(:_dual_direction_residual_ok!,"dual_simplex.jl",16),(:_finite_workspace,"dual_simplex.jl",17),(:update_duals!,"dual_simplex.jl",18),(:update_primals!,"dual_simplex.jl",19),(:_legacy_primal_point_certified,"legacy_primal_point.jl",20),(:_pipeline_basis_solve!,"hypersparse_pipeline.jl",:(operation==:weight_ftran ? 23 : operation==:bfrt ? 24 : transposed ? 22 : 21)),(:update_dse!,"dual_simplex.jl",25),(:_stabilize_small_dual_pivot!,"dual_simplex.jl",:(abs(pivot)>10*_dual_pivot_cutoff(Float64) ? 26 : 27)),(:_refined_dual_prices,"dual_simplex.jl",28),(:_refined_basis_solution,"simplex_recovery.jl",29),(:_try_refine_dual_prices!,"dual_simplex.jl",30),(:_refined_tableau_row,"dual_simplex.jl",31),(:_try_refine_dual_pivot!,"dual_simplex.jl",32),(:_try_refine_dual_direction!,"dual_simplex.jl",33))
 instrument(name,file,id)
end
function calibration()
 for i in 1:100;JS._dac_empty();end
 a=[]
 for round in 1:7
  GC.gc();t=@timed for i in 1:10000;JS._dac_empty();end
  push!(a,Dict("seconds_per_call"=>t.time/10000,"bytes"=>t.bytes,"allocations"=>Base.gc_alloc_count(t.gcstats),"compile_seconds"=>t.compile_time))
 end
 a
end
function run_case(input,options,out;label="runtime",limit=1_000_000)
 problem=read_mps(input)
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX()
 cleanup=Ref(false);latest=Ref{Any}(nothing);integers=zeros(Int,4);steps=zeros(Float64,2)
 windows=NamedTuple[];sizehint!(windows,128);last=Ref((time_ns(),Base.gc_num()))
 function checkpoint(ws)
  for a in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
   SHA.update!(states,reinterpret(UInt8,a))
  end
 end
 observer_body=(event,ws)->begin
  if event==:phase_auxiliary;cleanup[]=false;JS._dac.phase=2
  elseif event==:phase_dual;JS._dac.phase=cleanup[] ? 4 : 3
  elseif event==:phase_cleanup;cleanup[]=true;JS._dac.phase=4
  elseif event==:phase_primal;JS._dac.phase=cleanup[] ? 4 : 5
  elseif event==:certification;JS._dac.phase=6
  end
  if event in (:pivot_completed,:flip_completed)
   integers[1]=ws.progress.iteration_offset;integers[2]=ws.iterations
   integers[3]=ws.scratch.selected_row;integers[4]=ws.scratch.selected_entering
   steps[1]=ws.scratch.last_primal_step;steps[2]=ws.scratch.last_dual_step
   SHA.update!(events,reinterpret(UInt8,integers));SHA.update!(events,reinterpret(UInt8,steps))
   ws.iterations%80==0 && checkpoint(ws)
   if ws.iterations in (1000,10000,30000) && label!="runtime-repeat"
    path=out*"-state-"*string(ws.progress.iteration_offset)*"-"*string(ws.iterations)*".bin"
    if !ispath(path)
     serialize(path,(problem=ws.problem,options=ws.options,basics=ws.basis.basic_indices,
      states=ws.basis.states,primal=ws.primal,weights=ws.pricing_weights,lower=ws.lower,
      upper=ws.upper,reduced=ws.reduced_costs,costs=ws.costs,row=ws.scratch.tableau_row,iteration=ws.iterations,offset=ws.progress.iteration_offset,phase=JS._dac.phase))
    end
   end
   if ws.iterations%1000==0
    now=time_ns();g=Base.gc_num();delta=Base.GC_Diff(g,last[][2])
    push!(windows,(iteration=ws.iterations,offset=ws.progress.iteration_offset,seconds=(now-last[][1])/1e9,bytes=delta.allocd,allocations=Base.gc_alloc_count(delta),gc_seconds=delta.total_time/1e9))
    last[]=(now,g)
   end
  end
  latest[]=ws;nothing
 end
 observer=(event,ws)->begin
  token=JS._dac_begin(34)
  try;observer_body(event,ws);finally;JS._dac_end(34,token);end
 end
 diagnostics=JS.SimplexDiagnostics(;observer,kernel_timing=false)
 warm=read_mps(joinpath(dirname(dirname(pathof(JS))),"test/fixtures/solver/afiro.mps"))
 with_logger(NullLogger()) do;JS._solve_diagnosed(warm,diagnostics;options,relax_integrality=true);end
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();empty!(windows);latest[]=nothing;cleanup[]=false
 diagnostics=JS.SimplexDiagnostics(;observer,kernel_timing=false)
 JS._dac_reset();GC.gc();last[]=(time_ns(),Base.gc_num())
 t=@timed with_logger(NullLogger()) do
  JS._solve_diagnosed(problem,diagnostics;options,relax_integrality=true)
 end
 r=t.value;isnothing(latest[]) || checkpoint(latest[])
 s=JS._dac
 stats=[Dict("kernel"=>LABELS[i],"phase"=>["setup","auxiliary","dual","cleanup","primal","certification"][p],"calls"=>s.calls[i,p],"seconds_inclusive"=>s.ns[i,p]/1e9,"seconds_exclusive"=>s.exclusive_ns[i,p]/1e9,"bytes_inclusive"=>s.bytes[i,p],"bytes_exclusive"=>s.exclusive_bytes[i,p],"allocations_inclusive"=>s.allocs[i,p],"allocations_exclusive"=>s.exclusive_allocs[i,p]) for i in 1:34,p in 1:6 if s.calls[i,p]>0]
 report=Dict("label"=>label,"status"=>string(r.status),"iterations"=>r.statistics.iterations,"refactorizations"=>r.statistics.refactorizations,"seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"allocations"=>Base.gc_alloc_count(t.gcstats),"bytes"=>t.bytes,"stats"=>stats,"windows"=>[Dict(string(k)=>v for (k,v) in pairs(w)) for w in windows],"events"=>Dict(string(k)=>v for (k,v) in diagnostics.counts if v!=0),"events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)),"input_sha256"=>bytes2hex(open(sha256,input)))
 if r.status==OPTIMAL
  report["objective"]=r.objective_value;report["original_feasible"]=JS._original_primal_feasible(problem,r.primal,options.primal_tolerance);@assert report["original_feasible"]
 end
 @assert r.status==(limit==1_000_000 ? OPTIMAL : ITERATION_LIMIT)
 open(out,"w") do io;TOML.print(io,report);end
 println("DONE ",label," ",r.status," ",t.time);flush(stdout)
end
function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 c=calibration();open(out*"-calibration.toml","w") do io;TOML.print(io,Dict("cases"=>c));end
 options=SolverOptions(algorithm=:dual,basis_update=:huangfu_hall,basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,iteration_limit=1_000_000,time_limit=Inf,verbose=false)
 run_case("/home/jspitz/mps/runtime.mps",options,out*"-runtime.toml")
 # Same instrumented methods are warmed for a second full trajectory.
 run_case("/home/jspitz/mps/runtime.mps",options,out*"-runtime-repeat.toml";label="runtime-repeat")
 medium_options=SolverOptions(algorithm=:dual,basis_update=:huangfu_hall,basis_refactorization=:native,refactorization_interval=320,pricing=:steepest_edge,simplex_strategy=:legacy,partial_pricing=false,iteration_limit=4000,time_limit=Inf,verbose=false)
 run_case("/home/jspitz/mps/medium.mps",medium_options,out*"-medium.toml";label="medium",limit=4000)
end
Base.invokelatest(main,only(ARGS))
