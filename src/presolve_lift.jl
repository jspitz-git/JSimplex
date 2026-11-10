# Owned postsolve metadata: only columns/row terms needed for reverse reconstruction.
# All changes are hints; the original-model cleanup/certificate remains authoritative.
module _PostsolveLift
const JS=parentmodule(@__MODULE__)
struct ColumnData{T}
 index::Int
 cost::T
 rows::Vector{Int}
 values::Vector{T}
end
struct SingletonData{T}
 col::ColumnData{T}
 lower::JS.Bound{T}
 upper::JS.Bound{T}
end
struct EqualityData{T}
 col::ColumnData{T}
 row::Int
 pivot::T
 reduced_row::Int
 lower::JS.Bound{T}
 upper::JS.Bound{T}
 terms::Vector{Tuple{Int,T}}
 rhs::T
end
struct Metadata{T}
 step::JS.PostsolveStep{T}
 singleton::Vector{SingletonData{T}}
 equality::Vector{EqualityData{T}}
end
mapof(step::JS.PresolveMap)=step
mapof(step)=step.map
function column(p,j)
 range=p.A.colptr[j]:(p.A.colptr[j+1]-1)
 ColumnData(j,p.objective[j],p.A.rowval[range],p.A.nzval[range])
end
function metadata(p::JS.LinearProblem{T},next,pass::Int) where T
 @assert p.objective_sense==JS.MIN_SENSE
 step=only(next.postsolve_stack);ss=SingletonData{T}[];ee=EqualityData{T}[]
 if step isa JS.SingletonRowStep
  for j in eachindex(step.lower_sources)
   isnothing(step.lower_sources[j]) && isnothing(step.upper_sources[j]) && continue
   push!(ss,SingletonData(column(p,j),next.problem.column_lower[j],next.problem.column_upper[j]))
  end
 elseif step isa Union{JS.SingletonEqualityStep,JS.SparseEqualityStep}
  inverse=zeros(Int,size(p.A,1));for (new,old) in enumerate(step.map.rows);inverse[old]=new;end
  for r in step.records
   k=inverse[r.row]
   push!(ee,EqualityData(column(p,r.column),r.row,r.coefficient,k,k==0 ? p.row_lower[r.row] : next.problem.row_lower[k],k==0 ? p.row_upper[r.row] : next.problem.row_upper[k],r.terms,r.rhs))
  end
 elseif step isa JS.DoubletonStep
  r,j=step.equality_row,step.eliminated
  push!(ee,EqualityData(column(p,j),r,p.A[r,j],0,p.row_lower[r],p.row_upper[r],Tuple{Int,T}[],JS.bound_value(p.row_lower[r])))
 end
 Metadata{T}(step,ss,ee)
end
function price(col,y;except=0)
 v=col.cost
 for k in eachindex(col.rows)
  row=col.rows[k];row==except && continue
  v-=col.values[k]*y[row]
 end
 v
end
at(value,b,tol)=isfinite(b) && abs(value-JS.bound_value(b))<=tol
function state_from_price(old,value,lo,hi,price,options)
 old==JS.BASIC && return old
 desired=price>options.dual_tolerance ? JS.AT_LOWER : price < -options.dual_tolerance ? JS.AT_UPPER : old
 desired==JS.AT_LOWER && at(value,lo,options.primal_tolerance) && return desired
 desired==JS.AT_UPPER && at(value,hi,options.primal_tolerance) && return desired
 old
end
# x is already restored to this step's original column coordinates.
function one(meta::Metadata{T},basis,y_reduced::Vector{T},x::Vector{T},options; check_input=true) where T
 step=meta.step
 if step isa JS.InequalityActivationStep
  length(y_reduced)==step.rows && length(x)==step.columns || throw(ArgumentError("dual lift dimensions"))
  check_input && !(all(isfinite,y_reduced) && all(isfinite,x)) && throw(ArgumentError("nonfinite dual lift hint"))
  return JS.restore_basis(step,basis),y_reduced
 end
 map=mapof(step);n=length(map.removed_values);m=map.original_row_count
 length(y_reduced)==length(map.rows) && length(x)==n || throw(ArgumentError("dual lift dimensions"))
 check_input && !(all(isfinite,y_reduced) && all(isfinite,x)) && throw(ArgumentError("nonfinite dual lift hint"))
 y=zeros(T,m);y[map.rows]=y_reduced
 if step isa JS.SingletonRowStep
  restored=JS.restore_basis(map,basis)
  for entry in meta.singleton
   col=entry.col;j=col.index;old=restored.states[j];old==JS.BASIC && continue
   value=price(col,y);isfinite(value) || throw(ArgumentError("nonfinite restored price"))
   state=state_from_price(old,x[j],entry.lower,entry.upper,value,options)
   source=state==JS.AT_LOWER ? step.lower_sources[j] : state==JS.AT_UPPER ? step.upper_sources[j] : nothing
   isnothing(source) && continue
   row,rowstate=source;k=findfirst(==(row),col.rows);isnothing(k) && throw(ArgumentError("missing singleton coefficient"))
   a=col.values[k];iszero(a) && throw(ArgumentError("zero singleton coefficient"))
   y[row]+=value/a;isfinite(y[row]) || throw(ArgumentError("nonfinite singleton dual"))
   @assert restored.basic_indices[row]==n+row
   restored.basic_indices[row]=j;restored.states[j]=JS.BASIC;restored.states[n+row]=rowstate
  end
 else
  chosen=basis
  for e in meta.equality
   # The transformed row multiplier is retained when column bounds became a row.
   y[e.row]+=price(e.col,y;except=e.row)/e.pivot
   isfinite(y[e.row]) || throw(ArgumentError("nonfinite equality dual"))
   e.reduced_row==0 && continue
   index=length(map.columns)+e.reduced_row;old=basis.states[index]
   activity=zero(T);for (j,a) in e.terms;activity+=a*x[j];end
   state=state_from_price(old,activity,e.lower,e.upper,y_reduced[e.reduced_row],options)
   if state!=old
    chosen===basis && (chosen=JS.Basis(basis.basic_indices,basis.states))
    chosen.states[index]=state
   end
  end
  restored=JS.restore_basis(step,chosen)
 end
 return restored,y
end
end
