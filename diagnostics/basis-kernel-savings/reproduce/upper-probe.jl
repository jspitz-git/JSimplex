# Process-local experiment; no production upper method is edited.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,TOML,Statistics,SHA
const JS=JSimplex
@eval JS const _upper_probe_candidate=Ref(false)
function install(name,file)
 source=read(joinpath(@__DIR__,file*".baseline"),String)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 original=deepcopy(ex.args[2]);changed=Ref(0)
 function visit(x)
  x isa Expr||return x
  if x.head==:for && x.args[1] in (:(index=eachindex(column.indices)),:(slot=eachindex(ids)))
   changed[]+=1;index=x.args[1].args[1]
   ids=index==:index ? :(column.indices) : :ids
   diagonal=index==:index ? :column_index : :diagonal
   statements=filter(s->!(s isa Expr && occursin("continue",string(s))),x.args[2].args)
   fast=Expr(:for,Expr(:(=),index,:(1:(length($ids)-1))),Expr(:block,statements...))
   return Expr(:if,:(!isempty($ids) && $ids[end]==$diagonal),fast,x)
  end
  Expr(x.head,map(visit,x.args)...)
 end
 candidate=visit(original);@assert changed[]==1
 ex.args[2]=quote
  if _upper_probe_candidate[];$candidate;else;$original;end
 end
 Core.eval(JS,ex)
end
for (name,file) in ((:_upper_backsolve!,"triangular_factorization.jl"),(:_upper_transpose_solve!,"triangular_factorization.jl"),(:_stable_upper_backsolve_physical!,"triangular_indices.jl"),(:_stable_upper_transpose_solve!,"triangular_indices.jl"));install(name,file);end
function batch(f,y,fac,rhs,n,enabled)
 JS._upper_probe_candidate[]=enabled
 for _ in 1:n;f(y,fac,rhs);end
end
function compare(fac,rhs,mode)
 f=mode==:ftran ? JS._ordinary_forward_solve! : JS.transpose_solve!
 y=similar(rhs);ref=similar(rhs)
 batch(f,ref,fac,rhs,1,false);batch(f,y,fac,rhs,1,true);@assert isequal(ref,y)
 for flag in (false,true);batch(f,y,fac,rhs,5,flag);end
 estimate=@elapsed batch(f,y,fac,rhs,5,false);count=clamp(ceil(Int,0.01/max(estimate/5,1e-9)),5,10000)
 ts=[Float64[],Float64[]];bs=[Int[],Int[]]
 for round in 1:11,k in (isodd(round) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(f,y,fac,rhs,count,k==2);@assert t.compile_time==0 && isequal(y,ref)
  push!(ts[k],t.time/count);push!(bs[k],t.bytes÷count)
 end
 JS._upper_probe_candidate[]=false
 Dict("mode"=>string(mode),"seconds"=>ts,"bytes"=>bs,"ratio"=>median(ts[2])/median(ts[1]),"equal"=>true)
end
function main(out)
 rows=[]
 for history in ("runtime-40000","fast0507-1000")
  path="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories/"*history*".bin"
  d=deserialize(path);A=hcat(d.A,spdiagm(0=>-ones(size(d.A,1))))
  for (name,F) in (("ft",JS.ForrestTomlinFactorization),("ss",JS.SuhlSuhlFactorization),("bg",JS.BartelsGolubFactorization))
   f=F(A[:,d.basis]);rhs=zeros(size(A,1));direction=similar(rhs)
   for k in 0:320
    if k>0
     row,col=d.steps[k];fill!(rhs,0);for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
     JS.forward_solve!(direction,f,rhs);JS.replace_column!(f,direction,row;zero_tolerance=SolverOptions().zero_tolerance)
    end
    k in (0,80,320)||continue
    row,col=d.steps[k+1]
    for mode in (:ftran,:btran),kind in (:actual,:dense)
     fill!(rhs,0)
     if kind==:dense;rhs .= sin.(Float64.(eachindex(rhs)))
     elseif mode==:ftran;for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
     else;rhs[row]=1;end
     r=compare(f,rhs,mode);merge!(r,Dict("history"=>history,"manager"=>name,"chain"=>k,"rhs"=>string(kind)));push!(rows,r)
     println(history," ",name," ",k," ",mode," ",kind," ratio=",r["ratio"]);flush(stdout)
     open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
    end
   end
  end
 end
end
Base.invokelatest(main,only(ARGS))
