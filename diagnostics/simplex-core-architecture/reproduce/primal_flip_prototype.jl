# Private qualification only. No production method is replaced or extended.
module PrimalFlipPrototype
using JSimplex,LinearAlgebra,SparseArrays,SHA,Logging
const JS=JSimplex
include("primal_flip_fixtures.jl")
const PF=PrimalFlipFixtures
# Bind existing helpers into this private module; cloned methods have new names.
for name in names(JS;all=true,imported=true)
    Base.isidentifier(string(name)) || continue
    isdefined(@__MODULE__,name) && continue
    @eval const $name = getfield(JS,$(QuoteNode(name)))
end
const SOURCE_HASHES=Dict(
    "primal_simplex.jl"=>"6246c3f92e1535561cc8a1fd2cf6b5a128ca39bfcc5d52eedd2fbb3a91417d41",
    "simplex_pivot.jl"=>"2cf399478648b82aa1502acdc33651c1afd914fa22ef833ca00a3765295e70a9")
const RENAMES=Dict(
    Symbol("_primal_optimize!") => Symbol("_flip_optimize!"),
    Symbol("_primal_iteration!") => Symbol("_flip_iteration!"),
    Symbol("_primal_iteration_core!") => Symbol("_flip_iteration_core!"),
    Symbol("_legacy_primal_iteration!") => Symbol("_flip_legacy_iteration!"),
    Symbol("_legacy_primal_reject_candidate!") => Symbol("_flip_reject_candidate!"),
    Symbol("_primal_iteration_unchecked!") => Symbol("_flip_iteration_unchecked!"))
mutable struct FlipAuditContext{W}
    owner::W
    dirty::Bool
    applied::Int
    audits::Int
    skips::Int
    fallbacks::Int
    endpoint_refreshes::Int
    candidate_copies::Int
    direct_recomputations::Int
end
FlipAuditContext(ws)=FlipAuditContext(ws,false,0,0,0,0,0,0,0)

function eligible_run(ws)
    T=eltype(ws.primal);p=ws.progress.numerical_policy
    return T in (Float32,Float64) && ws.options.algorithm==:primal &&
        ws.options.simplex_strategy==:legacy && ws.options.pricing==:dantzig &&
        !_is_staged_workspace(ws) && !ws.perturbed && _native_primal_kernel(p) &&
        !(p.incremental_primal || p.incremental_primal_pivots || p.pivot_validation ||
          p.solve_refinement || p.recovery || p.precision_boosting || p.lp_refinement ||
          p.adaptive_pricing || p.adaptive_primal_perturbation || p.adaptive_stalling)
end
function _flip_eligible(ctx,ws,entering,change)
    ctx.owner===ws || error("Foreign flip context")
    isfinite(change) && !iszero(change) || return false
    state=ws.basis.states[entering]
    state in (AT_LOWER,AT_UPPER) || return false
    target=state==AT_LOWER ? ws.upper[entering] : ws.lower[entering]
    return isfinite(target) && change==bound_value(target)-ws.primal[entering]
end
# Private qualification hooks dispatch only on the private context type.
_flip_apply_kernel!(ctx,ws,entering,change,column)=apply_primal_flip!(ws,entering,change,column)
_flip_certificate(ctx,ws)=_legacy_primal_point_certified(ws)
function _flip_apply!(ctx,ws,entering,change,column)
    try
        _flip_apply_kernel!(ctx,ws,entering,change,column)
    catch exception
        exception isa _UnreliableBasisSolve || exception isa OverflowError || rethrow()
        # Existing apply kernel validates every value before its first write.
        return false
    end
    ctx.applied+=1
    ctx.dirty=true
    return true
end
function _flip_audit!(ctx,ws)
    ctx.audits+=1
    return try
        _flip_certificate(ctx,ws)
    catch exception
        exception isa _UnreliableBasisSolve || exception isa OverflowError || rethrow()
        false
    end
end
function _flip_current_point!(ctx,ws)
    candidate=_pivot_quality_buffers(ws).trial
    for (row,index) in enumerate(ws.basis.basic_indices)
        candidate[row]=ws.primal[index]
    end
    ctx.candidate_copies+=1
    return candidate
