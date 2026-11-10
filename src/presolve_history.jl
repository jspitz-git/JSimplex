# Compact propagation proofs live only from presolve to postsolve.
module _PropagationHistory
const JS=parentmodule(@__MODULE__)
struct Event{T}
 proof::Int
 position::Int
 column::Int
 upper::Bool
 old::JS.Bound{T}
 new::T
end
at(x,b,tol)=JS._primal_interval_at_bound(x,x,b,tol)
struct Proof{T}
 row::Int
 lowerrow::Bool
 bound::JS.Bound{T}
 first::Int
 last::Int
 usedfirst::Int
end
struct Column{T}
 cost::T
 first::Int
 last::Int
end
struct Group{T}
 proofs::Vector{Proof{T}}
 events::Vector{Event{T}}
 terms::Vector{Tuple{Int,T}}
 used::Vector{T}
 bounded::BitVector
 column_ids::Vector{Int}
 columns::Vector{Column{T}}
 rows::Vector{Int}
 values::Vector{T}
end
Group(T)=Group(Proof{T}[],Event{T}[],Tuple{Int,T}[],T[],BitVector(),Int[],Column{T}[],Int[],T[])
mutable struct Builder{T}
 group::Group{T}
 row::Int
 first::Int
 lowerproof::Int
 upperproof::Int
 minused::Vector{JS.Bound{T}}
 maxused::Vector{JS.Bound{T}}
end
Builder(::Type{T}) where T = Builder(Group(T),0,0,0,0,JS.Bound{T}[],JS.Bound{T}[])
# Invoked immediately before each accepted write. Before the first write in a
# row, these native bounds are precisely those used to build min/max_terms.
function record!(b::Builder{T},p,row,columns,lower,upper,position,column,old,new,isupper) where T
 g=b.group
 if b.row!=row
  b.row=row;b.first=length(g.terms)+1;b.lowerproof=b.upperproof=0
  append!(g.terms,columns)
  resize!(b.minused,length(columns));resize!(b.maxused,length(columns))
  for (k,(j,a)) in enumerate(columns)
   b.minused[k],b.maxused[k]=a>0 ? (lower[j],upper[j]) : (upper[j],lower[j])
  end
 end
 lowerrow=(columns[position][2]>0)!=isupper
 id=lowerrow ? b.lowerproof : b.upperproof
 if id==0
  usedfirst=length(g.used)+1
  for bound in (lowerrow ? b.maxused : b.minused)
   push!(g.used,bound.value);push!(g.bounded,isfinite(bound))
  end
  push!(g.proofs,Proof(row,lowerrow,lowerrow ? p.row_lower[row] : p.row_upper[row],b.first,b.first+length(columns)-1,usedfirst))
  id=length(g.proofs)
  lowerrow ? (b.lowerproof=id) : (b.upperproof=id)
 end
 push!(g.events,Event(id,position,column,isupper,old,new))
 nothing
end
function finish!(b::Builder{T},p) where T
 g=b.group
 # A row-removal-only pass still needs its empty Group, but no column scan.
 isempty(g.events) && return g
 # Ordered native indices replace a retained hash table. Exact lengths avoid
 # spare capacity for the largest copied storage. No solver arithmetic changes.
 seen=falses(length(p.objective));for e in g.events;seen[e.column]=true;end
 ids=findall(seen)
 nnz=sum(p.A.colptr[j+1]-p.A.colptr[j] for j in ids;init=0)
 rows=Vector{Int}(undef,nnz);values=Vector{T}(undef,nnz)
 cols=Vector{Column{T}}(undef,length(ids));offset=1
 for (k,j) in enumerate(ids)
  source=p.A.colptr[j];n=p.A.colptr[j+1]-source
  copyto!(rows,offset,p.A.rowval,source,n);copyto!(values,offset,p.A.nzval,source,n)
  cols[k]=Column(p.objective[j],offset,offset+n-1);offset+=n
 end
 # Julia may copy/reallocate when shrinking; this pass-level cost is timed.
 for v in (g.proofs,g.events,g.terms,g.used,g.bounded)
  sizehint!(v,length(v))
 end
 Group(g.proofs,g.events,g.terms,g.used,g.bounded,ids,cols,rows,values)
