using Test, SparseArrays, JSimplex
module _PresolveWorkTestTools
using JSimplex,SparseArrays,SHA
const JS=JSimplex
include("presolve_cache_fingerprint.jl")
fixture(T)=LinearProblem(sparse(T[3 5;1 0;0 1]),ones(T,2);row_lower=T[1,-10,-10],row_upper=T[1,10,10],column_lower=zeros(T,2),column_upper=ones(T,2))
end
@testset "Presolve work cache scope and exact repeated results" begin
 @test isdefined(JSimplex,:_PresolveWork)
 if isdefined(JSimplex,:_PresolveWork)
  W=JSimplex._PresolveWork;H=_PresolveWorkTestTools
  for T in (Float32,Float64,BigFloat)
   p=H.fixture(T);before=H.digest(p);reference=JSimplex.aggregate_sparse_equalities(p)
   @test isnothing(W.current(T))
   W.with_session(T) do
    cache=W.current(T);q=W.exact(T(3))
    @test W.exact(T(3))===q
    @test W.rows(p.A)===W.rows(p.A)
    a=JSimplex.aggregate_sparse_equalities(p)
    @test isempty(a.postsolve_stack) && haskey(cache.rejected,1)
    stored=cache.rejected[1];b=JSimplex.aggregate_sparse_equalities(p)
    @test cache.rejected[1]===stored
    @test H.digest(a)==H.digest(b)==H.digest(reference)
    @test H.digest(p)==before
    @test_throws ErrorException W.with_session(T) do
     @test W.current(T)!==cache
     error("nested scope")
    end
    @test W.current(T)===cache
    fetch(@async begin
     @test isnothing(W.current(T))
     W.with_session(T) do
      @test W.current(T)!==cache
      yield()
      @test W.exact(T(3))==q
     end
    end)
    @test W.current(T)===cache
   end
   @test isnothing(W.current(T))
   W.with_session(T;qcap=0,rcap=1) do
    W.exact(T(7));@test isempty(W.current(T).exact)
   end
  end
  for T in (Rational{BigInt},Rational{Int},Float16)
   W.with_session(T) do
    @test isnothing(W.current(T))
    @test W.exact(T(3))==JSimplex._exact_rational(T(3))
   end
  end
 end
end
