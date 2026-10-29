using Test, SparseArrays, LinearAlgebra, Random, Statistics, TOML
const D=@__DIR__
const W=normpath(joinpath(D,"../../.."))
module Original
using SparseArrays,LinearAlgebra,Logging
include(joinpath(Main.W,"src/numeric.jl"))
include(joinpath(Main.W,"src/options.jl"))
include(joinpath(Main.D,"magnitude-helper.jl"))
include(joinpath(Main.D,"original.jl"))
end
module A
using SparseArrays,LinearAlgebra,Logging
include(joinpath(Main.W,"src/numeric.jl"))
include(joinpath(Main.W,"src/options.jl"))
include(joinpath(Main.D,"magnitude-helper.jl"))
include(joinpath(Main.D,"finite-helper.jl"))
include(joinpath(Main.D,"A.jl"))
end
module B
using SparseArrays,LinearAlgebra,Logging
include(joinpath(Main.W,"src/numeric.jl"))
include(joinpath(Main.W,"src/options.jl"))
include(joinpath(Main.D,"magnitude-helper.jl"))
include(joinpath(Main.D,"B-reviewed.jl"))
end
module AB
using SparseArrays,LinearAlgebra,Logging
include(joinpath(Main.W,"src/numeric.jl"))
include(joinpath(Main.W,"src/options.jl"))
include(joinpath(Main.D,"magnitude-helper.jl"))
include(joinpath(Main.D,"finite-helper.jl"))
include(joinpath(Main.D,"AB-reviewed.jl"))
end
const MODULES=(Original,A,B,AB)
fields(v)=Tuple(getfield(v,k) for k in fieldnames(typeof(v)))
function check_case(matrix,x,rhs,transposed)
    inputs=deepcopy((matrix,x,rhs));reference=nothing
    for M in MODULES
        s=M.SolveQualityScratch(eltype(x),length(rhs));p=M.NumericalPolicy(eltype(x))
        outcome=try (:ok,fields(M.solve_quality!(s,matrix,x,rhs,p;transposed))) catch e;(:error,typeof(e));end
        @test outcome[1] === :ok
        current=(outcome,deepcopy(fields(s)))
        if isnothing(reference);reference=current;else;@test isequal(current,reference);end
        @test isequal((matrix,x,rhs),inputs)
    end
end
function check_components(matrix,x,rhs)
    expected=nothing
    for M in MODULES
        s=M.SolveQualityScratch(eltype(x),length(rhs))
        outcome=try (:ok,M._quality_components!(s.work_residual,s.work_scale,s.terms,matrix,x,rhs,true)) catch e;(:error,typeof(e));end
        current=(outcome,deepcopy(fields(s)))
        if isnothing(expected);expected=current;else;@test isequal(current,expected);end
    end
end
function correctness()
 @testset "Whole native quality equivalence" begin
  rng=MersenneTwister(517)
  for T in (Float32,Float64), (m,n) in ((0,0),(1,1),(7,11),(13,5)), density in (0.0,0.2,1.0), t in (false,true)
   mat=sprand(rng,T,m,n,density);x=randn(rng,T,t ? m : n);rhs=randn(rng,T,t ? n : m)
   check_case(mat,x,rhs,t);check_case(Matrix(mat),x,rhs,t)
  end
  for T in (Float32,Float64)
   edge=T[0,-0.0,nextfloat(zero(T)),-nextfloat(zero(T)),floatmin(T),1,-1,floatmax(T),Inf,-Inf,NaN]
   for v in edge, z in edge, t in (false,true)
    mat=sparse([1,2,1,2],[1,1,2,2],T[v,1,-1,v],2,2)
    check_case(mat,T[z,1],T[1,-0.0],t)
   end
   mat=sparse(T[1 0;0 1]);x=T[1,2];rhs=copy(x)
   for M in MODULES
    s=M.SolveQualityScratch(T,2);p=M.NumericalPolicy(T)
    @test_throws ArgumentError M.solve_quality!(s,mat,s.work_residual,rhs,p)
    @test_throws DimensionMismatch M.solve_quality!(s,mat,T[1],rhs,p)
    @test !M.solve_quality!(s,mat,T[1,3],rhs,p).reliable
    @test M.solve_quality!(s,mat,x,rhs,p).reliable
    # Views keep generic array behavior, including nonfinite endpoints.
    @test M.solve_quality!(s,mat,view(x,:),view(rhs,:),p).reliable
   end
   broken=SparseMatrixCSC(2,2,[1,3,4],[1,3,2],T[1,1,1])
   check_components(broken,T[1,2],T[0,0])
   for M in (B,AB)
    @test !M._quality_local_terms_eligible(zeros(T,2),zeros(T,2),mat.rowval,mat,x)
    raw=zeros(Int,2);alias=unsafe_wrap(Vector{T},Ptr{T}(pointer(raw)),2;own=false)
    GC.@preserve raw alias @test !M._quality_local_terms_eligible(alias,zeros(T,2),raw,mat,x)
   end
  end
 end
