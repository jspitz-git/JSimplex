function commit_case(n=3;interval=80,iteration_limit=1000,time_limit=Inf)
    A=sparse(Matrix{Float64}(I,n,n));p=J.LinearProblem(A,ones(n);row_lower=ones(n),row_upper=ones(n),column_lower=zeros(n))
    options=J.SolverOptions(Float64;pricing=:devex,verbose=false,refactorization_interval=interval,iteration_limit=iteration_limit,time_limit=time_limit)
    progress=J.SimplexProgressContext(p;start_ns=time_ns(),iteration_offset=7,refactorization_offset=11)
    ws=J.initialize_workspace(p,options;progress)
    clock=J._SolveDeadline(progress.start_ns,time_limit)
    (e=E.import_phase(ws,clock,E.EnginePolicy(ws)),source=ws)
end
function committed_snapshot(e)
    w=e.ws
    (primal=copy(w.primal),prices=copy(w.reduced_costs),costs=copy(w.costs),weights=copy(w.pricing_weights),reference=copy(w.devex_reference),basis=copy(w.basis.basic_indices),states=copy(w.basis.states),lower=copy(w.lower),upper=copy(w.upper),iterations=w.iterations,refactors=w.refactorizations,perturbed=w.perturbed,start=w.progress.start_ns,offsets=(w.progress.iteration_offset,w.progress.refactorization_offset))
end
function membership_matches(e)
    p,d=independent_members(e.ws)
    members(e.invariants.primal_bad)==p && members(e.invariants.dual_bad)==d
end
mutable struct ControlledClock
    expired::Base.RefValue{Bool}
end
(c::ControlledClock)()=c.expired[]
mutable struct CommitFaultFactor{F}
    inner::F
    mode::Symbol
    flag::Base.RefValue{Bool}
    forward_calls::Int
    transpose_calls::Int
    update_calls::Int
    refactor_calls::Int
    sentinel::ErrorException
end
CommitFaultFactor(f,mode;flag=Ref(false))=CommitFaultFactor(f,mode,flag,0,0,0,0,ErrorException("factor sentinel"))
function Base.getproperty(f::CommitFaultFactor,k::Symbol)
    k in fieldnames(typeof(f)) ? getfield(f,k) : getproperty(getfield(f,:inner),k)
end
function J.forward_solve!(out,f::CommitFaultFactor,rhs)
    f.forward_calls+=1;J.forward_solve!(out,f.inner,rhs)
    if f.mode==:direction_once;out[1]+=2.0^-20;f.mode=:native;end
    out
end
function J.transpose_solve!(out,f::CommitFaultFactor,rhs)
    f.transpose_calls+=1;J.transpose_solve!(out,f.inner,rhs)
    if f.mode in (:row_once,:row_always)
        out[1]+=2.0^-20;f.mode==:row_once&&(f.mode=:native)
    end
    out
end
function J.replace_column!(f::CommitFaultFactor,d,row;kwargs...)
    f.update_calls+=1;J.replace_column!(f.inner,d,row;kwargs...)
    f.mode==:factor_fail&&throw(SingularException(31))
    f.mode==:foreign_fail&&throw(f.sentinel)
    f.mode==:deadline&&(f.flag[]=true)
    f
end
function J.refactorize!(f::CommitFaultFactor,B)
    f.refactor_calls+=1;J.refactorize!(f.inner,B)
    f.mode==:refactor_fail&&throw(SingularException(32))
    f.mode==:factor_fail&&(f.mode=:native)
    f
end
function replace_engine_factor(e,f;clock=e.clock)
    old=e.ws;ws=J.SimplexWorkspace((k==:factorization ? f : getfield(old,k) for k in fieldnames(typeof(old)))...)
    ks=E.KernelState(e.owner,length(old.basis.basic_indices),e.supports,f)
    E.EngineState((k==:ws ? ws : k==:kernels ? ks : k==:clock ? clock : getfield(e,k) for k in fieldnames(typeof(e)))...)
end
mutable struct ThrowingPublisher
    writes::Int
    throw_at::Int
    sentinel::ErrorException
end
function E._write_numeric!(p::ThrowingPublisher,e,i,field,value)
    E._write_numeric!(E.NativePublisher(),e,i,field,value)
    p.writes+=1;p.writes==p.throw_at&&throw(p.sentinel)
    nothing
end
struct CaptureEvent
    slot::Base.RefValue{Union{Nothing,E.CompletionEvent}}
end
(c::CaptureEvent)(event)=(c.slot[]=event;nothing)
struct ThrowEvent{X}
    exception::X
end
(c::ThrowEvent)(event)=throw(c.exception)
