using JSimplex, Serialization, LinearAlgebra, SHA, Logging
const J=JSimplex
include("intervention.jl")
1<=length(ARGS)<=2 || error("Expected: snapshot [baseline|preserve_structural]")
install_intervention(length(ARGS)==2 ? ARGS[2] : "baseline")
function main(path)
 println("PROVENANCE snapshot=",abspath(path)," sha256=",bytes2hex(open(sha256,path))," source=",pathof(J)," julia=",VERSION)
 d=deserialize(path); ws=J.initialize_workspace(d.problem,d.options)
 ws.basis=deepcopy(d.basis); ws.costs.=d.costs; ws.lower.=d.lower; ws.upper.=d.upper; ws.primal.=d.primal
 ws.iterations=d.iteration
 before=point_certificate(ws);saved=copy(ws.primal)
 point=copy(ws.primal[ws.basis.basic_indices]);J.recompute!(ws;refactorize=true)
 restored=J._restore_legacy_primal_point!(ws,point,()->false)
 after=point_certificate(ws)
 println("RESTORE before=",before," after=",after," preserved=",restored," delta_inf=",norm(ws.primal-saved,Inf))
 point_certified(ws,after) || error("Uncertified restored point; no candidate inference")
 println("STATE objective=",dot(ws.costs,ws.primal)," dims=",size(ws.problem.A)," basic_artificials=",count(i->ws.costs[i]>0,ws.basis.basic_indices)," pinf=",J.primal_infeasibility(ws))
 candidates=Int[]
 for j in eachindex(ws.costs)
  s=ws.basis.states[j]; r=ws.reduced_costs[j]
  J._is_fixed(ws.lower[j],ws.upper[j]) && continue
  ((s==J.AT_LOWER && r<0)||(s==J.AT_UPPER && r>0)||(s==J.FREE_NONBASIC && r!=0)) && push!(candidates,j)
 end
 ws.scratch.steepest_initialized=true
 fill!(ws.scratch.steepest_valid,false)
 chosen=J._primal_entering(ws,0.0); println("SELECTED ",chosen); flush(stdout)
 sort!(candidates;by=j->-abs(ws.reduced_costs[j])/ws.pricing_weights[j])
 println("IMPROVING ",length(candidates)); flush(stdout)
 B=J._basis_matrix!(ws); buffers=J._pivot_quality_buffers(ws)
 for j in candidates[1:min(32,end)]
  rhs=copy(J._pipeline_column_rhs!(ws,j)); col=zeros(length(point)); J._ordinary_forward_solve!(col,ws.factorization,rhs)
  direction=sign(-ws.reduced_costs[j]); step,row,state=J._primal_ratio(ws,j,direction,col)
  implied=ws.costs[j]-dot(ws.costs[ws.basis.basic_indices],col)
  println("CAND j=",j," price=",ws.reduced_costs[j]," implied=",implied," weight=",ws.pricing_weights[j]," score=",abs(ws.reduced_costs[j])/ws.pricing_weights[j]," norm=",norm(col,Inf)," step=",step," row=",row," pivot=",row>0 ? col[row] : NaN," price_ok=",J._legacy_primal_direction_price_ok(ws,j,col,0.0))
  limits=Tuple{Float64,Int,Float64,Float64}[]
  for (k,i) in enumerate(ws.basis.basic_indices)
   mov=-direction*col[k]; iszero(mov) && continue
   b=mov>0 ? ws.upper[i] : ws.lower[i]; isfinite(b)||continue
   gap=J.bound_value(b)-ws.primal[i]; push!(limits,(max(0.,(gap+sign(mov)*ws.options.primal_tolerance)/mov),k,gap,col[k]))
  end
  sort!(limits)
  for (lim,k,gap,v) in limits[1:min(3,end)]
   i=ws.basis.basic_indices[k];mov=-direction*v
   raw=gap/mov
   worst=0.; worst_index=0
   for (r,n) in enumerate(ws.basis.basic_indices)
    r==k && continue
    value=ws.primal[n]-direction*col[r]*raw
    violation=max(0.,J._lower_violation(ws.lower[n],value),J._upper_violation(ws.upper[n],value))
    if violation>worst; worst=violation; worst_index=n; end
   end
   println("SNAP raw_step=",raw," max_other_basic_violation=",worst," worst_index=",worst_index)
   println("LIMIT relaxed=",lim," row=",k," index=",i," cost=",ws.costs[i]," value=",ws.primal[i]," gap=",gap," pivot=",v," fixed=",J._is_fixed(ws.lower[i],ws.upper[i])," snap_ok=",J._primal_bound_snap_feasible(ws,j,direction,col,k))
  end
  q=J._compensated_solve_quality!(buffers.column,B,col,rhs,ws.progress.numerical_policy,false)
  println("RESIDUAL_QUALITY ",q)
  if isnothing(q) || !q.finite
   println("REFINED unavailable");continue
  end
  J._ordinary_forward_solve!(buffers.correction,ws.factorization,buffers.column.residual)
  col .+= buffers.correction
  step2,row2,_=J._primal_ratio(ws,j,direction,col)
  println("REFINED step=",step2," row=",row2," implied=",ws.costs[j]-dot(ws.costs[ws.basis.basic_indices],col)," correction_norm=",norm(buffers.correction,Inf));flush(stdout)
 end
end
with_logger(NullLogger()) do
 main(ARGS[1])
end
