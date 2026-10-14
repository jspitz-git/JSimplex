using SparseArrays
function zero_fixture(count; old=0.0,multiplier=2.0,term=3.0,explicit=false)
 odd=collect(1:2:2count);even=odd .+ 1
 rows=vcat(odd,odd,even);cols=vcat(odd,even,odd);values=vcat(fill(2.0,count),fill(term,count),fill(2multiplier,count))
 if explicit || !iszero(old);append!(rows,even);append!(cols,even);append!(values,fill(old,count));end
 LinearProblem(sparse(rows,cols,values,2count,2count),repeat([0.0,2.0],count);objective_constant=7.0,
  row_lower=Union{Nothing,Float64}[isodd(i) ? 5.0 : nothing for i in 1:2count],
  row_upper=[isodd(i) ? 5.0 : 20.0 for i in 1:2count],
  column_lower=Union{Nothing,Float64}[isodd(i) ? 1.0 : nothing for i in 1:2count],
  column_upper=Union{Nothing,Float64}[isodd(i) ? 3.0 : nothing for i in 1:2count])
end
function identical(a,b)
 typeof(a)===typeof(b) || return false
 if a isa BigFloat
  return isequal(a,b) && precision(a)==precision(b)
 elseif a isa Union{Number,AbstractString,Symbol,Enum,Nothing}
  return isequal(a,b)
 elseif a isa SparseMatrixCSC
  return size(a)==size(b) && identical(a.colptr,b.colptr) && identical(a.rowval,b.rowval) && identical(a.nzval,b.nzval)
 elseif a isa AbstractArray
  size(a)==size(b) || return false
  return all(identical(a[i],b[i]) for i in eachindex(a,b))
 else
  return all(identical(getfield(a,i),getfield(b,i)) for i in 1:fieldcount(typeof(a)))
 end
end
function input_owners(p)
 Any[p.A,p.A.colptr,p.A.rowval,p.A.nzval,(getfield(p,f) for f in fieldnames(typeof(p)) if getfield(p,f) isa AbstractArray && f!=:A)...]
end
function input_preserved(p,original,owners)
 now=input_owners(p)
 identical(p,original) && length(now)==length(owners) && all(a===b for (a,b) in zip(now,owners))
end
metrics(t)=Dict{String,Any}("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),"gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function save_record(out,name,x)
 path=joinpath(out,name);ispath(path)&&error("existing output")
 open(path,"w") do io;TOML.print(io,x);flush(io);end
end
function paired_case(out,name,p,reference,candidate;warm=3,samples=8)
 original=deepcopy(p);owners=input_owners(p);saved=Any[]
 for pair in 1:(warm+samples)
  order=isodd(pair) ? (("reference",reference),("candidate",candidate)) : (("candidate",candidate),("reference",reference))
  results=Any[];records=Dict{String,Any}()
  for (side,f) in order
   GC.gc()
   t=@timed f(p)
   push!(results,t.value);records[side]=metrics(t)
  end
  equal=identical(results[1],results[2]);preserved=input_preserved(p,original,owners)
  record=Dict("pair"=>pair,"warm"=>pair<=warm,"equal"=>equal,"preserved"=>preserved,"metrics"=>records)
  save_record(out,name*"-"*string(pair)*".toml",record)
  equal && preserved || error("result/input mismatch "*name)
  if pair>warm
   all(records[s]["compile_seconds"]==0 && records[s]["recompile_seconds"]==0 for s in ("reference","candidate")) || error("measured compilation "*name)
   push!(saved,record)
  end
 end
 saved
end
