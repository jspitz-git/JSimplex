using JSimplex, SparseArrays, LinearAlgebra, Serialization, TOML, Statistics, Random, Logging, SHA
const JS=JSimplex
const NAMES=(:_native_primal_rows_filter,:_refined_primal_rows_feasible,
 :_legacy_primal_point_certified,:_legacy_primal_model_feasible,
 :_legacy_primal_row_consistent,:_primal_feasible_with_bounds)
function frozen(suffix,tag)
 for (name,file) in zip(NAMES,("primal_row_certification.jl","primal_row_certification.jl",
  "legacy_primal_point.jl","legacy_primal_point.jl","legacy_primal_point.jl","dual_simplex.jl"))
  source=read(joinpath(@__DIR__,file*"."*suffix),String)
  ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
  rename(x::Symbol)=x in NAMES ? Symbol(tag,x) : x
  rename(x::Expr)=Expr(x.head,map(rename,x.args)...)
  rename(x)=x
  Core.eval(JS,rename(ex))
 end
 Base.invokelatest(getfield,JS,Symbol(tag,:_legacy_primal_point_certified))
end
const BASELINE=frozen("baseline","_pcw0")
Base.@noinline function batch(f,w,n)
 for _ in 1:n;Base.donotdelete(f(w));end
end
function measure(name,w)
 fs=(BASELINE,JS._legacy_primal_point_certified)
 @assert fs[1](w)==fs[2](w)
 n=5;times=[Float64[],Float64[]];bytes=[Int[],Int[]];allocs=[Int[],Int[]]
 for f in fs;batch(f,w,n);end
 for round in 1:9,k in (isodd(round) ? (1,2) : (2,1))
  GC.gc();t=@timed batch(fs[k],w,n);@assert t.compile_time==0
  push!(times[k],t.time/n);push!(bytes[k],t.bytes÷n);push!(allocs[k],Base.gc_alloc_count(t.gcstats)÷n)
 end
 @assert fs[1](w)==fs[2](w)
 r=Dict("name"=>name,"type"=>string(eltype(w.primal)),"rows"=>size(w.problem.A,1),"columns"=>size(w.problem.A,2),"verdict"=>fs[2](w),"seconds"=>times,"bytes"=>bytes,"allocations"=>allocs,"speedup"=>median(times[1])/median(times[2]),"retained_buffers_bytes"=>Base.summarysize(w.scratch.primal_point_buffers))
 println(name," ratio=",r["speedup"]," bytes=",median.(bytes));flush(stdout)
 r
end
function restored(d)
 w=JS._initialize_workspace_state(d.problem,d.options)
 for (a,b) in ((w.primal,d.primal),(w.lower,d.lower),(w.upper,d.upper),(w.reduced_costs,d.reduced),(w.costs,d.costs),(w.pricing_weights,d.weights))
  copyto!(a,b)
 end
 w
end
function captured(origin,out)
 d=deserialize("/home/jspitz/.codex/worktrees/simplex-certificate-repair/JSimplex.jl/.superpowers/certificate-repair/medium-"*origin*"-handoff.bin")
 options=JS._remaining_options(d.options;iterations=d.options.iteration_limit-(d.iterations+32),time_limit=Inf)
 latest=Ref{Any}(nothing)
 diag=JS.SimplexDiagnostics(;observer=(event,w)->(latest[]=w;nothing))
 ctx=JS.SolveContext(time_ns(),Inf,diag,JS.NumericalPolicy(Float64,options))
 r=with_logger(NullLogger()) do
  JS.cleanup_original(d.problem,d.basis,options,ctx,d.iterations,d.refactorizations;target_primal=d.target_primal)
 end
 @assert r.status==ITERATION_LIMIT
 w=latest[];@assert !JS._has_active_bound_perturbations(w.scratch.perturbations)
 data=(problem=w.problem,options=w.options,primal=w.primal,lower=w.lower,upper=w.upper,reduced=w.reduced_costs,costs=w.costs,weights=w.pricing_weights)
 serialize(out,data)
 w
end
function main(out,mode)
 @assert Threads.nthreads()==BLAS.get_num_threads()==1
 records=[]
 for T in (Float32,Float64),kind in (:fast,:fallback,:dense)
  m=kind==:dense ? 256 : 2048
  A=kind==:fallback ? sparse(repeat(collect(1:m),3),vcat(fill(1,m),fill(2,m),fill(3,m)),vcat(fill(T(0.1),m),fill(T(-0.1),m),ones(T,m)),m,3) : kind==:fast ? spdiagm(0=>ones(T,m)) : sparse(rand(MersenneTwister(819),T,m,m))
  n=size(A,2);x=kind==:fallback ? T[3,3,1] : zeros(T,n);activity=A*x
  p=LinearProblem(A,zeros(T,n);row_lower=activity,row_upper=activity)
  w=JS._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,primal_tolerance=eps(T)^2))
  w.primal[1:n]=x;w.primal[n+1:end]=activity
  push!(records,measure(string(kind),w))
 end
 for origin in ("primal","dual")
  file=".superpowers/primal-certificate-work/capture/medium-"*origin*".bin"
  w=mode=="capture" ? captured(origin,file) : restored(deserialize(file))
  push!(records,measure("medium-"*origin,w));GC.gc()
  open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
 end
end
abspath(PROGRAM_FILE)==(@__FILE__) && Base.invokelatest(main,ARGS...)
