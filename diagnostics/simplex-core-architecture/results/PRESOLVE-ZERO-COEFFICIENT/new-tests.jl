using SparseArrays

# This catches treating a committed matrix update as a missing original zero,
# losing signed-zero inputs, or returning an inexact/unstaged result.
@testset "Missing zero conversions preserve sparse equality staging" begin
 for stored in (nothing, 0.0, -0.0), multiplier in (2.0,-2.0,0.0)
  rows=[1,1,2];cols=[1,2,1];values=[2.0,3.0,2multiplier]
  if stored!==nothing;push!(rows,2);push!(cols,2);push!(values,stored);end
  p=LinearProblem(sparse(rows,cols,values,2,2),[0.0,2.0];objective_constant=7.0,
    row_lower=[4.0,nothing],row_upper=[4.0,20.0],column_lower=[nothing,nothing],column_upper=[nothing,nothing])
  original=deepcopy(p);owners=(p.A,p.A.colptr,p.A.rowval,p.A.nzval,p.row_lower,p.row_upper,p.objective)
  r=JSimplex.aggregate_sparse_equalities(p)
  @test size(r.problem.A)==(1,1)
  @test r.problem.A[1,1]==-3multiplier
  @test bound_value(r.problem.row_upper[1])==20-4multiplier
  @test JSimplex.postsolve_primal(r,[0.0])==[2.0,0.0]
  @test isequal(p.A.nzval,original.A.nzval)
  @test p.A.colptr==original.A.colptr && p.A.rowval==original.A.rowval
  @test p.row_lower==original.row_lower && p.row_upper==original.row_upper && p.objective==original.objective
  @test all(a===b for (a,b) in zip(owners,(p.A,p.A.colptr,p.A.rowval,p.A.nzval,p.row_lower,p.row_upper,p.objective)))
 end
 for old in (0.0,3.0),term in (1.0,-1.0)
  p=LinearProblem(sparse([2.0 0.0 3.0;0.0 -2.0 term;2.0 2.0 old]),[0.0,0.0,2.0];objective_constant=7.0,
    row_lower=[4.0,-4.0,nothing],row_upper=[4.0,-4.0,20.0],column_lower=fill(nothing,3),column_upper=fill(nothing,3))
  r=JSimplex.aggregate_sparse_equalities(p)
  @test size(r.problem.A)==(1,1)
  @test r.problem.A[1,1]==old-3+term
  @test bound_value(r.problem.row_upper[1])==12.0
  @test JSimplex.postsolve_primal(r,[0.0])==[2.0,2.0,0.0]
 end
end
