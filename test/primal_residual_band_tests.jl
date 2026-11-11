using JSimplex,Test,SparseArrays
function _residual_band_workspace(T,sign)
 large=T===Float32 ? T(12) : T(1e10);tol=T(1e-7)
 p=LinearProblem(sparse(reshape(T[1,1],1,2)),zeros(T,2);column_lower=[nothing,large],column_upper=[nothing,large],row_lower=[large],row_upper=[large])
 w=JSimplex._initialize_workspace_state(p,SolverOptions(T;algorithm=:primal,presolve=false,simplex_strategy=:legacy,primal_tolerance=tol,dual_tolerance=tol,verbose=false))
 w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_UPPER]);JSimplex.refactorize!(w.factorization,JSimplex.basis_matrix(w))
 w.primal.=T[T(sign)*T(1.5)*tol,large,large];w.scratch.row_solution.=[w.primal[1]];w
end
@testset "Residual projection keeps Float64 and Float32 tolerance bands" begin
 for T in (Float64,Float32),sign in (-1,1)
  w=_residual_band_workspace(T,sign);fixed=copy(w.primal[2:3]);tol=w.options.primal_tolerance
  @test !JSimplex._legacy_primal_point_certified(w)
  @test JSimplex._try_joint_primal_point_recovery!(w,()->false)
  @test JSimplex._legacy_primal_point_certified(w)
  @test abs(Rational{BigInt}(w.primal[1]))<=Rational{BigInt}(tol)
  @test w.primal[2:3]==fixed && w.scratch.row_solution==w.primal[1:1]
  w.primal[1]=T(sign)*tol/T(2);w.scratch.row_solution.=w.primal[1:1];point=copy(w.primal)
  @test JSimplex._try_joint_primal_point_recovery!(w,()->false)
  @test w.primal==point
  w.primal[1]=T(sign)*nextfloat(tol)
  @test !JSimplex._legacy_primal_point_certified(w)
 end
end
