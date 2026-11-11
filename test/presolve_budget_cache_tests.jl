using JSimplex,Test,SparseArrays
@testset "A smaller sparse budget cannot poison later rejection reuse" begin
 W=JSimplex._PresolveWork;R=JSimplex._PresolveRepeat
 for T in (Float32,Float64,BigFloat)
  p=LinearProblem(sparse(T[3 4;1 0;0 1;0 1]),zeros(T,2);row_lower=[T(1),nothing,nothing,nothing],row_upper=[T(1),nothing,nothing,nothing],column_lower=fill(nothing,2),column_upper=fill(nothing,2))
  W.with_session(T) do
   budget=R.Ledger();budget.sparse_updates=199999
   R.with_budget(budget) do
    r=JSimplex.aggregate_sparse_equalities(p)
    @test isempty(r.postsolve_stack)
    @test haskey(W.current(T).rejected,1)
   end
   @test isempty(W.current(T).rejected)
   r=JSimplex.aggregate_sparse_equalities(p)
   @test !isempty(r.postsolve_stack)
   @test isnothing(R.current())
  end
 end
end
