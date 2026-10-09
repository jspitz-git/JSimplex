include("paired.jl")
source=read(joinpath(dirname(pathof(JS)),"legacy_primal_point.jl"),String)
ex,_=Meta.parse(source,first(findfirst("function _legacy_primal_point_certified(",source)))
ex.args[1].args[1]=:_movement_new_point_certified
Core.eval(JS,ex)
@eval JS begin
 const _movement_reference_mode=Ref(false)
 _legacy_primal_point_certified(ws) = _movement_reference_mode[] ?
  _pcw0_legacy_primal_point_certified(ws) : _movement_new_point_certified(ws)
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
 record
end
function cleanup_pair(out)
 records=[]
 for origin in ("primal","dual")
  for baseline in (true,false)
   d=deserialize("/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-"*origin*"-handoff.bin")
   r=run(d,baseline);r["origin"]=origin;push!(records,r)
   open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
   println(origin," baseline=",baseline," iterations=",r["iterations"]," seconds=",r["seconds"]);flush(stdout)
  end
  @assert records[end]["events_hash"]==records[end-1]["events_hash"]
  @assert records[end]["states_hash"]==records[end-1]["states_hash"]
 end
end
Base.invokelatest(cleanup_pair,only(ARGS))