end
function _flip_recompute!(ctx,ws;kwargs...)
    ctx.direct_recomputations+=1
    return recompute!(ws;kwargs...)
end
function _flip_refresh!(ctx,ws,stop)
    stop() && return DualTermination(TIME_LIMIT,"time limit reached before audited refresh")
    ctx.endpoint_refreshes+=1
    candidate=_flip_current_point!(ctx,ws)
    _flip_recompute!(ctx,ws;caller_guard=stop)
    recovery=_finish_legacy_primal_point!(ws,candidate,stop)
    isnothing(recovery) || return recovery
    _finite_workspace(ws) || return _numerical_failure()
    _primal_feasible(ws) || return DualTermination(NUMERICAL_ERROR,"primal feasibility lost")
    ctx.dirty=false
    return nothing
end

strip_lines(x)=x
function strip_lines(x::Expr)
    Expr(x.head,(strip_lines(a) for a in x.args if !(a isa LineNumberNode))...)
end
parsed(s)=strip_lines(Meta.parse(s))
function signature_call(signature)
    while signature isa Expr && signature.head in (:where,:(::))
        signature=signature.args[1]
    end
    signature isa Expr && signature.head==:call || error("Unexpected function signature")
    return signature
end
function insert_context!(call)
    position=length(call.args)>1 && call.args[2] isa Expr && call.args[2].head==:parameters ? 3 : 2
    insert!(call.args,position,:ctx)
    return call
end
function rewrite_calls(x)
    x isa Expr || return x
    out=Expr(x.head,map(rewrite_calls,x.args)...)
    if out.head==:call && out.args[1] isa Symbol
        name=out.args[1]
        if haskey(RENAMES,name)
            out.args[1]=RENAMES[name];insert_context!(out)
        elseif name==:recompute!
            out.args[1]=:_flip_recompute!;insert_context!(out)
        end
    end
    return out
end
function unresolved(x)
    x isa Expr || return false
    (x.head==:call && x.args[1] in keys(RENAMES)) || any(unresolved,x.args)
end
function transform_body(x,kind,hits)
    x isa Expr || return x
    # Inspect each original anchor once; inserted AST is not rewritten as source.
    y=Expr(x.head,(transform_body(a,kind,hits) for a in x.args)...)
    if kind==:_primal_iteration_unchecked!
        if x.head==:if && x.args[1]==:incremental
            hits[:flip]+=1
            y=quote
                if _flip_eligible(ctx,workspace,entering,direction*step)
                    applied_flip=_flip_apply!(ctx,workspace,entering,direction*step,tableau_column)
                end
                if !applied_flip
                    $y
                end
            end
        elseif x.head==:(=) && x.args[1]==:primal_candidate
            hits[:candidate]+=1
            y.args[2]=:(applied_flip ? _flip_current_point!(ctx,workspace) : $(y.args[2]))
        elseif x.head==:(=) && x.args[1]==:completed_updates
            hits[:skip]+=1
            y=quote
                if applied_flip && !refactorize
                    if _flip_audit!(ctx,workspace)
                        ctx.skips+=1
                        _simplex_event!(workspace,completion)
                        stop_requested() && return DualTermination(TIME_LIMIT,"time limit reached")
                        return nothing
                    end
                    ctx.fallbacks+=1
                end
                $y
            end
        elseif x.head==:if && x.args[1] in (parsed("entering == 0"),parsed("isnothing(step)"))
            hits[:endpoint]+=1
            guard=quote
                if ctx.dirty
                    refreshed=_flip_refresh!(ctx,workspace,stop_requested)
                    isnothing(refreshed) || return refreshed
                    return _primal_iteration_unchecked!(workspace,stop_requested,
                        reduced_cost_tolerance,basis_refreshed,defer_weak)
                end
            end
            y.args[2]=Expr(:block,guard,y.args[2])
        end
    elseif kind==:_primal_optimize!
        for (key,anchor) in ((:finite,parsed("_finite_workspace(workspace) || return _numerical_failure()")),
            (:feasible,parsed("_primal_feasible(workspace) || return DualTermination(NUMERICAL_ERROR, \"primal feasibility lost\")")))
            if x==anchor
                hits[key]+=1
                predicate=x.args[1]
                y=quote
                    if !$predicate
                        if ctx.dirty
                            refreshed=_flip_refresh!(ctx,workspace,stop_requested)
                            isnothing(refreshed) || return refreshed
                            continue
                        end
                        $(x.args[2])
                    end
                end
            end
        end
    end
    if x.head==:(=) && x.args[1]==:recovery && x.args[2] isa Expr &&
       x.args[2].head==:call && x.args[2].args[1]==:_finish_legacy_primal_point!
        hits[:finish]+=1
        y=quote
            $y
            isnothing(recovery) && (ctx.dirty=false)
        end
    end
    return y