end
function price(g,j,y)
 idx=searchsortedfirst(g.column_ids,j);@assert idx<=length(g.column_ids) && g.column_ids[idx]==j
 c=g.columns[idx];v=c.cost
 for k in c.first:c.last;v=JS._PostsolveLift.price_step(v,g.values[k],y[g.rows[k]]);end
 v
end
function proof_activity(g,p,x,o)
 T=eltype(x);low=high=zero(T);bad=0
 for (k,idx) in enumerate(p.first:p.last)
  j,a=g.terms[idx]
  l,u=JS._primal_product_bounds(a,x[j]);low,_=JS._primal_sum_bounds(low,l);_,high=JS._primal_sum_bounds(high,u)
  if !at(x[j],JS.Bound{T}(g.used[p.usedfirst+k-1],g.bounded[p.usedfirst+k-1]),o.primal_tolerance)
   bad = bad == 0 ? k : -1
  end
 end
 JS._primal_interval_at_bound(low,high,p.bound,o.primal_tolerance),bad
end
function apply(g::Group{T},b,y,x,o) where T
 m=length(b.basic_indices);n=length(b.states)-m
 @assert length(y)==m && length(x)==n
 # One inverse position vector per propagation pass, not a scan per event.
 isempty(g.events) && return b,y
 positions=zeros(Int,m);for (slot,j) in enumerate(b.basic_indices);j>n && (positions[j-n]=slot);end
 cached=Dict{Int,Tuple{Bool,Int}}()
 for e in Iterators.reverse(g.events)
  j=e.column;p=g.proofs[e.proof];row=p.row;logical=n+row
  if b.states[j]==JS.BASIC;continue;end
  if !at(x[j],JS.Bound(e.new),o.primal_tolerance);continue;end
  if at(x[j],e.old,o.primal_tolerance);continue;end
  if positions[row]==0 || abs(y[row])>o.dual_tolerance;continue;end
  a=g.terms[p.first+e.position-1][2]
  if abs(a)<=o.zero_tolerance;continue;end
  other_basic=false
  for idx in p.first:p.last
   k,_=g.terms[idx]
   if k!=j && b.states[k]==JS.BASIC;other_basic=true;break;end
  end
  if other_basic;continue;end
  active,bad=get!(cached,e.proof) do
   proof_activity(g,p,x,o)
  end
  if !active;continue;end
  if bad!=0 && bad!=e.position;continue;end
  r=price(g,j,y)
  if !isfinite(r);continue;end
  if !(e.upper ? r < -o.dual_tolerance : r > o.dual_tolerance);continue;end
  delta=r/a;newdual=y[row]+delta
  if !isfinite(delta) || !isfinite(newdual);continue;end
  if !(p.lowerrow ? newdual>=-o.dual_tolerance : newdual<=o.dual_tolerance);continue;end
  slot=positions[row];@assert b.basic_indices[slot]==logical
  b.basic_indices[slot]=j;b.states[j]=JS.BASIC;b.states[logical]=p.lowerrow ? JS.AT_LOWER : JS.AT_UPPER
  positions[row]=0;y[row]=newdual
 end
 b,y
end
function chain(metas,groups,basis,y,x,o)
 b=basis
 length(metas)==length(groups) || throw(ArgumentError("incomplete postsolve metadata"))
 all(isfinite,y) && all(isfinite,x) || throw(ArgumentError("nonfinite starting hint"))
 for i in reverse(eachindex(metas))
  meta=metas[i];x=JS._apply_postsolve_step(JS.postsolve_primal,meta.step,x)
  b,y=JS._PostsolveLift.one(meta,b,y,x,o;check_input=false)
  if !isnothing(groups[i])
   b,y=apply(groups[i],b,y,x,o)
  end
 end
 all(isfinite,x) && all(isfinite,y) || throw(ArgumentError("nonfinite restored hint"))
 length(unique(b.basic_indices))==length(y) && all(j->b.states[j]==JS.BASIC,b.basic_indices) || throw(ArgumentError("invalid restored basis"))
 b,y,x
end
end
