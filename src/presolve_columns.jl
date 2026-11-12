# Bounded optional proportional-column engines. Disabled unless requested.
module _ColumnMerge
using SparseArrays
const JS = parentmodule(@__MODULE__)
const Q = Rational{BigInt}
exact_value(v)=Q(v)
exact_value(v::BigFloat)=JS._exact_rational(v)
inc!(s,k,n=1) = (s[k]=get(s,k,0)+n)

struct Merge{T}
    anchor::Int
    donor::Int
    alpha::Q
    lower_before::JS.Bound{T}
    upper_before::JS.Bound{T}
    lower_after::JS.Bound{T}
    upper_after::JS.Bound{T}
end
struct Dominance{T}
    donor::Int
    receiver::Int
    donor_sign::Int
    receiver_sign::Int
    alpha::Q
    value::T
end

struct Groups{T}
    matrix::SparseMatrixCSC{T,Int}
    groups::Vector{Vector{Int}}
end

function exact_cache(::Type{T}) where T
    cache=Dict{T,Q}()
    function exact(x::T)
        prior=get(cache,x,nothing)
        prior isa Q && return prior
        v=exact_value(x)
        length(cache)<100_000 && (cache[x]=v)
        v
    end
    exact,cache
end

anchor_magnitude(x,exact)=abs(x)
anchor_magnitude(x::BigFloat,exact)=abs(exact(x))

# Same entry cap as native; additionally bound retained arbitrary-precision
# payloads. Cache misses still compute the identical exact result.
function exact_cache(::Type{BigFloat};bytecap=64*1024^2)
    bytecap>=0 || throw(ArgumentError("negative exact cache byte cap"))
    cache=Dict{BigFloat,Q}();used=Ref(0)
    function exact(x::BigFloat)
        old=get(cache,x,nothing)
        old isa Q && return old
        value=JS._exact_rational(x)
        if length(cache)<100_000
            cost=JS._PresolveWork.keybytes(x,value)
            if cost<=bytecap-used[]
                cache[JS._PresolveWork.owned(x)]=value
                used[]+=cost
            end
        end
        value
    end
    exact,cache
end

positions(A,j) = (k for k in nzrange(A,j) if !iszero(A.nzval[k]))

# The first partition is native support hashing. Exact ratios are only formed
# inside repeated supports; unique sparse columns require no BigInt signature.
function parallel_groups(p,exact,stats)
    A=p.A
    buckets=Dict{Tuple{UInt,Int},Vector{Int}}()
    for j in axes(A,2)
        h=UInt(0);n=0
        for k in positions(A,j)
            h=hash(A.rowval[k],h);n+=1
        end
        n==0 && continue
        push!(get!(() -> Int[],buckets,(h,n)),j)
    end
    result=Vector{Int}[]
    for bucket in values(buckets)
        length(bucket)==1 && continue
        # Hash collisions never constitute a support or proportionality proof.
        supports=Dict{Vector{Int},Vector{Int}}()
        for j in bucket
            support=Int[A.rowval[k] for k in positions(A,j)]
            push!(get!(() -> Int[],supports,support),j)
        end
        for same_support in values(supports)
            length(same_support)==1 && continue
            inc!(stats,"columns_with_repeated_support",length(same_support))
            signatures=Dict{Vector{Q},Vector{Int}}()
            for j in same_support
                pivot=exact(A.nzval[first(positions(A,j))])
                signature=Q[exact(A.nzval[k])/pivot for k in positions(A,j)]
                push!(get!(() -> Int[],signatures,signature),j)
                inc!(stats,"exact_signature_terms",length(signature))
            end
            for group in values(signatures)
                length(group)>1 && push!(result,sort!(group))
            end
        end
    end
    sort!(result;by=first)
    stats["parallel_groups"]=length(result)
    stats["parallel_extra_columns"]=sum(g->length(g)-1,result;init=0)
    Groups(A,result)
end

function sum_endpoint(::Type{T},a,b,alpha,exact) where T
    (!isfinite(a)||!isfinite(b)) && return JS._unbounded_bound(T)
    value=JS._represent_exact(T,exact(JS.bound_value(a))+alpha*exact(JS.bound_value(b)))
    isnothing(value) ? nothing : JS.Bound(value)
end

