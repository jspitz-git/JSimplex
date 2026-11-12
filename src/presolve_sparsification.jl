# One bounded row-equivalence batch and a provisional postsolve hint.
module _RowSparsification
using SparseArrays
const JS=parentmodule(@__MODULE__)
const Q=Rational{BigInt}
q(x)=JS._exact_rational(x)
struct Operation{T}
    equality::Int
    target::Int
    scale::T
end
struct Candidate{T}
    op::Operation{T}
    saving::Int
end
mutable struct Budget
    left::Int
    used::Int
    exhausted::Bool
end
function charge!(b,n)
    if n>b.left
        b.exhausted=true
        return false
    end
    b.left-=n;b.used+=n
    true
end
inc!(s,k)=s[k]=get(s,k,0)+1

# Check a single pair without touching either model. All cancellations and
# representation decisions refer to exact values of the stored input numbers.
function transformed(p,rows,op::Operation{T},budget,stats) where T
    i,k=op.equality,op.target;eq,row=rows[i],rows[k]
    charge!(budget,2length(row)+2length(eq)) || return nothing
    z=Dict(j=>q(v) for (j,v) in row);scale=q(op.scale)
    oldmax=maximum(abs(q(v)) for (_,v) in row)
    for (j,v) in eq
        new=get(z,j,zero(Q))+scale*q(v)
        iszero(new) ? delete!(z,j) : (z[j]=new)
    end
    length(z)<length(row) || return nothing
    charge!(budget,2length(z)) || return nothing
    maximum(abs,values(z);init=zero(Q))<=2oldmax || (inc!(stats,"growth_rejected");return nothing)
    entries=Tuple{Int,T}[]
    for (j,v) in z
        native=JS._represent_exact(T,v)
        isnothing(native) && (inc!(stats,"coefficient_rejected");return nothing)
        push!(entries,(j,native))
    end
    shift=scale*q(JS.bound_value(p.row_lower[i]))
    lower=JS._shift_bound_exact(T,p.row_lower[k],-shift)
    upper=p.row_lower[k]==p.row_upper[k] ? lower : JS._shift_bound_exact(T,p.row_upper[k],-shift)
    (isnothing(lower)||isnothing(upper)) && (inc!(stats,"bound_rejected");return nothing)
    sort!(entries;by=first)
    (entries=entries,lower=lower,upper=upper,saving=length(row)-length(entries))
end

function sparsify(p::JS.LinearProblem{T};work_limit=2_000_000,stop_requested=()->false) where T
    work_limit>=0 || throw(ArgumentError("negative work budget"))
    stats=Dict{String,Int}("term_visits"=>0,"initialization_terms"=>0,
        "matrix_build_terms"=>0,"selected"=>0,"nnz_removed"=>0,"exhausted"=>0,"stopped"=>0)
    function identity()
        stats["selected"]=0;stats["nnz_removed"]=0;stats["explicit_zeros_removed"]=0
        return (problem=p,operations=Operation{T}[],stats=stats)
    end
    (stop_requested() || work_limit==0) && begin
        stats[work_limit==0 ? "exhausted" : "stopped"]=1
        return identity()
    end
    rows=JS._row_entries(p.A)
    stats["initialization_terms"]=nnz(p.A)*(nnz(p.A)>size(p.A,1) ? 2 : 1)
    # Reserve one quarter of the shared pass budget for revalidation/staging.
    search_limit=work_limit-div(work_limit,4)
    budget=Budget(search_limit,0,false);candidates=Candidate{T}[]
    for i in eachindex(rows)
        stop_requested() && (stats["stopped"]=1;stats["term_visits"]=budget.used;return identity())
        eq=rows[i]
        2<=length(eq)<=64 || continue
        isfinite(p.row_lower[i]) && p.row_lower[i]==p.row_upper[i] || continue
        inc!(stats,"equalities")
        charge!(budget,length(eq)) || break
        j=first(eq[argmin([p.A.colptr[j+1]-p.A.colptr[j] for (j,_) in eq])])
        for pos in nzrange(p.A,j)
            k=p.A.rowval[pos];k==i && continue
            row=rows[k]
            charge!(budget,length(row)+length(eq)) || break
            inc!(stats,"pairs")
            rd=Dict(j=>v for (j,v) in row);scales=Dict{Q,Int}();missing=0
            for (col,a) in eq
                if haskey(rd,col)
                    scale=-q(rd[col])/q(a)
                    scales[scale]=get(scales,scale,0)+1
                else
                    missing+=1
                end
            end
            for scale in sort!(collect(keys(scales));by=x->(abs(x),x))
                scales[scale]>missing || continue
                abs(scale)<=1 || (inc!(stats,"large_scale_rejected");continue)
                native=JS._represent_exact(T,scale)
                isnothing(native) && (inc!(stats,"scale_rejected");continue)
                op=Operation(i,k,native)
                result=transformed(p,rows,op,budget,stats)
                !isnothing(result) && push!(candidates,Candidate(op,result.saving))
                budget.exhausted && break
            end
            budget.exhausted && break
        end
        budget.exhausted && break
    end
    stats["candidates"]=length(candidates)
    search_exhausted=budget.exhausted
    stats["term_visits"]=budget.used;stats["exhausted"]=Int(search_exhausted)
    isempty(candidates) && return identity()
    budget.left=work_limit-budget.used;budget.exhausted=false
    sort!(candidates;by=c->(-c.saving,c.op.target,c.op.equality,abs(c.op.scale)))
    targets=falses(length(rows));anchors=falses(length(rows))
    operations=Operation{T}[]
    updates=Dict{Int,Vector{Tuple{Int,T}}}()
    lo=p.row_lower;hi=p.row_upper
    for c in candidates
        stop_requested() && (stats["stopped"]=1;stats["term_visits"]=budget.used;return identity())
        op=c.op;i,k=op.equality,op.target
        (targets[k]||anchors[k]||targets[i]) && continue
        result=transformed(p,rows,op,budget,stats)
        budget.exhausted && break
        isnothing(result) && continue
        if lo===p.row_lower
            lo=copy(p.row_lower);hi=copy(p.row_upper)
        end
        targets[k]=true;anchors[i]=true
        updates[k]=result.entries;lo[k]=result.lower;hi[k]=result.upper
        push!(operations,op);stats["nnz_removed"]+=result.saving
    end
    stats["term_visits"]=budget.used;stats["exhausted"]=Int(search_exhausted||budget.exhausted)
    isempty(operations) && return identity()
    # One batch-level construction, never one matrix/model copy per candidate.
    I=Int[];J=Int[];V=T[]
    stats["explicit_zeros_removed"]=nnz(p.A)-sum(length,rows)
    stats["nnz_removed"]+=stats["explicit_zeros_removed"]
    expected_nnz=nnz(p.A)-stats["nnz_removed"]
    sizehint!(I,expected_nnz);sizehint!(J,expected_nnz);sizehint!(V,expected_nnz)
    for k in eachindex(rows)
        for (j,v) in get(updates,k,rows[k])
            push!(I,k);push!(J,j);push!(V,v)
        end
    end
    stats["matrix_build_terms"]=length(V)
    stop_requested() && (stats["stopped"]=1;stats["nnz_removed"]=0;return identity())
    A=sparse(I,J,V,size(p.A)...)
    result=JS.LinearProblem{T}(A,p.objective,p.objective_constant,p.objective_sense,
        lo,hi,p.column_lower,p.column_upper,p.variable_domains,p.name,p.row_names,p.column_names)
    stats["selected"]=length(operations)
    (problem=result,operations=operations,stats=stats)
