using JSimplex,SparseArrays,LinearAlgebra,Test,Serialization,SHA
_bf_projection_digest(x)=begin io=IOBuffer();serialize(io,x);bytes2hex(sha256(take!(io))) end
function _bf_projection_scalar(bits,sign=1;large_exp=bits+10,manager=:huangfu_hall)
 large=setprecision(BigFloat,320) do;BigFloat(2)^large_exp;end
 tol=BigFloat("1e-7");small=BigFloat(sign)*BigFloat(1.5)*tol
 p=LinearProblem(sparse(reshape(BigFloat[1,1],1,2)),zeros(BigFloat,2);column_lower=[nothing,large],column_upper=[nothing,large],row_lower=[large],row_upper=[large])
 o=SolverOptions(BigFloat;algorithm=:primal,basis_update=manager,presolve=false,simplex_strategy=:legacy,primal_tolerance=tol,dual_tolerance=tol,verbose=false)
 w=JSimplex._initialize_workspace_state(p,o);w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_UPPER])
 JSimplex.refactorize!(w.factorization,JSimplex.basis_matrix(w));w.primal.=BigFloat[small,large,large];w.scratch.row_solution.=[small]
 w
end
function _bf_projection_shifted()
    T=BigFloat;t=T(1e-7);margin=T(16)*t
    p=LinearProblem(sparse(reshape(T[1],1,1)),T[1];row_lower=T[-margin])
    w=JSimplex.initialize_workspace(p,SolverOptions(T;algorithm=:primal,basis_update=:pfi,primal_tolerance=t,verbose=false))
    w.basis=JSimplex.Basis([1],[JSimplex.BASIC,JSimplex.AT_LOWER])
    journal=JSimplex.PerturbationJournal(w);journal.bounds=JSimplex.BoundPerturbationState(w)
    journal.bounds.active_lower[1]=Bound(-margin);journal.bounds.active=true;journal.bounds.level=1
    w.lower=journal.bounds.active_lower;w.upper=journal.bounds.active_upper
    w.scratch.perturbations=journal;w.perturbed=true
    JSimplex.recompute!(w;refactorize=true)
    w
end
_bf_projection_frozen(w)=_bf_projection_digest((w.basis,w.lower,w.upper,w.costs,w.reduced_costs,w.options,w.progress.numerical_policy,w.problem))
@testset "BigFloat full residual band, stored precision and original guards" begin
 for bits in (32,64,128,240,256,512),sign in (-1,1)
  setprecision(BigFloat,bits) do
   w=_bf_projection_scalar(bits,sign);before=_bf_projection_frozen(w);nonbasic=_bf_projection_digest(w.primal[2:3]);env=(precision(BigFloat),rounding(BigFloat))
   ok=JSimplex._try_joint_primal_point_recovery!(w,()->false)
   @test ok
   @test JSimplex._ResidualProjection.certified(w)
   @test JSimplex._original_primal_feasible(w.problem,w.primal[1:2],w.options.primal_tolerance)
   @test abs(JSimplex._exact_rational(w.primal[1]))<=JSimplex._exact_rational(w.options.primal_tolerance)
   @test _bf_projection_digest(w.primal[2:3])==nonbasic && precision(w.primal[2])==precision(w.primal[3])==320
   @test _bf_projection_frozen(w)==before && env==(precision(BigFloat),rounding(BigFloat))
   @test w.scratch.row_solution==w.primal[1:1]
   @test !JSimplex._legacy_primal_row_validation_enabled(w)
   # A point already certified anywhere in the full band remains unchanged.
   safe=_bf_projection_scalar(bits,sign;large_exp=min(bits-40,100));safe.primal[1]=BigFloat(sign)*safe.options.primal_tolerance/2
   safe.scratch.row_solution.=safe.primal[1:1];point=_bf_projection_digest(safe.primal)
   @test JSimplex._ResidualProjection.certified(safe)
   @test JSimplex._try_joint_primal_point_recovery!(safe,()->false)
   @test _bf_projection_digest(safe.primal)==point
   safe.primal[1]=BigFloat(sign)*nextfloat(safe.options.primal_tolerance)
   @test !JSimplex._ResidualProjection.certified(safe)
  end
 end