function merge_columns(p::JS.LinearProblem{T};identical_only=false,groups=nothing,exact_state=nothing) where T
    @assert T in (Float32,Float64,BigFloat) && JS.is_continuous(p)
    stats=Dict{String,Int}("selected"=>0,"bound_rejected"=>0,"cost_groups"=>0,
        "different_cost_columns"=>0,"nonidentical_columns_skipped"=>0)
    exact,cache=isnothing(exact_state) ? exact_cache(T) : exact_state
    groups=isnothing(groups) ? parallel_groups(p,exact,stats) : groups
    groups.matrix===p.A || throw(ArgumentError("column groups belong to a different immutable input matrix"))
    A=p.A;n=size(A,2);keep=nothing
    lower=p.column_lower;upper=p.column_upper
    operations=Merge{T}[]
    for group in groups.groups
        costs=Dict{Q,Vector{Int}}()
        for j in group
            pivot=exact(A.nzval[first(positions(A,j))])
            push!(get!(() -> Int[],costs,exact(p.objective[j])/pivot),j)
        end
        inc!(stats,"cost_groups",length(costs))
        inc!(stats,"different_cost_columns",length(costs)-1)
        for same_cost in values(costs)
          subgroups=if identical_only
            pivots=Dict{T,Vector{Int}}()
            for j in same_cost
                pivot=A.nzval[first(positions(A,j))]
                push!(get!(() -> Int[],pivots,pivot),j)
            end
            collect(values(pivots))
          else
            [same_cost]
          end
          for subgroup in subgroups
            # Smallest pivot avoids the simple [3A,A] -> nonrepresentable 4/3
            # choice. This remains a heuristic, not exhaustive anchor search.
            anchor=minimum(j->(anchor_magnitude(A.nzval[first(positions(A,j))],exact),j),subgroup)[2]
            ap=exact(A.nzval[first(positions(A,anchor))])
            for j in subgroup
                j==anchor && continue
                alpha=exact(A.nzval[first(positions(A,j))])/ap
                identical_only && @assert alpha==1
                low,high=alpha>0 ? (p.column_lower[j],p.column_upper[j]) :
                                  (p.column_upper[j],p.column_lower[j])
                l=sum_endpoint(T,lower[anchor],low,alpha,exact)
                u=sum_endpoint(T,upper[anchor],high,alpha,exact)
                (isnothing(l)||isnothing(u)) && (inc!(stats,"bound_rejected");continue)
                if lower===p.column_lower
                    lower=copy(lower);upper=copy(upper);keep=trues(n)
                end
                push!(operations,Merge(anchor,j,alpha,lower[anchor],upper[anchor],l,u))
                lower[anchor]=l;upper[anchor]=u;keep[j]=false
            end
          end
        end
    end
    stats["selected"]=length(operations);stats["exact_cache_entries"]=length(cache)
    isempty(operations) && return (problem=p,operations=operations,stats=stats)
    cols=findall(keep)
    # Only A/objective/column-bound/domain/name slices are fresh. The remaining
    # borrowed arrays are copied by the original validated model constructor.
    reduced=JS._presolve_model(Val(2499),A[:,cols],p.objective[cols],p.objective_constant,
        p.objective_sense,p.row_lower,p.row_upper,lower[cols],upper[cols],
        p.variable_domains[cols],p.name,p.row_names,
        isempty(p.column_names) ? String[] : p.column_names[cols])
    (problem=reduced,operations=operations,stats=stats)
end

end

module _ColumnDominance
using SparseArrays
const JS=parentmodule(@__MODULE__)
const CP=JS._ColumnMerge
const Q=Rational{BigInt}
const Endpoint=Union{Nothing,Q}
struct Capacity{T}
    donor::Int
    receiver::Int
    donor_sign::Int
    alpha::Q
    value::T
    aggregate_lower::Endpoint
    aggregate_upper::Endpoint
end
struct RowIndex
    ptr::Vector{Int}
    columns::Vector{Int}
    positions::Vector{Int}
end
struct Activity
    minimum::Q
    maximum::Q
    minimum_infinite::Int
    maximum_infinite::Int
end
inc!(s,k,n=1)=(s[k]=get(s,k,0)+n)
lowermax(a,b)=isnothing(a) ? b : isnothing(b) ? a : max(a,b)
uppermin(a,b)=isnothing(a) ? b : isnothing(b) ? a : min(a,b)

function row_index(A)
    ptr=ones(Int,size(A,1)+1)
    for k in 1:nnz(A);ptr[A.rowval[k]+1]+=1;end
    for i in 2:length(ptr);ptr[i]+=ptr[i-1]-1;end
    columns=Vector{Int}(undef,nnz(A));positions=similar(columns);next=copy(ptr)
    for j in axes(A,2),k in nzrange(A,j)
        r=A.rowval[k];at=next[r];columns[at]=j;positions[at]=k;next[r]+=1
    end
    RowIndex(ptr,columns,positions)
end

