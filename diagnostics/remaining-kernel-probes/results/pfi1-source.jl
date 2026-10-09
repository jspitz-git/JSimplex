# Diagnostic-only bounds-check elimination on validated, owned eta payloads.
using JSimplex,SparseArrays,LinearAlgebra,Serialization,TOML,Statistics,SHA
const JS=JSimplex
function candidate(name,tag)
 source=read(joinpath(dirname(pathof(JS)),"factorization.jl"),String)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end;sig.args[1]=tag
 function visit(x)
  x isa Expr||return x
  if x.head==:for && x.args[1]==:(index = eachindex(eta.indices))
   return Expr(:macrocall,Symbol("@inbounds"),LineNumberNode(0),x)
  end
  Expr(x.head,map(visit,x.args)...)
 end
 ex.args[2]=visit(ex.args[2]);Core.eval(JS,ex);getfield(JS,tag)
end
const FTRAN=candidate(:forward_solve!,:_probe_eta_forward!)
const BTRAN=candidate(:transpose_solve!,:_probe_eta_transpose!)
function batch(f,y,fac,rhs,n)
 for _ in 1:n;f(y,fac,rhs);end
end
function compare(fac,rhs,mode)
 fs=mode==:ftran ? (JS.forward_solve!,FTRAN) : (JS.transpose_solve!,BTRAN)
 y=similar(rhs);ref=similar(rhs);fs[1](ref,fac,rhs);fs[2](y,fac,rhs);@assert isequal(y,ref)
 for f in fs;batch(f,y,fac,rhs,5);end
 ts=[Float64[],Float64[]];bs=[Int[],Int[]]
 for r in 1:11,k in (isodd(r) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(fs[k],y,fac,rhs,5);@assert t.compile_time==0&&isequal(y,ref)
  push!(ts[k],t.time/5);push!(bs[k],t.bytes÷5)
 end
 Dict("mode"=>string(mode),"seconds"=>ts,"bytes"=>bs,"ratio"=>median(ts[2])/median(ts[1]),"equal"=>true)
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
