# Paired original PFI methods versus the production methods.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,TOML,Statistics,SHA
const JS=JSimplex
function baseline(name,tag)
 source=read(joinpath(@__DIR__,"factorization.jl.baseline"),String)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end;sig.args[1]=tag
 Core.eval(JS,ex);getfield(JS,tag)
end
const FTRAN=baseline(:forward_solve!,:_baseline_eta_forward!)
const BTRAN=baseline(:transpose_solve!,:_baseline_eta_transpose!)
function batch(f,y,fac,rhs,n)
 for _ in 1:n;f(y,fac,rhs);end
end
function compare(fac,rhs,mode)
 fs=mode==:ftran ? (FTRAN,JS.forward_solve!) : (BTRAN,JS.transpose_solve!)
 y=similar(rhs);ref=similar(rhs);fs[1](ref,fac,rhs);fs[2](y,fac,rhs);@assert isequal(y,ref)
 for f in fs;batch(f,y,fac,rhs,5);end
 estimate=@elapsed batch(fs[1],y,fac,rhs,5)
 count=clamp(ceil(Int,0.01/max(estimate/5,1e-9)),5,10000)
 ts=[Float64[],Float64[]];bs=[Int[],Int[]]
 for r in 1:11,k in (isodd(r) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(fs[k],y,fac,rhs,count);@assert t.compile_time==0&&isequal(y,ref)
  push!(ts[k],t.time/count);push!(bs[k],t.bytes÷count)
 end
 Dict("mode"=>string(mode),"batch_count"=>count,"seconds"=>ts,"bytes"=>bs,"ratio"=>median(ts[2])/median(ts[1]),"equal"=>true)
end
function main(out)
 rows=[]
 for history in ("runtime-40000","fast0507-1000")
  file="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/basis-chain-cost/histories/"*history*".bin"
  d=deserialize(file);A=hcat(d.A,spdiagm(0=>-ones(size(d.A,1))));basis=copy(d.basis);f=JS.PFIFactorization(A[:,basis]);rhs=zeros(length(basis));v=similar(rhs)
  for k in 0:320
   if k>0
    row,col=d.steps[k];fill!(rhs,0);for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
    JS.forward_solve!(v,f,rhs);JS.replace_column!(f,v,row;zero_tolerance=SolverOptions().zero_tolerance);basis[row]=col
   end
   k in (0,80,320)||continue
   @assert all(t->length(t.indices)==length(t.values)&&all(i->1<=i<=length(rhs),t.indices),f.updates)
   row,col=d.steps[k+1]
   for mode in (:ftran,:btran),kind in (:actual,:dense)
    fill!(rhs,0)
    if kind==:dense;rhs .= sin.(Float64.(eachindex(rhs)))
    elseif mode==:ftran;for p in nzrange(A,col);rhs[A.rowval[p]]=A.nzval[p];end
    else;rhs[row]=1;end
    r=compare(f,rhs,mode);r["history"]=history;r["chain"]=k;r["rhs"]=string(kind);push!(rows,r)
    println(history," ",k," ",mode," ",kind," ratio=",r["ratio"]);flush(stdout)
   end
  end
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
end
Base.invokelatest(main,only(ARGS))