end
const REWRITTEN_HASHES=Dict{String,String}()
function install_clones!()
    found=Dict{Symbol,Expr}()
    root=dirname(pathof(JS))
    for (file,expected) in SOURCE_HASHES
        source=read(joinpath(root,file),String)
        bytes2hex(sha256(source))==expected || error("Frozen source mismatch: $file")
        for expr in Meta.parseall(source).args
            expr isa Expr && expr.head==:function || continue
            call=signature_call(expr.args[1]);name=call.args[1]
            haskey(RENAMES,name) || continue
            haskey(found,name) && error("Duplicate source method: $name")
            found[name]=strip_lines(expr)
        end
    end
    Set(keys(found))==Set(keys(RENAMES)) || error("Missing private seam method")
    hits=Dict(k=>0 for k in (:flip,:candidate,:skip,:endpoint,:finite,:feasible,:finish))
    for name in sort!(collect(keys(found));by=string)
        original=found[name]
        body=transform_body(original.args[2],name,hits)
        call=signature_call(original.args[1]);position=call.args[2] isa Expr && call.args[2].head==:parameters ? 3 : 2
        owner=call.args[position];owner=owner isa Expr ? owner.args[1] : owner
        body=Expr(:block,:(ctx.owner===$owner || error("Foreign flip context")),body)
        if name==:_primal_iteration_unchecked!
            pushfirst!(body.args,:(applied_flip=false))
        end
        clone=rewrite_calls(Expr(:function,original.args[1],body))
        unresolved(clone) && error("Unresolved original seam call")
        REWRITTEN_HASHES[string(name)]=bytes2hex(sha256(string(clone)))
        Core.eval(@__MODULE__,clone)
    end
    hits==Dict(:flip=>1,:candidate=>1,:skip=>1,:endpoint=>2,:finite=>1,:feasible=>1,:finish=>3) ||
        error("Unexpected source anchors: $hits")
    return nothing
end
install_clones!()

# This entry builds its own problem/options/deadline/observer. It accepts no
# caller-owned workspace, logger, stop callback or arbitrary mutation hook.
function run_flip_experiment!(::Type{T},kind;manager=:pfi,backend=:native,candidate=true) where T
    fixture=PF.workspace(T,kind;manager,backend)
    ws,d=fixture.ws,fixture.diagnostics
    initial_basis=copy(ws.basis.basic_indices);initial_prices=copy(ws.reduced_costs)
    ctx=FlipAuditContext(ws)
    enabled=candidate && eligible_run(ws)
    stop=PF.deadline(ws,d)
    terminal=with_logger(NullLogger()) do
        enabled ? _flip_optimize!(ctx,ws,stop,ws.options.dual_tolerance;perturb_degenerate=false) :
            JS._primal_optimize!(ws,stop,ws.options.dual_tolerance;perturb_degenerate=false)
    end
    calls=copy(d.kernel_calls)
    stats=(;ctx.dirty,ctx.applied,ctx.audits,ctx.skips,ctx.fallbacks,ctx.endpoint_refreshes,
        ctx.candidate_copies,ctx.direct_recomputations)
    run=JS._internal_solution(ws,terminal)
    return (;run,calls,stats,enabled,events=copy(fixture.events),
        feasible=!isnothing(run.primal) && JS._original_primal_feasible(fixture.problem,run.primal,ws.options.primal_tolerance),
        basis_unchanged=ws.basis.basic_indices==initial_basis,prices_unchanged=ws.reduced_costs==initial_prices,
        iterations=ws.iterations,updates=length(ws.factorization.updates))
end
end
