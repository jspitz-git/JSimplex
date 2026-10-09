include("paired.jl")
const STEP1=frozen("step1","_pcw1")
const STEP2=frozen("step2","_pcw2")
function compare(name,w)
 fs=(BASELINE,STEP1,STEP2,JS._legacy_primal_point_certified)
 n=3;ts=[Float64[] for _ in fs];bs=[Int[] for _ in fs];ns=[Int[] for _ in fs]
 verdict=BASELINE(w)
 for f in fs;@assert f(w)==verdict;batch(f,w,n);end
 for round in 1:9,k in (isodd(round) ? (1,2,3,4) : (4,3,2,1))
  GC.gc();t=@timed batch(fs[k],w,n);@assert t.compile_time==0
  push!(ts[k],t.time/n);push!(bs[k],t.bytes÷n);push!(ns[k],Base.gc_alloc_count(t.gcstats)÷n)
 end
 r=Dict("name"=>name,"type"=>string(eltype(w.primal)),"verdict"=>verdict,
 "seconds"=>ts,"bytes"=>bs,"allocations"=>ns,"ratios"=>median(ts[1])./median.(ts),"retained_bytes"=>Base.summarysize(w.scratch.primal_point_buffers))
 println(name," ",eltype(w.primal)," ratios=",r["ratios"]," bytes=",median.(bs));flush(stdout);r
end
function stages(out)
 records=[]
 for T in (Float32,Float64),kind in (:fast,:sparse_overlap,:dense_overlap,:consistency_only,:partial_overlap)
  m=kind==:dense_overlap ? 128 : 2048
  A=kind==:fast ? spdiagm(0=>ones(T,m)) : kind==:dense_overlap ? sparse(hcat(fill(T(0.1),m,64),fill(T(-0.1),m,64),ones(T,m))) : sparse(hcat(fill(T(0.1),m),fill(T(-0.1),m),ones(T,m)))
  n=size(A,2);x=kind==:fast ? zeros(T,n) : vcat(fill(T(3),n-1),one(T))
  activity=kind==:fast ? zeros(T,m) : ones(T,m)
  p=LinearProblem(A,zeros(T,n);row_lower=activity,row_upper=activity)
  w=JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=eps(T)^2))
  w.primal[1:n]=x;w.primal[n+1:end]=activity
  if kind in (:consistency_only,:partial_overlap)
   range=kind==:consistency_only ? (1:m) : (1:2:m)
   for i in range;p.row_lower[i]=Bound(T(0));p.row_upper[i]=Bound(T(2));end
  end
  push!(records,compare(string(kind),w))
 end
 for origin in ("primal","dual")
  d=deserialize(".superpowers/primal-certificate-work/capture/medium-"*origin*".bin")
  push!(records,compare("medium-"*origin,restored(d)))
 end
 open(out,"w") do io;TOML.print(io,Dict("arms"=>["baseline","step1","step2","step3"],"cases"=>records));end
end
Base.invokelatest(stages,only(ARGS))
