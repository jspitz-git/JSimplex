using JSimplex,Test,SparseArrays
@testset "Numerical failure cannot replenish recovery by advancing iterations" begin
 for T in (Float32,Float64,BigFloat,Rational{BigInt}), rounds in (0,1,100), varying_signature in (false,true)
  failures=Ref(0);checks=Ref(0)
  # The real primal kernel rejects this unreliable direction. Simulate
  # completed work at its error boundary without making the point valid.
  d=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
   if event==:feasibility_recovery
    failures[]+=1
    w.iterations+=1
    varying_signature && (w.scratch.phase_generation+=UInt(1))
   end
  end)
  p=LinearProblem(sparse(reshape(T[1//10],1,1)),T[-1];row_upper=T[1])
  o=SolverOptions(T;verbose=false,algorithm=:primal,zero_tolerance=T(1//2))
  policy=JSimplex.NumericalPolicy(T;feasibility_recovery=true,max_recovery_rounds=rounds)
  w=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
  before=w.options;b=JSimplex.SimplexRunBudget(w)
  result=JSimplex.run_from_basis!(w,b,policy,()->begin checks[]+=1;checks[]>200 end)
  @test result.status==NUMERICAL_ERROR
  @test failures[]<=min(2,rounds)+1
  @test !varying_signature || failures[]==min(2,rounds)+1
  @test checks[]<=200
  @test occursin("bounded feasibility recovery exhausted",result.message)
  @test occursin("last numerical failure:",result.message)
  @test occursin("primal pivot is below the zero tolerance",result.message)
  @test result.iterations==b.iterations==failures[]
  @test w.options===before
 end
end

@testset "Cancellation keeps precedence at recovery exhaustion" begin
 for T in (Float32,Float64), throwing in (false,true)
  failed=Ref(false)
  d=JSimplex.SimplexDiagnostics(;observer=(event,w)->begin
   if event==:feasibility_recovery
    failed[]=true;w.iterations+=1
   end
  end)
  p=LinearProblem(sparse(reshape(T[1//10],1,1)),T[-1];row_upper=T[1])
  o=SolverOptions(T;verbose=false,algorithm=:primal,zero_tolerance=T(1//2))
  policy=JSimplex.NumericalPolicy(T;feasibility_recovery=true,max_recovery_rounds=0)
  w=JSimplex.initialize_workspace(p,o;progress=JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
  before=w.options;b=JSimplex.SimplexRunBudget(w);failure=JSimplex.SingularException(71)
  result=try
   JSimplex.run_from_basis!(w,b,policy,()->failed[] ? (throwing ? throw(failure) : true) : false)
  catch e
   e
  end
  @test failed[]
  @test throwing ? result===failure : result.status==TIME_LIMIT
  @test w.options===before
  @test b.iterations==w.iterations==1
 end
end
