using JSimplex,Test,SparseArrays,LinearAlgebra,TOML,SHA
const JS=JSimplex
const ROOT=dirname(dirname(pathof(JS)))
@testset "Integrated restoration contracts" begin
 include(joinpath(ROOT,"test/restoration_alias_copy_tests.jl"))
 include(joinpath(ROOT,"test/cost_restore_allocation_tests.jl"))
 # Actual restoration during a small stalled primal chain, both HH backends.
 for backend in (:native,:markowitz)
  p=LinearProblem(spdiagm(0=>ones(3),1=>-ones(2)),[-1.0,0,0];row_upper=[0.0,0,1])
  policy=JS.NumericalPolicy(Float64;simplex_strategy=:adaptive,adaptive_pricing=false,
      adaptive_primal_perturbation=true,stagnation_window=1,refactor_timing=false)
  d=JS.SimplexDiagnostics()
  w=JS.initialize_workspace(p,SolverOptions(;algorithm=:primal,basis_update=:huangfu_hall,
      basis_refactorization=backend,verbose=false,iteration_limit=100);
      progress=JS.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
  result=JS.run_from_basis!(w,JS.SimplexRunBudget(w),policy,()->false)
  @test result.status==OPTIMAL
  @test JS._original_primal_feasible(p,result.primal,w.options.primal_tolerance)
  @test JS._original_costs_active(w) && JS._original_bounds_active(w)
  @test !JS._has_active_perturbations(w.scratch.perturbations)
 end
end
@assert !ispath(only(ARGS))
open(only(ARGS),"w") do io
 TOML.print(io,Dict("source"=>pathof(JS),"source_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"src/simplex_perturbation.jl")))),
 "complete"=>true,"julia_threads"=>Threads.nthreads(),"blas_threads"=>BLAS.get_num_threads()))
end
