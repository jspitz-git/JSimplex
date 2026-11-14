using Test, JSimplex, SparseArrays, LinearAlgebra, Random
module DualRowAdapterKernelTests
using Test, JSimplex, SparseArrays, LinearAlgebra, Random
const JS = JSimplex
const rng=MersenneTwister(39117)
function ws_fixture(T,m=200,n=97)
 A=sprand(rng,T,m,n,0.08);p=LinearProblem(A,zeros(T,n);column_upper=fill(T(3),n))
 JS.initialize_workspace(p,SolverOptions(T;verbose=false,presolve=false,simplex_strategy=:legacy,pricing=:steepest_edge))
end
freeze(r)=(r[1],copy(r[2]),r[3])
@testset "Both complete kernels, guard boundaries and support consumers" begin
 for T in (Float32,Float64)
  w=ws_fixture(T);m,n=size(w.problem.A);out=zeros(T,m+n);ref=similar(out)
  c=JS._DualRowContext(T,m,n)
  for trial in 1:150
   # Valid shuffled structural/slack basis; states deliberately independently varied.
   w.basis.basic_indices.=shuffle(rng,collect(1:m+n))[1:m]
   for i in eachindex(w.basis.states)
    w.basis.states[i]=rand(rng,(JS.AT_LOWER,JS.AT_UPPER,JS.BASIC,JS.FREE_NONBASIC))
    w.reduced_costs[i]=T(rand(rng,-2:4))
   end
   rho=trial%2==0 ? randn(rng,T,m) : zeros(T,m)
   trial%2==1 && (rho[rand(rng,1:m)]=T(randn(rng)))
   leaving=rand(rng,1:m)
   JS._csc_price!(ref,w.problem.A,rho);JS._dual_row_price!(c,w,out,rho,leaving)
   @test isequal(out,ref)
   @test isequal(JS._dual_row_residual!(c,w,rho,leaving),JS._dual_row_residual_ratio(w,rho,leaving))
   @test !c.ready
   @test isequal(JS._dual_row_residual!(c,w,rho,leaving),JS._dual_row_residual_ratio(w,rho,leaving))
   orientation=rand(rng,Bool) ? one(T) : -one(T);violation=T(rand(rng,1:100))
   empty!(w.scratch.rejected_entering);trial%4==0 && push!(w.scratch.rejected_entering,rand(rng,1:n+m))
   # All values, including tiny nonzeros and signed zero, participate in support.
   row=T.(rand(rng,[-2,-1,0,0,0,1,2],m+n));row[1]=-zero(T);row[2]=T(1e-10)
   support=findall(!iszero,row)
   expected=JS.dual_ratio_test(w,row,orientation)
   @test JS._dual_ratio_test_indices(w,row,orientation,support)==expected
   expected=freeze(JS._bound_flipping_ratio_test(w,row,orientation,violation))
   @test isequal(freeze(JS._bound_flipping_ratio_test_indices(w,row,orientation,violation,support)),expected)
  end
  for bad in (T(Inf),T(NaN),floatmax(T))
   rho=fill(bad,m);JS._dual_row_price!(c,w,out,rho,1);JS._csc_price!(ref,w.problem.A,rho)
   @test isequal(out,ref)
   @test isequal(JS._dual_row_residual!(c,w,rho,1),JS._dual_row_residual_ratio(w,rho,1))
  end
  # Duplicate basis fallback, invalid index deferred to original guard.
  rho=ones(T,m);w.basis.basic_indices[2]=w.basis.basic_indices[1]
  JS._dual_row_price!(c,w,out,rho,1);@test c.mode==:fallback
  @test isequal(JS._dual_row_residual!(c,w,rho,1),JS._dual_row_residual_ratio(w,rho,1))
  w.basis.basic_indices[1]=m+n+1
  JS._dual_row_price!(c,w,out,rho,1);@test c.mode==:fallback
  @test_throws BoundsError JS._dual_row_residual!(c,w,rho,1)
  @test_throws DimensionMismatch JS._dual_row_basis_map!(c,w,rho[1:end-1],out,1)
 end
 # Exact cancellation and replacement must clear the previous support.
 w=JS.initialize_workspace(LinearProblem(sparse([1. -1;1 -1]),zeros(2)),SolverOptions(verbose=false,presolve=false))
 c=JS._DualRowContext(Float64,2,2);out=zeros(4)
 for rho in ([1.,0.],[1.,-1.],[0.,0.],[-0.,1.])
  JS._dual_row_support!(c,w.problem.A,out,rho)
  @test c.support==findall(!iszero,out)
 end
 n=96;w=JS.initialize_workspace(LinearProblem(sparse(ones(1,n)),collect(1.:n);column_upper=ones(n)),SolverOptions(verbose=false,presolve=false))
 w.basis.states[1:n].=JS.AT_LOWER;w.reduced_costs[1:n].=1:n
 row=[ones(n);0.];expected=freeze(JS._bound_flipping_ratio_test(w,row,1.,80.5))
 @test length(expected[2])>=32
 @test freeze(JS._bound_flipping_ratio_test_indices(w,row,1.,80.5,collect(1:n)))==expected
 # Zero-length rho, generation rollover and no per-call allocation when warmed.
 @test JS._dual_row_route(Float64[])==:support
 w=ws_fixture(Float64);m,n=size(w.problem.A);c=JS._DualRowContext(Float64,m,n);rho=ones(m);out=zeros(m+n)
 c.generation=typemax(UInt64);@test JS._dual_row_basis_map!(c,w,rho,out,1);@test c.generation==1
 JS._dual_row_price!(c,w,out,rho,1);JS._dual_row_residual!(c,w,rho,1)
 kernel(c,w,out,rho)=(JS._dual_row_price!(c,w,out,rho,1);JS._dual_row_residual!(c,w,rho,1);nothing)
 kernel(c,w,out,rho)
 bytes=@allocated kernel(c,w,out,rho)
 @test bytes==0
end

end
