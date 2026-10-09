# Diagnostic only: compact update indices without changing ordered arithmetic.
# The temporary compact records share coefficients; no production layout changes.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,TOML,Statistics
const JS=JSimplex
@eval JS struct HHCompactProbe{T}
 u_indices::Vector{Int32};u_values::Vector{T}
 v_indices::Vector{Int32};v_values::Vector{T};pivot::T
end
source=read(joinpath(dirname(pathof(JS)),"huangfu_hall_factorization.jl"),String)
ex,_=Meta.parse(source,first(findfirst("@inline function _hh_apply!",source)))
function substitute(x)
 x isa Symbol && return x==:HHUpdate ? :HHCompactProbe : x
 x isa Expr ? Expr(x.head,map(substitute,x.args)...) : x
end
Core.eval(JS,substitute(ex))
for (name,tag) in ((:_hh_forward!,:_compact_probe_forward!),(:transpose_solve!,:_compact_probe_transpose!))
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end
 sig.args[1]=tag;push!(sig.args,:updates)
 function visit(x)
  x == :(f.updates) && return :updates
  x isa Expr ? Expr(x.head,map(visit,x.args)...) : x
 end
 ex.args[2]=visit(ex.args[2]);Core.eval(JS,ex)
end
function batch(y,f,rhs,updates,n,mode)
 for _ in 1:n
  if mode==:ftran;JS._compact_probe_forward!(y,f,rhs,false,updates)
  else;JS._compact_probe_transpose!(y,f,rhs,updates);end
 end
end
compact(f)=[JS.HHCompactProbe(Int32.(t.u_indices),t.u_values,Int32.(t.v_indices),t.v_values,t.pivot) for t in f.updates]
function main(out)
 rows=[]
 for history in ("runtime-40000","fast0507-1000")
  path="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories/"*history*".bin"
  d=deserialize(path);A=hcat(d.A,spdiagm(0=>-ones(size(d.A,1))));f=JS.HuangfuHallFactorization(A[:,d.basis]);rhs=zeros(size(A,1));y=similar(rhs)
  for k in 0:320
   if k>0
    row,col=d.steps[k];fill!(rhs,0);for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
    JS.forward_solve!(y,f,rhs);JS.replace_column!(f,y,row;zero_tolerance=SolverOptions().zero_tolerance)
   end
   k in (0,80,320)||continue
   compact(f);prep=@timed compact(f);alternatives=(f.updates,prep.value)
   index_count=sum(t->length(t.u_indices)+length(t.v_indices),f.updates;init=0)
   row,col=d.steps[k+1]
   for mode in (:ftran,:btran),kind in (:actual,:dense)
    fill!(rhs,0)
    if kind==:dense;rhs .= sin.(Float64.(eachindex(rhs)))
    elseif mode==:ftran;for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
    else;rhs[row]=1;end
    ref=similar(rhs);batch(ref,f,rhs,alternatives[1],1,mode)
    for u in alternatives;batch(y,f,rhs,u,5,mode);@assert isequal(y,ref);end
    estimate=@elapsed batch(y,f,rhs,alternatives[1],5,mode)
    count=clamp(ceil(Int,0.01/max(estimate/5,1e-9)),5,10000)
    ts=[Float64[],Float64[]];bs=[Int[],Int[]]
    for round in 1:11,i in (isodd(round) ? (1,2) : (2,1))
     GC.gc();t=@timed batch(y,f,rhs,alternatives[i],count,mode)
     @assert t.compile_time==0 && isequal(y,ref)
     push!(ts[i],t.time/count);push!(bs[i],t.bytes÷count)
    end
    r=Dict("history"=>history,"chain"=>k,"mode"=>string(mode),"rhs"=>string(kind),"equal"=>true,
     "seconds"=>ts,"bytes"=>bs,"ratio"=>median(ts[2])/median(ts[1]),
     "index_count"=>index_count,"compact_index_bytes"=>4index_count,"original_index_bytes"=>8index_count,
     "conversion_seconds"=>prep.time,"conversion_bytes"=>prep.bytes)
    push!(rows,r);println(history," ",k," ",mode," ",kind," ratio=",r["ratio"]);flush(stdout)
    open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
   end
  end
 end
end
Base.invokelatest(main,only(ARGS))