function contribution(p,j,a,minimum,exact)
    iszero(a) && return zero(Q),0
    b=(a>0)==minimum ? p.column_lower[j] : p.column_upper[j]
    isfinite(b) ? (a*exact(JS.bound_value(b)),0) : (zero(Q),1)
end

function interval_box(p,r,d,alpha,exact)
    dl,du=alpha>0 ? (p.column_lower[d],p.column_upper[d]) : (p.column_upper[d],p.column_lower[d])
    lo=isfinite(p.column_lower[r])&&isfinite(dl) ? exact(JS.bound_value(p.column_lower[r]))+alpha*exact(JS.bound_value(dl)) : nothing
    hi=isfinite(p.column_upper[r])&&isfinite(du) ? exact(JS.bound_value(p.column_upper[r]))+alpha*exact(JS.bound_value(du)) : nothing
    lo,hi
end

function projection(p,r,d,alpha,index,cache,exact,stats,term_limit)
    lo,hi=interval_box(p,r,d,alpha,exact)
    need=p.A.colptr[r+1]-p.A.colptr[r]
    if stats["activity_terms"]+stats["projection_terms"]+need>term_limit
        stats["budget_exhausted"]=1;return nothing
    end
    inc!(stats,"projection_terms",need)
    for k in CP.positions(p.A,r)
        i=p.A.rowval[k];a=exact(p.A.nzval[k])
        !isfinite(p.row_lower[i])&&!isfinite(p.row_upper[i]) && continue
        activity=get(cache,i,nothing)
        if isnothing(activity)
            need=index.ptr[i+1]-index.ptr[i]
            if stats["activity_terms"]+stats["projection_terms"]+need>term_limit
                stats["budget_exhausted"]=1;return nothing
            end
            inc!(stats,"activity_terms",need)
            smn=zero(Q);smx=zero(Q);imn=0;imx=0
            for at in index.ptr[i]:index.ptr[i+1]-1
                j=index.columns[at];v=exact(p.A.nzval[index.positions[at]])
                vmin,imin=contribution(p,j,v,true,exact);vmax,imax=contribution(p,j,v,false,exact)
                smn+=vmin;smx+=vmax;imn+=imin;imx+=imax
            end
            activity=Activity(smn,smx,imn,imx);cache[i]=activity
        end
        mn=activity.minimum;mx=activity.maximum;imn=activity.minimum_infinite;imx=activity.maximum_infinite
        for (j,v) in ((r,a),(d,alpha*a))
            vmin,imin=contribution(p,j,v,true,exact);vmax,imax=contribution(p,j,v,false,exact)
            mn-=vmin;mx-=vmax;imn-=imin;imx-=imax
        end
        @assert imn>=0 && imx>=0
        if isfinite(p.row_lower[i]) && imx==0
            v=(exact(JS.bound_value(p.row_lower[i]))-mx)/a
            a>0 ? (lo=lowermax(lo,v)) : (hi=uppermin(hi,v))
        end
        if isfinite(p.row_upper[i]) && imn==0
            v=(exact(JS.bound_value(p.row_upper[i]))-mn)/a
            a>0 ? (hi=uppermin(hi,v)) : (lo=lowermax(lo,v))
        end
        if !isnothing(lo)&&!isnothing(hi)&&lo>hi
            inc!(stats,"aggregate_conflicts");return nothing
        end
    end
    (lo,hi)
end

function contained(p,r,value,alpha,lo,hi,exact)
    if isfinite(p.column_lower[r])
        isnothing(lo) && return false
        lo>=exact(JS.bound_value(p.column_lower[r]))+alpha*exact(value) || return false
    end
    if isfinite(p.column_upper[r])
        isnothing(hi) && return false
        hi<=exact(JS.bound_value(p.column_upper[r]))+alpha*exact(value) || return false
    end
    true
end

function group_pairs(group,p,exact,stats)
    if length(group)<=32
        return [(group[i],group[j]) for i in 1:length(group)-1 for j in i+1:length(group)]
    end
    inc!(stats,"heuristic_large_groups")
    scores=[(exact(p.objective[j])/exact(p.A.nzval[first(CP.positions(p.A,j))]),j) for j in group]
    sort!(scores);ordered=Int[last(score) for score in scores]
    pairs=Set{Tuple{Int,Int}}()
    for j in group,a in (first(ordered),last(ordered))
        j==a || push!(pairs,minmax(j,a))
    end
    for i in 1:length(ordered)-1;push!(pairs,minmax(ordered[i],ordered[i+1]));end
    sort!(collect(pairs))
end

