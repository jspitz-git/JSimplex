using JSimplex,Test,SparseArrays,Random,Statistics,TOML
const JS=JSimplex
# Freeze pre-change code, including the old activity materialization.
source=read(joinpath(@__DIR__,"point-baseline.txt"),String)
for name in (:_legacy_primal_row_consistent,:_legacy_primal_point_certified)
 ex,_=Meta.parse(source,first(findfirst("function "*string(name)*"(",source)))
 function rename(x)
  x isa Symbol && return x in (:_legacy_primal_row_consistent,:_legacy_primal_point_certified) ? Symbol(:_movement_baseline_,x) : x
  x isa Expr && return Expr(x.head,map(rename,x.args)...)
  x
 end
 Core.eval(JS,rename(ex))
end
function sample(f,w,reps)
 f(w);GC.gc()
 @timed for i in 1:reps
  # Structural zero with alternating sign leaves this test point feasible,
  # while ensuring each call observes current storage.
  w.primal[1]=isodd(i) ? 0.0 : -0.0
  Base.donotdelete(f(w))
 end
end
function main(out)
 records=[]
 for T in (Float32,Float64), (n,density) in ((2048,0.002),(32768,0.0001),(512,1.0))
  T===Float32 && n>2048 && continue
  rng=MersenneTwister(443);A=sprand(rng,T,n,n,density)
  p=LinearProblem(A,zeros(T,n);row_lower=fill(T(-1),n),row_upper=ones(T,n))
  w=JS.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
  old=JS._movement_baseline__legacy_primal_point_certified;new=JS._legacy_primal_point_certified
  @test old(w) && new(w)
  times=[Float64[],Float64[]];allocs=[Float64[],Float64[]];reps=20
  for round in 1:9
   for k in (isodd(round) ? (1,2) : (2,1))
    t=sample(k==1 ? old : new,w,reps);@assert t.compile_time==0
    push!(times[k],t.time/reps);push!(allocs[k],t.bytes/reps)
   end
  end
  # Actual independent arithmetic reference for repeated current values.
  for _ in 1:12
   w.primal .= randn(rng,T,length(w.primal))
   @test old(w)==new(w)
  end
  push!(records,Dict("type"=>string(T),"dimension"=>n,"nonzeros"=>nnz(A),"density"=>density,"old_seconds"=>times[1],"new_seconds"=>times[2],"old_bytes"=>allocs[1],"new_bytes"=>allocs[2],"ratio"=>median(times[2])/median(times[1]),"retained_numeric_bytes"=>sizeof(T)*3n))
  open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
  println(T," ",n," ratio=",records[end]["ratio"]," bytes ",median(allocs[1])," -> ",median(allocs[2]));flush(stdout)
 end
 open(out,"w") do io;TOML.print(io,Dict("cases"=>records));end
end
main(only(ARGS))
