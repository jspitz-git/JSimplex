# Diagnostic-only controlled restoration states, not natural perturbation frequency.
using JSimplex, SparseArrays, LinearAlgebra, Logging, SHA, TOML
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
const LABELS=("restore_original","restore_journal","invalidate_checkpoints","reset_auto_pricing",
 "original_cost_scans","original_bound_scans","recompute","ftran_requests","btran_requests","copy_calls","copy_elements")
Core.eval(JS,:(const _oc_counts=zeros(Int,11)))
Core.eval(JS,:(const _oc_records=Any[]))
scalar(x::BigFloat)=iszero(x) ? string(signbit(x) ? "-0" : "+0","@",precision(x)) : isfinite(x) ? string(Rational{BigInt}(x),"@",precision(x)) : string(x)
scalar(x)=string(x)
vals(x)=scalar.(x)
function state(w)
 j=w.scratch.perturbations;p=w.scratch.pricing
 Dict("costs"=>vals(w.costs),"lower"=>vals(w.lower),"upper"=>vals(w.upper),
 "primal"=>vals(w.primal),"prices"=>vals(w.reduced_costs),"weights"=>vals(w.pricing_weights),
 "basis"=>copy(w.basis.basic_indices),"states"=>string.(w.basis.states),
 "iterations"=>w.iterations,"refactorizations"=>w.refactorizations,"phase"=>Int(w.scratch.phase_generation),
 "checkpoints"=>length(w.scratch.checkpoints),"perturbed"=>w.perturbed,
 "journal_present"=>!isnothing(j),"journal_active"=>!isnothing(j) && j.active,
 "bounds_active"=>!isnothing(j) && JS._active_bounds(j.bounds),
 "active_costs_same"=>!isnothing(j) && w.costs===j.active_costs,
 "pricing_present"=>!isnothing(p),"pricing_mode"=>isnothing(p) ? "none" : string(p.active),
 "pricing_needs_reset"=>!isnothing(p) && p.needs_reset,
 "steepest_valid"=>copy(w.scratch.steepest_valid))
end
Core.eval(JS,:(const _oc_state=$state))
Core.eval(JS,quote
 function _oc_copy!(destination,args...)
   _oc_counts[10]+=1
   _oc_counts[11]+=length(args)==1 ? length(args[1]) : args[end]
   return copyto!(destination,args...)
 end
end)
function run_case(T,algorithm,backend,profile,mode,counted)
 p=mode==:bounds_alien ? LinearProblem(sparse(T[1;;]),T[1];row_lower=T[1],column_upper=T[2]) : LinearProblem(sparse(T[1;;]),T[1];column_upper=T[1])
 events=Any[];failure=SingularException(917);armed=Ref(false)
 observer=(reason,w)->begin
   armed[] || return nothing
   push!(events,Dict("reason"=>string(reason),"state"=>state(w)))
   mode==:observer_throw && reason==:restore_perturbations && throw(failure)
 end
 d=JS.SimplexDiagnostics(;observer)
 policy=JS.NumericalPolicy(T;numerical_profile=profile,simplex_strategy=:legacy)
 o=SolverOptions(T;algorithm,basis_update=:huangfu_hall,basis_refactorization=backend,
    verbose=false,scaling=:off,iteration_limit=50)
 w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
 j=nothing
 if mode in (:cost_owned,:cost_detached,:bounds_owned,:expired,:stop_restored,:observer_throw)
   j=JS.PerturbationJournal(w);w.scratch.perturbations=j
   if mode==:bounds_owned
     j.bounds=JS.BoundPerturbationState(w);j.bounds.active_lower[1]=JS.Bound(T(-1))
     w.lower=j.bounds.active_lower;w.upper=j.bounds.active_upper;j.bounds.active=true
   else
     j.active_costs[1]=-one(T);j.active=true;w.costs=j.active_costs;w.perturbed=true
     mode==:cost_detached && (w.costs=copy(w.costs))
   end
 elseif mode==:cost_unowned
   w.costs[1]=-one(T);w.perturbed=true
 elseif mode==:bounds_alien
   w.upper[1]=JS.Bound(zero(T))
 end
 JS.recompute!(w)
 # Exercise the already-owned pricing-state reset without enabling a heuristic.
 w.scratch.pricing=JS.PricingState(T);w.scratch.pricing.algorithm=algorithm
 w.scratch.pricing.needs_reset=true;w.scratch.pricing.framework_valid=false
 checkpoint=JS.checkpoint_basis(w)
 @assert JS._checkpoint_matches(w,checkpoint)
 other=JS.initialize_workspace(LinearProblem(copy(p.A),copy(p.objective);column_upper=T[1]),o)
 @assert !JS._checkpoint_matches(other,checkpoint)
 w.iterations=5;w.refactorizations=2
 budget=JS.SimplexRunBudget(w)
 mode==:expired && (budget.time_limit_seconds=0.0)
 stop=()->mode==:stop_restored && any(e->e["reason"]=="phase_cleanup",events)
 initial=state(w);original_input=(copy(p.objective),copy(p.column_lower),copy(p.column_upper))
 fill!(JS._oc_counts,0);empty!(JS._oc_records);armed[]=true
 result=nothing;caught=nothing
 try
   result=with_logger(NullLogger()) do;JS.run_from_basis!(w,budget,policy,stop);end
 catch e;caught=e;end
 armed[]=false
 counts=copy(JS._oc_counts);records=deepcopy(JS._oc_records)
 @assert isequal(original_input,(p.objective,p.column_lower,p.column_upper))
 row=Dict{String,Any}("key"=>join(string.((T,algorithm,backend,profile,mode)),"/"),
 "type"=>string(T),"algorithm"=>string(algorithm),"backend"=>string(backend),"profile"=>string(profile),
 "mode"=>string(mode),"initial"=>initial,"final"=>state(w),"events"=>events,
 "foreign_checkpoint_rejected"=>true,"checkpoint_still_matches"=>JS._checkpoint_matches(w,checkpoint),
 "budget_iterations"=>budget.iterations,"budget_refactorizations"=>budget.refactorizations,
 "input_unchanged"=>true)
 if caught!==nothing
   @assert mode==:observer_throw && caught isa JS.DiagnosticObserverFailure && caught.cause===failure
   row["exception_preserved"]=true
 else
   @assert mode!=:observer_throw
   row["status"]=string(result.status);row["objective"]=scalar(result.objective_value)
   row["primal"]=isnothing(result.primal) ? String[] : vals(result.primal)
   row["original_feasible"]=!isnothing(result.primal) && JS._original_primal_feasible(p,result.primal,o.primal_tolerance)
   if mode in (:expired,:stop_restored);@assert result.status==TIME_LIMIT
   elseif mode==:bounds_alien;@assert result.status==NUMERICAL_ERROR
   else
     @assert result.status==OPTIMAL && result.objective_value==zero(T) && result.primal==T[0]
     @assert row["original_feasible"] && JS._original_costs_active(w) && JS._original_bounds_active(w)
   end
 end
 if mode in (:cost_owned,:cost_detached,:cost_unowned,:bounds_owned,:stop_restored)
   @assert !row["checkpoint_still_matches"] && isnothing(w.scratch.perturbations)
 end
 @assert budget.iterations>=5 && budget.refactorizations>=2
 return row,counts,records
