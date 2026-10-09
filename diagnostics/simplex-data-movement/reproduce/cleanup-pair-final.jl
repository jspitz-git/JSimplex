using JSimplex,Serialization,TOML,SHA,Logging,LinearAlgebra,Statistics
const JS=JSimplex
# Define the frozen reference and the current function under separate names.
source=read(joinpath(@__DIR__,"point-baseline.txt"),String)
for name in (:_legacy_primal_row_consistent,:_legacy_primal_point_certified)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 function rename(x)
  x isa Symbol && return x in (:_legacy_primal_row_consistent,:_legacy_primal_point_certified) ? Symbol(:_movement_baseline_,x) : x
  x isa Expr && return Expr(x.head,map(rename,x.args)...)
  x
 end
 Core.eval(JS,rename(ex))
end
source=read(joinpath(dirname(pathof(JS)),"legacy_primal_point.jl"),String)
ex,_=Meta.parse(source,first(findfirst("function _legacy_primal_point_certified(",source)))
ex.args[1].args[1]=:_movement_new_point_certified
Core.eval(JS,ex)
@eval JS begin
 const _movement_reference_mode=Ref(false)
 _legacy_primal_point_certified(ws) = _movement_reference_mode[] ?
  _movement_baseline__legacy_primal_point_certified(ws) : _movement_new_point_certified(ws)
end
function run(d,baseline)
 JS._movement_reference_mode[]=baseline
 options=JS._remaining_options(d.options;iterations=d.options.iteration_limit-(d.iterations+128),time_limit=Inf)
 events=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX();latest=Ref{Any}(nothing)
 observer=(event,w)->begin
  if event in (:pivot_completed,:flip_completed)
   SHA.update!(events,reinterpret(UInt8,[w.iterations,w.scratch.selected_row,w.scratch.selected_entering]))
   for a in (w.basis.basic_indices,w.primal,w.reduced_costs,w.pricing_weights)
    SHA.update!(states,reinterpret(UInt8,a))
   end
  end
  latest[]=w;nothing
 end
 diag=JS.SimplexDiagnostics(;observer,kernel_timing=true)
 ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
 t=@timed with_logger(NullLogger()) do
  JS.cleanup_original(d.problem,d.basis,options,ctx,d.iterations,d.refactorizations;target_primal=d.target_primal)
 end
 r=t.value;@assert r.status==ITERATION_LIMIT
 record=Dict("baseline"=>baseline,"status"=>string(r.status),"iterations"=>r.iterations,"seconds"=>t.time,"compile_seconds"=>t.compile_time,"gc_seconds"=>t.gctime,"bytes"=>t.bytes,"events_hash"=>bytes2hex(SHA.digest!(events)),"states_hash"=>bytes2hex(SHA.digest!(states)))
 # Repeated kernel measurements on an actual late workspace, after its solve.
 w=latest[];old=JS._movement_baseline__legacy_primal_point_certified;new=JS._movement_new_point_certified
 old(w);new(w);a=[];b=[];aa=[];bb=[]
 for round in 1:9
  for k in (isodd(round) ? (1,2) : (2,1))
   f=k==1 ? old : new;GC.gc()
   v=@timed for i in 1:3;Base.donotdelete(f(w));end
   @assert v.compile_time==0
   push!(k==1 ? a : b,v.time/3);push!(k==1 ? aa : bb,v.bytes/3)
  end
 end
 @assert old(w)==new(w)
 record["certificate"]=Dict("verdict"=>new(w),"old_seconds"=>a,"new_seconds"=>b,"old_bytes"=>aa,"new_bytes"=>bb,"rows"=>size(w.problem.A,1),"columns"=>size(w.problem.A,2))
 record
end
function main(out,reference_file)
 records=[]
 references=TOML.parsefile(reference_file)["cases"]
 for origin in ("primal","dual")
  d=deserialize("/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-"*origin*"-handoff.bin")
  reference=copy(only(filter(r->r["origin"]==origin && r["baseline"],references)))
  reference["reused_from"]=reference_file
  push!(records,reference)
  for baseline in (false,)
   r=run(d,baseline);r["origin"]=origin;push!(records,r)
   open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
   println(origin," baseline=",baseline," seconds=",r["seconds"]);flush(stdout)
  end
  @assert records[end]["events_hash"]==records[end-1]["events_hash"]
  @assert records[end]["states_hash"]==records[end-1]["states_hash"]
 end
end
Base.invokelatest(main,ARGS...)
