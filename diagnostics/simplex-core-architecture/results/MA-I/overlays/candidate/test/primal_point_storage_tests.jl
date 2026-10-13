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

@testset "Point certificate refreshes owned storage and preserves fallback decisions" begin
 for T in (Float32,Float64), update in (:pfi,:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub)
  p=LinearProblem(sparse(T[1 -1;0 1]),zeros(T,2);row_lower=T[-Inf,-Inf],column_lower=T[-Inf,-Inf])
  w=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,basis_update=update,verbose=false))
  other=JSimplex.initialize_workspace(p,w.options)
  @test isnothing(w.scratch.primal_point_buffers)
  w.primal[1]=T(NaN)
  @test !JSimplex._legacy_primal_point_certified(w)
  @test isnothing(w.scratch.primal_point_buffers)
  w.primal .= T[4,1,3,1]
  @test JSimplex._legacy_primal_point_certified(w)
  @test JSimplex._legacy_primal_point_certified(other)
  @test w.scratch.primal_point_buffers !== other.scratch.primal_point_buffers
  for x in (T[2,1,1,1],T[2,1,2,1],T[4,2,2,2],T[4,2,2,3])
   w.primal .= x
   @test JSimplex._legacy_primal_point_certified(w) == (x[1]-x[2]==x[3] && x[2]==x[4])
  end
  w.primal .= T[4,1,3,1];w.problem.A.nzval[1]=T(2)
  @test !JSimplex._legacy_primal_point_certified(w)
  w.primal[3]=T(7)
  @test JSimplex._legacy_primal_point_certified(w)
  # Restore shared model before probing the other workspace.
  w.problem.A.nzval[1]=one(T)
  @test JSimplex._legacy_primal_point_certified(other)
 end
 for T in (Float32,Float64)
  large=T===Float32 ? T(2.0^30) : T(2.0^60)
  p=LinearProblem(sparse(reshape(T[large,1,-large],1,3)),zeros(T,3);row_lower=T[1],row_upper=T[1])
  w=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,verbose=false))
  w.primal .= T[1,1,1,1]
  @test JSimplex._legacy_primal_point_certified(w)
  w.primal[2]=T(2)
  @test !JSimplex._legacy_primal_point_certified(w)
  w.primal[2]=one(T)
  @test JSimplex._legacy_primal_point_certified(w)
 end
end

@testset "Native row fallback avoids a copied activity slice" begin
    n=2048
    problem=LinearProblem(spdiagm(0=>ones(n)),zeros(n);row_lower=zeros(n))
    workspace=JSimplex.initialize_workspace(problem,SolverOptions(;algorithm=:primal,verbose=false))
    workspace.primal .= 1.0
    primal=ones(n)
    bounds=(zeros(n),fill(2.0,n))
    # Force the compensated fallback with a wide enclosure of exact unit rows.
    @test JSimplex._legacy_primal_row_consistent(workspace,workspace.options.primal_tolerance,primal,bounds)
    bytes=@allocated JSimplex._legacy_primal_row_consistent(workspace,workspace.options.primal_tolerance,primal,bounds)
    @test bytes <= 142000
end