function capacity_columns(p::JS.LinearProblem{T};term_limit=20_000_000,pair_limit=1_000_000,groups=nothing,exact_state=nothing) where T
    @assert T in (Float32,Float64,BigFloat) && JS.is_continuous(p) && term_limit>=0 && pair_limit>=0
    stats=Dict{String,Int}("selected"=>0,"proposed"=>0,"fixing_rejected"=>0,
        "pairs"=>0,"orientations"=>0,"activity_terms"=>0,"projection_terms"=>0,
        "aggregate_conflicts"=>0,"capacity_rejected"=>0,"cost_rejected"=>0,
        "budget_exhausted"=>0,"heuristic_large_groups"=>0,"finite_receiver_selected"=>0,
        "row_index_terms"=>0,"cached_rows"=>0)
    exact,qcache=isnothing(exact_state) ? CP.exact_cache(T) : exact_state;certificates=Capacity{T}[]
    groups=isnothing(groups) ? CP.parallel_groups(p,exact,Dict{String,Int}()) : groups
    groups.matrix===p.A || throw(ArgumentError("capacity groups refer to a different matrix"))
    (isempty(groups.groups)||term_limit==0||pair_limit==0) && return (result=JS.identity_presolve(p),certificates=certificates,stats=stats,index=nothing)
    index=row_index(p.A);stats["row_index_terms"]=length(index.positions)
    cache=Dict{Int,Activity}();n=size(p.A,2);fixed=falses(n);protected=falses(n)
    selections=Vector{Union{Nothing,Tuple{T,JS.VariableState}}}(nothing,n)
    sense=p.objective_sense==JS.MIN_SENSE ? 1 : -1
    for group in groups.groups
        for (r,d) in group_pairs(group,p,exact,stats)
            if stats["pairs"]>=pair_limit
                stats["budget_exhausted"]=1;break
            end
            inc!(stats,"pairs")
            (fixed[r]||fixed[d]) && continue
            alpha=exact(p.A.nzval[first(CP.positions(p.A,d))])/exact(p.A.nzval[first(CP.positions(p.A,r))])
            projected=projection(p,r,d,alpha,index,cache,exact,stats,term_limit)
            isnothing(projected) && (stats["budget_exhausted"]==1 ? break : continue)
            lo,hi=projected
            for swapped in (false,true)
                donor,receiver=swapped ? (r,d) : (d,r)
                (fixed[donor]||protected[donor]||fixed[receiver]) && continue
                ratio=swapped ? inv(alpha) : alpha
                low,high=if !swapped
                    lo,hi
                elseif alpha>0
                    isnothing(lo) ? nothing : lo/alpha,isnothing(hi) ? nothing : hi/alpha
                else
                    isnothing(hi) ? nothing : hi/alpha,isnothing(lo) ? nothing : lo/alpha
                end
                for sd in (-1,1)
                    bound=sd<0 ? p.column_lower[donor] : p.column_upper[donor]
                    isfinite(bound) || continue
                    inc!(stats,"orientations")
                    if sense*sd*(exact(p.objective[donor])-ratio*exact(p.objective[receiver]))>0
                        inc!(stats,"cost_rejected");continue
                    end
                    value=JS.bound_value(bound)
                    if !contained(p,receiver,value,ratio,low,high,exact)
                        inc!(stats,"capacity_rejected");continue
                    end
                    push!(certificates,Capacity(donor,receiver,sd,ratio,value,low,high))
                    selections[donor]=(value,sd<0 ? JS.AT_LOWER : JS.AT_UPPER)
                    fixed[donor]=true;protected[receiver]=true
                    break
                end
            end
            stats["budget_exhausted"]==1 && break
        end
        stats["budget_exhausted"]==1 && break
    end
    stats["proposed"]=length(certificates);stats["cached_rows"]=length(cache);stats["exact_cache_entries"]=length(qcache)
    isempty(certificates) && return (result=JS.identity_presolve(p),certificates=certificates,stats=stats,index=index)
    result=JS._presolve_basic(p;selections)
    result isa JS.PresolveFailure && return (result=result,certificates=certificates,stats=stats,index=index)
    removed=isempty(result.postsolve_stack) ? Set{Int}() : Set(findall(!isnothing,first(result.postsolve_stack).removed_values))
    filter!(c->c.donor in removed,certificates)
    stats["selected"]=length(certificates);stats["fixing_rejected"]=stats["proposed"]-stats["selected"]
    for c in certificates
        sr=c.alpha*c.donor_sign<0 ? 1 : -1
        isfinite(sr>0 ? p.column_upper[c.receiver] : p.column_lower[c.receiver]) && inc!(stats,"finite_receiver_selected")
    end
    (result=result,certificates=certificates,stats=stats,index=index)
end
end