end
function parsed(file,prefix)
 src=read(joinpath(ROOT,"src",file),String);p=findall(prefix,src);@assert length(p)==1
 ex,_=Meta.parse(src,first(only(p)));@assert ex.head==:function;ex
end
function copies(ex)
 ex isa Expr || return ex
 ex.head==:call && ex.args[1]==:copyto! && return Expr(:call,:_oc_copy!,map(copies,ex.args[2:end])...)
 Expr(ex.head,map(copies,ex.args)...)
end
function install!()
 hooks=[("simplex.jl","function _restore_original_costs!",1),
 ("simplex_perturbation.jl","function restore_perturbations!",2),
 ("simplex_recovery.jl","function _invalidate_basis_checkpoints!",3),
 ("simplex_pricing.jl","function _reset_auto_pricing!",4),
 ("simplex_driver.jl","function _original_costs_active",5),
 ("simplex_driver.jl","function _original_bounds_active",6),
 ("simplex.jl","function recompute!(workspace::SimplexWorkspace{T};",7),
 ("simplex_recovery.jl","function _checked_basis_solve!",8),
 ("simplex_perturbation.jl","function _restore_working_bounds!",0)]
 for (file,prefix,index) in hooks
   ex=parsed(file,prefix);body=ex.args[2]
   index in (0,1,2) && (body=copies(body))
   probe=index==0 ? :(nothing) : index==8 ? :(_oc_counts[8+Int(transposed)]+=1) : :(_oc_counts[$index]+=1)
   if index==1
     ex.args[2]=quote
       before=_oc_state(workspace);counts_before=copy(_oc_counts);complete=false
       try;$probe;value=(() -> begin $body end)();complete=true;return value
       finally;push!(_oc_records,Dict("before"=>before,"after"=>_oc_state(workspace),
           "counts"=>_oc_counts-counts_before,"complete"=>complete));end
     end
   else;ex.args[2]=quote $probe;$body end;end
   Core.eval(JS,ex)
 end
end
function counted_cases(cases,controls)
 rows=Any[]
 for (case,control) in zip(cases,controls)
   row,counts,records=run_case(case...,true)
   @assert isequal(row,control) "pair mismatch $(row["key"])"
   push!(rows,Dict("control"=>row,"exact_recorded_pair"=>true,"counts"=>counts,"restorations"=>records))
 end
 rows
end
function main(out)
 @assert !ispath(out)
 modes=(:original,:cost_owned,:cost_detached,:cost_unowned,:bounds_owned,:bounds_alien,:expired,:stop_restored,:observer_throw)
 cases=[(T,a,b,p,m) for T in (Float64,Rational{BigInt}) for a in (:primal,:dual)
   for b in (:native,:markowitz) for p in (:native,:checked) for m in modes]
 controls=[first(run_case(c...,false)) for c in cases]
 println("CONTROLS_PASS ",length(controls));flush(stdout)
 install!();rows=Base.invokelatest(counted_cases,cases,controls)
 report=Dict("source"=>pathof(JS),"source_sha256"=>bytes2hex(sha256(read(pathof(JS)))),
 "script_sha256"=>bytes2hex(sha256(read(@__FILE__))),"labels"=>collect(LABELS),"cases"=>rows,
 "julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads(),"case_count"=>length(rows))
 open(out,"w") do io;TOML.print(io,report);end
 println("OBJECTIVE_RESTORE_CENSUS_PASS ",length(rows))
end
main(only(ARGS))
