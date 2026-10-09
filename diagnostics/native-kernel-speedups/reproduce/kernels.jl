using JSimplex, SparseArrays, Random, Statistics, TOML, Test
const JS=JSimplex
Base.include(JS,joinpath(@__DIR__,"baseline-kernels.jl"))
include(joinpath(@__DIR__,"../../../test/primal_certificate_reuse_tests.jl"))
function workspace(T,m,n)
 rng=MersenneTwister(17);I=Int[];J=Int[];V=T[]
 for j in 1:n,k in 0:11
  push!(I,mod1(j+137k,m));push!(J,j);push!(V,T(rand(rng,(-1,1)))/T(16))
 end
 p=LinearProblem(sparse(I,J,V,m,n),zeros(T,n);row_lower=fill(T(-100),m),row_upper=fill(T(100),m))
 ws=JS.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
 ws.primal[1:n].=one(T);ws.primal[n+1:end].=p.A*ones(T,n)
 return ws
end
function measure(f,repetitions)
 f();GC.gc(); t=@timed for _ in 1:repetitions;f();end
 (;seconds=t.time/repetitions,bytes=t.bytes/repetitions,compilation=t.compile_time)
end
function main(out)
 records=[]
 for T in (Float32,Float64)
  ws=workspace(T,2048,4096);m,n=size(ws.problem.A)
  rho=randn(MersenneTwister(1),T,m);direction=randn(MersenneTwister(2),T,m)
  rhs=randn(MersenneTwister(3),T,m);prices=copy(ws.reduced_costs);ref=copy(prices)
  # Exercise structural basis columns, row columns, signed zeros and nonfinite data.
  ws.basis.basic_indices[1:div(m,2)].=1:div(m,2)
  for value in (zero(T),-zero(T),one(T),T(Inf),T(NaN))
   rho[1]=value
   @test isequal(JS._dual_row_residual_ratio(ws,rho,2),JS._baseline_row_residual(ws,rho,2))
   copyto!(ws.scratch.row_rhs,rhs);a=JS._dual_direction_residual_ok!(ws,direction,T(.25));r=copy(ws.scratch.tau);sc=copy(ws.scratch.row_rhs)
   copyto!(ws.scratch.row_rhs,rhs);b=JS._baseline_direction_residual!(ws,direction,T(.25))
   @test a==b && isequal(r,ws.scratch.tau) && isequal(sc,ws.scratch.row_rhs)
   JS._recompute_reduced_costs!(prices,ws,rho);JS._baseline_reduced_costs!(ref,ws,rho)
   @test isequal(prices,ref)
  end
  rho[1]=one(T)
  for value in (zero(T),-zero(T),one(T),T(Inf),T(-Inf),T(NaN)), operand in (:direction,:rhs)
   saved = operand==:direction ? direction[1] : rhs[1]
   operand==:direction ? (direction[1]=value) : (rhs[1]=value)
   copyto!(ws.scratch.row_rhs,rhs);a=JS._dual_direction_residual_ok!(ws,direction,T(.25));r=copy(ws.scratch.tau);sc=copy(ws.scratch.row_rhs)
   copyto!(ws.scratch.row_rhs,rhs);b=JS._baseline_direction_residual!(ws,direction,T(.25))
   @test a==b && isequal(r,ws.scratch.tau) && isequal(sc,ws.scratch.row_rhs)
   operand==:direction ? (direction[1]=saved) : (rhs[1]=saved)
  end
  funcs=[("certificate",()->separate_primal_point_certificate(ws),()->JS._legacy_primal_point_certified(ws),30),
   ("row_residual",()->JS._baseline_row_residual(ws,rho,2),()->JS._dual_row_residual_ratio(ws,rho,2),300),
   ("direction_residual",()->(copyto!(ws.scratch.row_rhs,rhs);JS._baseline_direction_residual!(ws,direction,T(.25))),()->(copyto!(ws.scratch.row_rhs,rhs);JS._dual_direction_residual_ok!(ws,direction,T(.25))),300),
   ("reduced_costs",()->JS._baseline_reduced_costs!(ref,ws,rho),()->JS._recompute_reduced_costs!(prices,ws,rho),300),
   ("direction_weight",()->JS._baseline_direction_weight(direction),()->JS._primal_direction_weight(direction),300)]
  for (name,old,new,reps) in funcs
   for batch in 1:7,mode in (isodd(batch) ? (false,true) : (true,false))
    t=measure(mode ? new : old,reps)
    push!(records,Dict("type"=>string(T),"kernel"=>name,"new"=>mode,"batch"=>batch,"seconds"=>t.seconds,"bytes"=>t.bytes,"compile_seconds"=>t.compilation))
   end
  end
 end
 open(out,"w") do io;TOML.print(io,Dict("samples"=>records));end
 for typ in ("Float32","Float64"), k in unique(r["kernel"] for r in records)
  old=filter(r->r["type"]==typ&&r["kernel"]==k&&!r["new"],records);new=filter(r->r["type"]==typ&&r["kernel"]==k&&r["new"],records)
  println(typ," ",k," ratio=",median(r["seconds"] for r in new)/median(r["seconds"] for r in old)," bytes=",median(r["bytes"] for r in old)," => ",median(r["bytes"] for r in new))
 end
end
main(ARGS[1])