end
@testset "Generic basis-manager coverage" begin
 setprecision(BigFloat,128) do
  for manager in (:huangfu_hall,:forrest_tomlin,:suhl_suhl,:bartels_golub,:pfi)
   w=_bf_projection_scalar(128;manager)
   @test JSimplex._try_joint_primal_point_recovery!(w,()->false)
   @test JSimplex._ResidualProjection.certified(w)
  end
 end
end
@testset "Failure, stop, exceptions and unsupported modes roll back" begin
 setprecision(BigFloat,128) do
  for mode in (RoundDown,RoundUp,RoundToZero,RoundFromZero)
   w=_bf_projection_scalar(128);before=_bf_projection_digest((w.primal,w.scratch.row_solution));controls=_bf_projection_frozen(w)
   setrounding(BigFloat,mode) do
    @test !JSimplex._try_joint_primal_point_recovery!(w,()->false)
    @test _bf_projection_digest((w.primal,w.scratch.row_solution))==before && _bf_projection_frozen(w)==controls
   end
  end
  for prediction in (BigFloat[],BigFloat[NaN])
   w=_bf_projection_scalar(128);before=_bf_projection_digest((w.primal,w.scratch.row_solution));controls=_bf_projection_frozen(w)
   @test !JSimplex._try_joint_primal_point_recovery!(w,()->false,prediction)
   @test _bf_projection_digest((w.primal,w.scratch.row_solution))==before && _bf_projection_frozen(w)==controls
  end
  w=_bf_projection_scalar(128);w.primal[1]=4w.options.primal_tolerance;w.lower[1]=JSimplex.Bound(w.primal[1]);w.upper[1]=JSimplex.Bound(w.primal[1]);w.scratch.row_solution.=w.primal[1:1]
  before=_bf_projection_digest((w.primal,w.scratch.row_solution));controls=_bf_projection_frozen(w)
  @test !JSimplex._try_joint_primal_point_recovery!(w,()->false)
  @test _bf_projection_digest((w.primal,w.scratch.row_solution))==before && _bf_projection_frozen(w)==controls
  probe=_bf_projection_scalar(128);calls=Ref(0)
  @test JSimplex._try_joint_primal_point_recovery!(probe,()->(calls[]+=1;false))
  total=calls[]
  for at in unique([1,2,max(1,total÷2),total])
   for throwing in (false,true)
    w=_bf_projection_scalar(128);before=_bf_projection_digest((w.primal,w.scratch.row_solution));controls=_bf_projection_frozen(w);count=Ref(0)
    stop=()->begin count[]+=1;if count[]>=at;throwing && error("injected");return true;end;false;end
    if throwing;@test_throws ErrorException JSimplex._try_joint_primal_point_recovery!(w,stop)
    else;@test !JSimplex._try_joint_primal_point_recovery!(w,stop);end
    @test _bf_projection_digest((w.primal,w.scratch.row_solution))==before && _bf_projection_frozen(w)==controls
   end
  end
 end
end
@testset "BigFloat owned working-bound journal remains distinct from original feasibility" begin
 setprecision(BigFloat,128) do
  w=_bf_projection_shifted()
  before=_bf_projection_digest(w.primal)
  @test JSimplex._ResidualProjection.certified(w)
  @test !JSimplex._original_primal_feasible(w.problem,w.primal[1:1],w.options.primal_tolerance)
  @test JSimplex._try_joint_primal_point_recovery!(w,()->false)
  @test _bf_projection_digest(w.primal)==before
  journal=w.scratch.perturbations;owner=journal.workspace_id;journal.workspace_id=UInt(0)
  @test_throws ArgumentError JSimplex._try_joint_primal_point_recovery!(w,()->false)
  journal.workspace_id=owner
  @test JSimplex._internal_solution(w,JSimplex.OPTIMAL,"working-only point").status==JSimplex.NUMERICAL_ERROR
 end
end
