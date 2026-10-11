# Full recorder + trace verification. Never call from an authoritative timer.
function verify_long_trace(bench,kind;recorder=nothing)
 J=bench.JS
 isnothing(recorder) || reset_long_recorder!(recorder)
 names=SHA.SHA2_256_CTX();states=SHA.SHA2_256_CTX()
 event_counts=Dict{String,Int}();capturing=Ref(false);completed=Ref(0)
 trace=(event,ws)->begin
  capturing[] || return nothing
  name=string(event);SHA.update!(names,codeunits(name*"\n"))
  event_counts[name]=get(event_counts,name,0)+1
  if event in (:pivot_completed,:flip_completed)
   completed[]+=1
   SHA.update!(states,reinterpret(UInt8,[ws.iterations,ws.scratch.selected_row,ws.scratch.selected_entering]))
   SHA.update!(states,reinterpret(UInt8,[ws.scratch.last_primal_step,ws.scratch.last_dual_step]))
   for a in (ws.basis.basic_indices,ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.pricing_weights)
    SHA.update!(states,reinterpret(UInt8,a))
   end
  end
  nothing
 end
 observer=isnothing(recorder) ? trace : LongTraceObserver(recorder,trace)
 diag=J.SimplexDiagnostics(;observer)
 p=bench.fixture(kind)
 options=J.SolverOptions(;algorithm=:dual,basis_update=:huangfu_hall,
  basis_refactorization=:native,refactorization_interval=160,pricing=:steepest_edge,
  simplex_strategy=:legacy,partial_pricing=false,iteration_limit=10000,verbose=false)
 ws=J.initialize_workspace(p,options;progress=J.SimplexProgressContext(p;diagnostics=diag))
 @assert isnothing(J.make_dual_feasible!(ws,J._guard_stop_callback(()->false)))
 before=ws.iterations;refactors=ws.refactorizations;entry_hash=bench.state_hash(ws)
 context=J.SolveContext(time_ns(),Inf,diag)
 stop=J._guard_stop_callback(()->J.time_limit_reached(context))
 if !isnothing(recorder)
  reset_long_recorder!(recorder);recorder.phase=:phase_two;recorder.algorithm=:dual;recorder.section=3;recorder.base_section=3
 end
 capturing[]=true
 result=J._dual_optimize!(ws,stop)
 capturing[]=false
 @assert result.status==J.OPTIMAL
 @assert J._original_primal_feasible(p,ws.primal[1:size(p.A,2)],options.primal_tolerance)
 if !isnothing(recorder)
  @assert recorder.accepted==completed[]
  @assert isempty(diag.events)
  finish!(recorder)
 end
 return Dict("entry_state_hash"=>entry_hash,"state_hash"=>bench.state_hash(ws),
  "completion_states_hash"=>bytes2hex(SHA.digest!(states)),"events_hash"=>bytes2hex(SHA.digest!(names)),
  "event_counts"=>event_counts,"steps"=>ws.iterations-before,"refactorizations"=>ws.refactorizations-refactors)
end
