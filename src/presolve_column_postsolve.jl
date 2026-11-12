# Compact owned undo records; no original/reduced matrix, cache, or workspace.
module _ColumnPostsolve
const JS=parentmodule(@__MODULE__)
const CP=JS._ColumnMerge
const Q=Rational{BigInt}
q(v)=JS._exact_rational(v)
lo(b,t)=isfinite(b) ? q(JS.bound_value(b))-q(t) : nothing
hi(b,t)=isfinite(b) ? q(JS.bound_value(b))+q(t) : nothing
maxlo(a,b)=isnothing(a) ? b : isnothing(b) ? a : max(a,b)
minhi(a,b)=isnothing(a) ? b : isnothing(b) ? a : min(a,b)
inrange(v,l,u)=(isnothing(l)||v>=l)&&(isnothing(u)||v<=u)
struct Undo{T}
    op::CP.Merge{T}
    donor_lower::JS.Bound{T}
    donor_upper::JS.Bound{T}
end
struct Step{T} <: JS.AbstractPostsolveStep
    columns::Int
    rows::Int
    kept::Vector{Int}
    undo::Vector{Undo{T}}
end
function record(p::JS.LinearProblem{T},stage) where T
    keep=trues(size(p.A,2))
    for op in stage.operations;keep[op.donor]=false;end
    undo=Undo{T}[Undo(op,p.column_lower[op.donor],p.column_upper[op.donor]) for op in stage.operations]
    T===BigFloat && (undo=deepcopy(undo))
    Step(size(p.A,2),size(p.A,1),findall(keep),undo)
end
function bound_state(v,l,u,tol)
    JS._primal_interval_at_bound(v,v,l,tol) && return JS.AT_LOWER
    JS._primal_interval_at_bound(v,v,u,tol) && return JS.AT_UPPER
    !isfinite(l)&&!isfinite(u)&&iszero(v) && return JS.FREE_NONBASIC
    JS.BASIC
end
function pair(::Type{T},z,undo,tol,basic::Union{Nothing,Bool}) where T
    op=undo.op;alpha=op.alpha;zz=q(z)
    al,au=lo(op.lower_before,tol),hi(op.upper_before,tol)
    dl,du=lo(undo.donor_lower,tol),hi(undo.donor_upper,tol)
    left=isnothing(au) ? nothing : (zz-au)/alpha
    right=isnothing(al) ? nothing : (zz-al)/alpha
    alpha<0 && ((left,right)=(right,left))
    dl=maxlo(dl,left);du=minhi(du,right)
    !isnothing(dl)&&!isnothing(du)&&dl>du && return nothing
    seeds=Q[]
    for b in (op.lower_before,op.upper_before)
        isfinite(b) && push!(seeds,(zz-q(JS.bound_value(b)))/alpha)
    end
    for b in (undo.donor_lower,undo.donor_upper)
        isfinite(b) && push!(seeds,q(JS.bound_value(b)))
    end
    push!(seeds,zero(Q))
    !isnothing(dl) && push!(seeds,dl)
    !isnothing(du) && push!(seeds,du)
    for seed in seeds
        !isnothing(dl) && (seed=max(seed,dl))
        !isnothing(du) && (seed=min(seed,du))
        d0=T(seed);isfinite(d0) || continue
        for d in (d0,prevfloat(d0),nextfloat(d0))
            isfinite(d)&&inrange(q(d),dl,du) || continue
            a=JS._represent_exact(T,zz-alpha*q(d));isnothing(a) && continue
            inrange(q(a),al,au) || continue
            sa=bound_state(a,op.lower_before,op.upper_before,tol)
            sd=bound_state(d,undo.donor_lower,undo.donor_upper,tol)
            if basic===true
                sa==JS.BASIC&&sd==JS.BASIC && continue
                sa,sd=sd==JS.BASIC ? (sa,JS.BASIC) : (JS.BASIC,sd)
            elseif basic===false
                (sa==JS.BASIC||sd==JS.BASIC) && continue
            end
            return a,d,sa,sd
        end
    end
    nothing
end
function expand(step::Step{T},x) where T
    length(x)==length(step.kept)&&all(isfinite,x) || throw(ArgumentError("column postsolve dimensions/nonfinite point"))
    out=zeros(T,step.columns)
    for (i,j) in enumerate(step.kept);out[j]=x[i];end
    out
end
function primal(step::Step{T},x,tol::T) where T
    out=expand(step,x)
    for undo in Iterators.reverse(step.undo)
        op=undo.op;split=pair(T,out[op.anchor],undo,tol,nothing)
        isnothing(split) && throw(ArgumentError("no safe native proportional-column split"))
        out[op.anchor],out[op.donor]=split[1],split[2]
    end
    out
end
function lift(step::Step{T},b,y,x,options) where T
    n=length(step.kept);m=step.rows
    length(b.states)==n+m && length(b.basic_indices)==m && length(y)==m || throw(ArgumentError("column basis/dual dimensions"))
    out=expand(step,x);states=fill(JS.FREE_NONBASIC,step.columns+m)
    for (i,j) in enumerate(step.kept);states[j]=b.states[i];end
    copyto!(states,step.columns+1,b.states,n+1,m)
    indices=Vector{Int}(undef,m);slots=zeros(Int,step.columns+m)
    for (slot,j) in enumerate(b.basic_indices)
        1<=j<=n+m || throw(ArgumentError("column basis index"))
        k=j<=n ? step.kept[j] : step.columns+j-n
        slots[k]==0 && states[k]==JS.BASIC || throw(ArgumentError("invalid column basis"))
        indices[slot]=k;slots[k]=slot
    end
    count(==(JS.BASIC),states)==m || throw(ArgumentError("column basis states"))
    for undo in Iterators.reverse(step.undo)
        op=undo.op;a=op.anchor;d=op.donor;slot=slots[a]
        split=pair(T,out[a],undo,options.primal_tolerance,slot!=0)
        isnothing(split) && throw(ArgumentError("no safe proportional-column basis split"))
        out[a],out[d],states[a],states[d]=split
        if slot!=0 && states[d]==JS.BASIC
            indices[slot]=d;slots[d]=slot;slots[a]=0
        end
    end
    # A proposal only. No intermediate factorization or false certification:
    # the original cleanup installs/recomputes/certifies this entire chain.
    JS.Basis(indices,states,Val(:owned)),y,out
end
end
