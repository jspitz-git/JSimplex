using JSimplex,Test,SparseArrays
@testset "Unequal-cost proportional dominance respects objective sense" begin
 J=JSimplex
 for T in (Float32,Float64,BigFloat),sense in (MIN_SENSE,MAX_SENSE)
  p=LinearProblem(sparse(T[1 1 1;1 1 -1]),T[1,2,1];row_lower=T[3,-1],row_upper=T[5,2],column_upper=T[10,10,4],objective_sense=sense)
  o=SolverOptions(T;verbose=false,scaling=:off,pricing=:devex,presolve_column_dominance=true)
  h=sense==MIN_SENSE ? J._PostsolveHistory(T) : nothing
  r=J._with_optional_presolve(J.identity_presolve(p),h,o)
  @test r isa J._OptionalPresolveResult
  @test !isempty(r.fixing_steps)
  removed=first(r.fixing_steps).removed_values
  @test !isnothing(removed[sense==MIN_SENSE ? 2 : 1])
  @test isnothing(removed[sense==MIN_SENSE ? 1 : 2])
  q=J._minimization_problem(r.problem)
  progress=J.SimplexProgressContext(q;numerical_policy=J.NumericalPolicy(T,o),witness_problem=q)
  run=J._solve_continuous_dual(q,o;progress)
  @test run.status==OPTIMAL
  b,x=J._postsolve_with_dual(h,r,J.identity_scaling(r.problem),run,o)
  @test !isnothing(b) && !isnothing(x)
  @test J._original_primal_feasible(p,x,o.primal_tolerance)
  final=J.cleanup_original(p,b,o,J.SolveContext(time_ns(),Inf),run.iterations,run.refactorizations;target_primal=x)
  @test final.status==OPTIMAL
  @test J._restored_objective(p,final.primal)==(sense==MIN_SENSE ? T(3) : T(17//2))
  ws=J.initialize_from_basis(J._minimization_problem(p),final.basis,o)
  @test J._original_optimality_certified(ws,final.primal)
 end
end
