using JSimplex,Test,SparseArrays,LinearAlgebra
const JS=JSimplex
const implementation=joinpath(@__DIR__,"long_counters.jl")
@test isfile(implementation)
include(implementation)
install_long_counters!(JS,dirname(pathof(JS)))
function check_long_counters()
 @testset "Long count-only instrumentation" begin
  @test_throws ArgumentError install_long_counters!(JS,dirname(pathof(JS)))
  storage=JS._lc_counts
  @test all(iszero,storage)
  problem=JS.LinearProblem(sparse(reshape([1.0],1,1)),[1.0];row_lower=[1.0],row_upper=[Inf])
  for pricing in (:steepest_edge,:dantzig)
   ws=JS.initialize_workspace(problem,JS.SolverOptions(;pricing,basis_update=:huangfu_hall,verbose=false))
   reset_long_counters!(JS)
   @test JS._finite_workspace(ws)
   counts=long_counter_rows(JS)
   @test counts["_finite_workspace"]==1
   @test counts["finite_value_elements"]==(pricing==:dantzig ? 3 : 4)*length(ws.primal)
   ws.primal[1]=NaN
   reset_long_counters!(JS)
   @test !JS._finite_workspace(ws)
   @test long_counter_rows(JS)["finite_value_elements"]==length(ws.primal)
   ws.primal[1]=0
   for (op,transpose) in ((:ftran,false),(:btran,true),(:weight_ftran,false),(:weight_btran,true),(:bfrt,false))
    reset_long_counters!(JS)
    JS._pipeline_basis_solve!(zeros(1),ws,ones(1);operation=op,transposed=transpose)
    c=long_counter_rows(JS)
    @test c["pipeline_"*string(op)*"_"*(transpose ? "transpose" : "forward")]==1
    @test c["_pipeline_basis_solve!"]==1
   end
   reset_long_counters!(JS)
   @test_throws ArgumentError JS._pipeline_basis_solve!(zeros(1),ws,ones(1);kernel_mode=:invalid)
   @test long_counter_rows(JS)["_pipeline_basis_solve!"]==1
  end
  for _ in 1:1000;reset_long_counters!(JS);end
  @test JS._lc_counts===storage
  @test length(storage)==length(LONG_COUNTER_LABELS)
  @test all(iszero,storage)
  # The private counter shape is checked at reset before unchecked probes run.
  resize!(storage,length(LONG_COUNTER_LABELS)-1)
  try
   @test_throws DimensionMismatch reset_long_counters!(JS)
  finally
   resize!(storage,length(LONG_COUNTER_LABELS));fill!(storage,0)
  end
 end
end

Base.invokelatest(check_long_counters)