end
const F0=(s,m,x,r,p,t)->Original.solve_quality!(s,m,x,r,p;transposed=t)
const FA=(s,m,x,r,p,t)->A.solve_quality!(s,m,x,r,p;transposed=t)
const FB=(s,m,x,r,p,t)->B.solve_quality!(s,m,x,r,p;transposed=t)
const FAB=(s,m,x,r,p,t)->AB.solve_quality!(s,m,x,r,p;transposed=t)
function batch(f,s,mat,x,rhs,p,t,count)
 q=f(s,mat,x,rhs,p,t)
 for k in 2:count;q=f(s,mat,x,rhs,p,t);end
 q
end
function window(f,s,mat,x,rhs,p,t,count)
 result=@timed batch(f,s,mat,x,rhs,p,t,count)
 (q=fields(result.value),seconds=result.time,bytes=result.bytes,events=Base.gc_alloc_count(result.gcstats),gc_seconds=result.gctime,compile_seconds=result.compile_time,recompile_seconds=result.recompile_time)
end
function fixture(T,n,storage,t,bad)
 rng=MersenneTwister(91+n)
 mat=spdiagm(0=>fill(T(4),n),1=>fill(T(1)/16,max(n-1,0)),-1=>fill(-T(1)/32,max(n-1,0)))
 if storage=="dense";mat=Matrix(mat);for j in 1:n,i in 1:n;if i!=j;mat[i,j]=T(mod(i*7+j*3,9)-4)/256;end;end;end
 x=T.(mod.(1:n,7)./8);rhs=(t ? transpose(mat) : mat)*x
 if bad && n>0;x[1]+=T(1)/4;end
 (mat,x,rhs)
end
correctness()
records=Any[];setup=Any[]
for T in (Float32,Float64),n in (16,128,384),storage in ("sparse","dense"),t in (false,true),bad in (false,true)
 prep=@timed fixture(T,n,storage,t,bad);mat,x,rhs=prep.value
 push!(setup,Dict("type"=>string(T),"n"=>n,"storage"=>storage,"transposed"=>t,"bad"=>bad,"seconds"=>prep.time,"bytes"=>prep.bytes,"events"=>Base.gc_alloc_count(prep.gcstats),"compile_seconds"=>prep.compile_time))
 contexts=map(M->(M.SolveQualityScratch(T,n),M.NumericalPolicy(T)),MODULES)
 fs=(F0,FA,FB,FAB);count=clamp(cld(80000,storage=="sparse" ? nnz(mat) : n*n),4,1024)
 for k in 1:4,warm in 1:3;window(fs[k],contexts[k][1],mat,x,rhs,contexts[k][2],t,count);end
 snapshot=deepcopy((mat,x,rhs));GC.gc()
 for pair in 1:12
  for k in (isodd(pair) ? (1,2,3,4) : (4,3,2,1))
   w=window(fs[k],contexts[k][1],mat,x,rhs,contexts[k][2],t,count)
   @test isequal(w.q,fields(F0(contexts[1][1],mat,x,rhs,contexts[1][2],t)))
   @test !w.q[4] == bad
   @test iszero(w.compile_seconds) && iszero(w.recompile_seconds)
   push!(records,Dict("type"=>string(T),"n"=>n,"storage"=>storage,"transposed"=>t,"bad"=>bad,"pair"=>pair,"arm"=>("original","A","B","AB")[k],"calls"=>count,"seconds"=>w.seconds,"bytes"=>w.bytes,"events"=>w.events,"gc_seconds"=>w.gc_seconds,"compile_seconds"=>w.compile_seconds,"recompile_seconds"=>w.recompile_seconds))
  end
 end
 @test isequal((mat,x,rhs),snapshot)
 println("FINISHED ",T,"/",n,"/",storage,"/",t,"/",bad);flush(stdout)
end
open(ARGS[1],"w") do io;TOML.print(io,Dict("records"=>records,"fixture_setup"=>setup));end
println("MEASUREMENT_COMPLETE records=",length(records))
