using JSimplex,SparseArrays,LinearAlgebra,Random,Serialization,TOML,Statistics
const JS=JSimplex
# Freeze the old generic per-term accumulation inside an otherwise identical
# quality evaluator; the changed specialization is bypassed only in this probe.
let
 source=read(joinpath(@__DIR__,"baseline-quality.txt"),String)
 ex=Meta.parse(source)
 sig=ex.args[1];while sig.head!=:call;sig=sig.args[1];end
 sig.args[1]=:_residual_reference_quality!
 Core.eval(JS,ex)
end
Base.@noinline function batch(f,s,B,x,rhs,policy,transposed,n)
 for i in 1:n
  rhs[1]=isodd(i) ? one(eltype(rhs)) : nextfloat(one(eltype(rhs)))
  Base.donotdelete(f(s,B,x,rhs,policy,transposed))
 end
 nothing
end
function measure(name,B,x,rhs,transposed)
 T=eltype(B);policy=JS.NumericalPolicy(T)
 a=JS.SolveQualityScratch(T,length(rhs));b=deepcopy(a)
 functions=(JS._residual_reference_quality!,JS._compensated_solve_quality!);scratch=(a,b)
 q1=functions[1](a,B,x,rhs,policy,transposed);q2=functions[2](b,B,x,rhs,policy,transposed)
 @assert isequal(q1,q2)
 @assert all(isequal(getfield(a,k),getfield(b,k)) for k in fieldnames(typeof(a)))
 n=10;times=[Float64[],Float64[]];bytes=[Int[],Int[]];allocs=[Int[],Int[]]
 for k in 1:2;batch(functions[k],scratch[k],B,x,rhs,policy,transposed,n);end
 for round in 1:9
  for k in (isodd(round) ? (1,2) : (2,1))
   GC.gc();t=@timed batch(functions[k],scratch[k],B,x,rhs,policy,transposed,n)
   @assert t.compile_time==0
   push!(times[k],t.time/n);push!(bytes[k],t.bytes);push!(allocs[k],Base.gc_alloc_count(t.gcstats))
  end
 end
 Dict("name"=>name,"type"=>string(T),"rows"=>size(B,1),"nnz"=>nnz(sparse(B)),"transposed"=>transposed,"baseline_seconds"=>times[1],"candidate_seconds"=>times[2],"baseline_median"=>median(times[1]),"candidate_median"=>median(times[2]),"speedup"=>median(times[1])/median(times[2]),"baseline_batch_bytes"=>bytes[1],"candidate_batch_bytes"=>bytes[2],"candidate_batch_allocations"=>allocs[2])
end
function main(out)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 rows=[];rng=MersenneTwister(124)
 for T in (Float32,Float64),dense in (false,true),transposed in (false,true)
  n=dense ? 256 : 4000;B=sprand(rng,T,n,n,dense ? 1.0 : 0.002);x=randn(rng,T,n);rhs=ones(T,n)
  push!(rows,measure("synthetic_"*(dense ? "dense_csc" : "sparse"),B,x,rhs,transposed))
 end
 for T in (Float32,Float64)
  n=4000
  for kind in (:empty_columns,:zero_vector,:mostly_zero_vector,:diagonal)
   B=kind==:diagonal ? spdiagm(0=>ones(T,n)) : sprand(rng,T,n,n,kind==:empty_columns ? 0.0001 : 0.002)
   x=randn(rng,T,n)
   kind==:zero_vector && fill!(x,zero(T))
   kind==:mostly_zero_vector && (x[2:end].=zero(T))
   push!(rows,measure(string(kind),B,x,ones(T,n),true))
  end
  B=randn(rng,T,128,128)
  push!(rows,measure("dense_matrix",B,randn(rng,T,128),ones(T,128),true))
 end
 for iteration in (1000,10000,30000,50000)
  d=deserialize(".superpowers/simplex-data-movement/runtime-final-v2/solve/row-0-$(iteration).bin")
  m,n=size(d.A);aug=hcat(d.A,-sparse(I,m,m));B=aug[:,d.basics];rhs=zeros(m);rhs[d.row]=1
  push!(rows,measure("runtime_$(iteration)",B,d.rho,rhs,true))
 end
 d=deserialize(".superpowers/dual-allocation-cost/census/cost-medium.toml-state-0-1000.bin")
 m,n=size(d.problem.A);B=hcat(d.problem.A,-sparse(I,m,m))[:,d.basics]
 push!(rows,measure("medium_basis_random_vector",B,randn(rng,m),ones(m),true))
 open(out,"w") do io;TOML.print(io,Dict("cases"=>rows));end
 for r in rows;println(r["name"]," ",r["type"]," transpose=",r["transposed"]," speedup=",r["speedup"]);end
end
Base.invokelatest(main,only(ARGS))
