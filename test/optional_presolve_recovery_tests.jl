using JSimplex,Test,SparseArrays
@testset "Missing optional dual uses certified original recovery" begin
 JS=JSimplex
 for T in (Float32,Float64,BigFloat)
  p=LinearProblem(sparse(T[1 1 1;1 1 -1]),T[1,1,1];row_lower=T[3,-1],row_upper=T[5,2],column_upper=T[4,4,4])
  o=SolverOptions(T;verbose=false,scaling=:off,pricing=:devex,presolve_column_merging=true)
  reduced=Ref(0);original=Ref(0)
  diagnostics=JS.SimplexDiagnostics(;observer=(reason,w)->begin
   if reason==:certification
    if size(w.problem.A,2)<size(p.A,2)
     reduced[]+=1
     # Deliberately suppress the optional witness after a completed reduced
     # solve. Exercise the real caller boundary without changing its result.
     c=w.progress
     w.progress=typeof(c)(c.start_ns,c.objective,c.objective_constant,c.scaling,
       c.iteration_offset,c.refactorization_offset,c.diagnostics,c.numerical_policy,nothing)
    elseif size(w.problem.A)==size(p.A)
     original[]+=1
    end
   end
   nothing
  end)
  result=JS._solve_diagnosed(p,diagnostics;options=o)
  @test reduced[]>0
  @test original[]>0
  @test result.status==OPTIMAL
  @test JS._original_primal_feasible(p,result.primal,o.primal_tolerance)
  @test result.objective_value==T(3)
 end
end