end

# For A'=E*A the original dual is E'*y'. E changes only target rows and
# targets/anchors are disjoint. A structural column transforms with E; a
# logical column does so too unless it belongs to an anchor. Thus the same
# basis indices are proved valid here when all anchor logicals are nonbasic.
# x is a borrowed unchanged vector; returned dual/basis are owned when changed.
function lift(operations,m,n,b::JS.Basis,y::Vector{T},x::Vector{T}; provisional=false) where T
    length(y)==m && length(x)==n && length(b.states)==n+m && length(b.basic_indices)==m ||
        throw(ArgumentError("lift dimensions"))
    all(isfinite,x) && all(isfinite,y) || throw(ArgumentError("nonfinite lift input"))
    length(unique(b.basic_indices))==m && all(j->1<=j<=n+m && b.states[j]==JS.BASIC,b.basic_indices) &&
        count(==(JS.BASIC),b.states)==m || throw(ArgumentError("invalid basis"))
    isempty(operations) && return (basis=b,dual=y,primal=x,reason="identity")
    sums=Dict{Int,Q}()
    for op in operations
        isfinite(op.scale) || throw(ArgumentError("nonfinite lift scale"))
        iszero(y[op.target]) && continue
        sums[op.equality]=get(sums,op.equality,q(y[op.equality]))+q(op.scale)*q(y[op.target])
    end
    restored=copy(y)
    for (i,v) in sums
        # This is a restoration HINT, never an accepted dual certificate.
        # Round the exact sum once in the unchanged working precision. The
        # original cleanup recomputes all values from its own basis/model.
        native=T(v)
        isfinite(native) || return (basis=nothing,dual=nothing,primal=x,reason="nonfinite_dual_hint")
        restored[i]=native
    end
    if any(op->b.states[n+op.equality]==JS.BASIC,operations)
        # Same indices are NOT proved nonsingular when an anchor logical is
        # basic. An explicit caller may request a provisional candidate ONLY
        # for the original-model factor/recompute/cleanup validation boundary.
        # Never use this candidate as a certified basis or bypass that boundary.
        provisional && return (basis=JS.Basis(b.basic_indices,b.states),dual=restored,
            primal=x,reason="provisional_basic_anchor")
        return (basis=nothing,dual=restored,primal=x,reason="basic_anchor_logical")
    end
    (basis=JS.Basis(b.basic_indices,b.states),dual=restored,primal=x,reason="restored")
end
end
