using JSimplex, Serialization, TOML, Logging, LinearAlgebra
const JS=JSimplex
# Process-local timing wrappers preserve each original body. Nested time is
# subtracted to distinguish assembly, validation, quality work and correction.
@eval JS begin
 const _rprobe_calls=zeros(Int,7)
 const _rprobe_ns=zeros(UInt64,7)
 const _rprobe_exclusive=zeros(UInt64,7)
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

for (name,file,id) in ((:_legacy_primal_point_certified,"legacy_primal_point.jl",1),(:_primal_row_bounds!,"dual_simplex.jl",2),(:_legacy_primal_model_feasible,"legacy_primal_point.jl",3),(:_legacy_primal_row_consistent,"legacy_primal_point.jl",4),(:_native_primal_rows_filter,"primal_row_certification.jl",5),(:_exact_primal_rows_feasible,"primal_row_certification.jl",6),(:_primal_feasible_with_bounds,"dual_simplex.jl",7))
 instrument(name,file,id)
end

function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 reports=[]
 for origin in ("primal","dual")
  d=deserialize("/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-"*origin*"-handoff.bin")
  options=JS._remaining_options(d.options;iterations=d.options.iteration_limit-(d.iterations+32),time_limit=Inf)
  latest=Ref{Any}(nothing)
  observer=(event,w)->(latest[]=w;nothing)
  diag=JS.SimplexDiagnostics(;observer)
  ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
  JS._rprobe_reset();GC.gc()
  t=@timed with_logger(NullLogger()) do
   JS.cleanup_original(d.problem,d.basis,options,ctx,d.iterations,d.refactorizations;target_primal=d.target_primal)
  end
  @assert t.value.status==ITERATION_LIMIT
  continuation=Dict("seconds"=>t.time,"compile_seconds"=>t.compile_time,"iterations"=>t.value.iterations,"status"=>string(t.value.status))
  # Warm the final actual workspace, then isolate repeated certification.
  w=latest[];verdict=JS._legacy_primal_point_certified(w)
  JS._rprobe_reset();GC.gc()
  sample=@timed for i in 1:10
   @assert JS._legacy_primal_point_certified(w)==verdict
  end
  @assert sample.compile_time==0
  r=Dict("origin"=>origin,"continuation"=>continuation,"verdict"=>verdict,"certificate_seconds_per_call"=>sample.time/10,"certificate_bytes_per_call"=>sample.bytes/10,"timing"=>[Dict("kernel"=>["point_certificate","row_bounds","model_feasible","row_consistent","native_filter","exact_rows","feasible_with_bounds"][i],"calls"=>JS._rprobe_calls[i],"inclusive_seconds"=>JS._rprobe_ns[i]/1e9,"exclusive_seconds"=>JS._rprobe_exclusive[i]/1e9) for i in 1:7])
  push!(reports,r);open(out,"w") do io;TOML.print(io,Dict("cases"=>reports));end
  println(origin," ",r);flush(stdout)
 end
end
Base.invokelatest(main,only(ARGS))
