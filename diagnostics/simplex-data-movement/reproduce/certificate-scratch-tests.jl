using JSimplex,Test,SparseArrays
@testset "Repeated native point certification reuses numeric storage" begin
 for T in (Float32,Float64)
  n=2048;p=LinearProblem(spdiagm(0=>ones(T,n)),zeros(T,n);row_lower=zeros(T,n))
  ws=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
  @test JSimplex._legacy_primal_point_certified(ws)
  JSimplex._legacy_primal_point_certified(ws)
  @test (@allocated JSimplex._legacy_primal_point_certified(ws))<=512
  # Repeated calls must re-read the current point, not cache a verdict/enclosure.
  ws.primal[1]=T(1)
  @test !JSimplex._legacy_primal_point_certified(ws)
  ws.primal[n+1]=T(1)
  @test JSimplex._legacy_primal_point_certified(ws)
  ws.primal[1]=T(NaN)
  @test !JSimplex._legacy_primal_point_certified(ws)
  ws.primal[1]=T(1)
  @test JSimplex._legacy_primal_point_certified(ws)
 end
end
