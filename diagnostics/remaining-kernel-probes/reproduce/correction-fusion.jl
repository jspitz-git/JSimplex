# Throwaway fusion probe. Correction validation remains before trial mutation.
using JSimplex,Serialization,Random,Statistics,TOML,LinearAlgebra,SparseArrays,SHA
function baseline!(trial,correction)
 all(isfinite,correction)||return false
 for i in eachindex(trial);trial[i]+=correction[i];end
 all(isfinite,trial)
end
function fused!(trial,correction)
 all(isfinite,correction)||return false
 finite=true
 for i in eachindex(trial)
  value=trial[i]+correction[i];trial[i]=value;finite&=isfinite(value)
 end
 finite
end
function batch(f,trial,correction,initial,n)
 for _ in 1:n;copyto!(trial,initial);Base.donotdelete(f(trial,correction));end
end
function compare(name,initial,correction)
 trial=copy(initial);ref=copy(initial)
 @assert baseline!(ref,correction)==fused!(trial,correction)&&isequal(ref,trial)
 fs=(baseline!,fused!);ts=[Float64[],Float64[]];bs=[Int[],Int[]]
 for f in fs;batch(f,trial,correction,initial,10);end
 for r in 1:13,k in (isodd(r) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(fs[k],trial,correction,initial,20);@assert t.compile_time==0
  push!(ts[k],t.time/20);push!(bs[k],t.bytes÷20)
 end
 Dict("name"=>name,"type"=>string(eltype(trial)),"n"=>length(trial),"seconds"=>ts,"bytes"=>bs,"ratio"=>median(ts[2])/median(ts[1]),"equal"=>true)
end
function actual_medium(origin)
 path="/home/jspitz/.codex/worktrees/basis-update-chain-bench/JSimplex.jl/.superpowers/medium-hh-main/"*origin*"/attempt-1/reports/certification-first.bin"
 d=deserialize(path);m,n=size(d.problem.A)
 f=JSimplex.HuangfuHallFactorization{Float64,Nothing,:native}(d.factor_base,copy(d.factor_updates),zeros(m),zeros(m),zeros(m),zeros(m),false,nothing,JSimplex.HHUnitWorkspace(m,Float64),length(d.factor_updates),JSimplex.HHPool(Float64),JSimplex.HHPool(Float64),JSimplex.HHExtractWorkspace())
 A=d.problem.A;B=hcat(A,spdiagm(0=>-ones(m)))[:,d.basis.basic_indices]
 p=clamp(d.selected_row,1,m);rhs=zeros(m);rhs[p]=1
 trial=copy(d.rho);scratch=JSimplex.SolveQualityScratch(Float64,m);policy=JSimplex.NumericalPolicy(Float64,d.options)
 quality=JSimplex._compensated_solve_quality!(scratch,B,trial,rhs,policy,true)
 @assert !isnothing(quality)&&quality.finite
 c=zeros(m);JSimplex.transpose_solve!(c,f,scratch.residual)
 r=compare("medium-"*origin*"-native-btran-correction",trial,c)
 r["snapshot_sha256"]=bytes2hex(open(sha256,path));r["correction_nonzeros"]=count(!iszero,c);r["correction_norm"]=norm(c,Inf)
 r
end

function main(out)
 records=[];rng=MersenneTwister(991)
 for T in (Float32,Float64),n in (2048,12000,360982),density in (0.01,1.0)
  a=randn(rng,T,n);c=randn(rng,T,n);c[rand(rng,n).>density].=zero(T)
  push!(records,compare("synthetic-density-"*string(density),a,c))
  for i in (1,n÷2,n),value in (T(Inf),T(NaN),floatmax(T),-zero(T))
   b=copy(a);b[i]=value;d=copy(c);d[i]=value;x=copy(b);y=copy(b)
   @assert baseline!(x,d)==fused!(y,d)&&isequal(x,y)
  end
 end
 for origin in ("primal","dual");push!(records,actual_medium(origin));GC.gc(true);end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
 for r in records;println(r["type"]," ",r["n"]," ",r["name"]," ratio=",r["ratio"]);end
end
main(only(ARGS))
