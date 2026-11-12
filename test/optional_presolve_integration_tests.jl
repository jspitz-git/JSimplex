using Test,JSimplex,SparseArrays,LinearAlgebra
module OptionalPresolveFixtures
using JSimplex,SparseArrays
const JS=JSimplex
function options(T,flags;kwargs...)
 JS.SolverOptions(T;verbose=false,pricing=:devex,presolve_row_sparsification=flags[1],presolve_column_merging=flags[2],presolve_column_dominance=flags[3],kwargs...)
end
function model(T;sense=JS.MIN_SENSE)
 JS.LinearProblem(sparse(T[1 1 0; .5 .5 1]),T[1,1,1];row_lower=T[2,2],row_upper=T[2,2],column_upper=T[4,4,4],objective_sense=sense)
end
function run(p,o)
 rp=JS._minimization_problem(p)
 progress=JS.SimplexProgressContext(rp;numerical_policy=JS.NumericalPolicy(eltype(p.A),o),witness_problem=rp)
 (o.algorithm==:dual ? JS._solve_continuous_dual : JS._solve_continuous_primal)(rp,o;progress)
end
off_columns(b,h,o)=JS._with_optional_presolve(b,h,o).original_column_count
function off_allocations(b::B,h::H,o::O) where {B,H,O}
 off_columns(b,h,o)
 @allocated off_columns(b,h,o)
end
same(p,q)=p.A.colptr==q.A.colptr && p.A.rowval==q.A.rowval && JS._PresolveWork.samevalues(p.A.nzval,q.A.nzval) &&
 all(JS._PresolveWork.samevalues(getfield(p,k),getfield(q,k)) for k in (:objective,:row_lower,:row_upper,:column_lower,:column_upper)) && JS._PresolveWork.samevalue(p.objective_constant,q.objective_constant)
end
@testset "Disabled optional passes preserve identity and allocate no model-sized metadata" begin
 JS=JSimplex;F=OptionalPresolveFixtures
 for T in (Float32,Float64,BigFloat),n in (2,64)
  p=LinearProblem(sparse(ones(T,2,n)),zeros(T,n);row_lower=T[0,0],column_upper=ones(T,n))
  base=JS.identity_presolve(p);o=F.options(T,(false,false,false))
  h=JS._PostsolveHistory(T)
  @test JS._with_optional_presolve(base,h,o)===base
  @test isempty(h.metadata)
  F.off_columns(base,h,o)
  # Julia boxes the immutable PresolveResult in the helper union return.
  # Bound this fixed setup cost; no optional index/history/cache is built.
  @test F.off_allocations(base,h,o)<=160
  enabled=F.options(T,(true,true,true);presolve=false)
  @test JS._with_optional_presolve(base,h,enabled)===base
 end
end
@testset "Optional batches actually reduce and restore the complete chain" begin
 JS=JSimplex;F=OptionalPresolveFixtures
 for T in (Float32,Float64,BigFloat),flags in ((true,false,false),(false,true,false),(false,false,true),(true,true,true)),sense in (JS.MIN_SENSE,JS.MAX_SENSE)
  p=F.model(T;sense);original=deepcopy(p);o=F.options(T,flags;scaling=:off)
  h=sense==JS.MIN_SENSE ? JS._PostsolveHistory(T) : nothing
  r=JS._with_optional_presolve(JS.identity_presolve(p),h,o)
  @test r isa JS._OptionalPresolveResult
  @test F.same(p,original)
  flags[1] && @test !isnothing(r.row_step)
  flags[2] && @test !isnothing(r.column_step)
  @test count(v->v isa LinearProblem, (getfield(r,k) for k in fieldnames(typeof(r))))==1
  if !isnothing(r.column_step)
   @test !hasproperty(r.column_step,:problem) && !hasproperty(r.column_step,:original)
  end
  run=F.run(r.problem,o)
  @test run.status==OPTIMAL && !isnothing(run.dual)
  b,x=JS._postsolve_with_dual(h,r,JS.identity_scaling(r.problem),run,o)
  @test !isnothing(b) && !isnothing(x)
  @test JS._original_primal_feasible(p,x,o.primal_tolerance)
  ws=JS.initialize_from_basis(JS._minimization_problem(p),b,o)
  @test JS._original_primal_feasible(p,ws.primal[1:3],o.primal_tolerance)
  @test JS._original_optimality_certified(ws,ws.primal[1:3])
  @test isnothing(h) || isempty(h.metadata)
  @test isnothing(r.tail_history) || isempty(r.tail_history.metadata)
  @test F.same(p,original)
 end
end
@testset "Public solve all8 flags, primal/dual, scaling and objective sense" begin
 JS=JSimplex;F=OptionalPresolveFixtures
 for T in (Float32,Float64,BigFloat),mask in 0:7,algorithm in (:primal,:dual),scaling in (:off,:auto),sense in (JS.MIN_SENSE,JS.MAX_SENSE)
  flags=ntuple(i->!iszero(mask & (1<<(i-1))),3);p=F.model(T;sense)
  o=F.options(T,flags;algorithm,scaling)
  sol=solve(p;options=o)
  @test sol.status==OPTIMAL
  @test sol.objective_value==T(3)
  @test JS._original_primal_feasible(p,sol.primal,o.primal_tolerance)
 end
end
@testset "Safe decline, stop, empty histories and owned BigFloat undo" begin
 JS=JSimplex;F=OptionalPresolveFixtures
 for T in (Float32,Float64,BigFloat)
  p=F.model(T);base=JS.identity_presolve(p);h=JS._PostsolveHistory(T);o=F.options(T,(true,true,true);scaling=:off)
  @test JS._with_optional_presolve(base,h,o;stop_requested=()->true)===base
  @test isempty(h.metadata)
  r=JS._with_optional_presolve(base,h,o)
  run=F.run(r.problem,o)
  @test run.status==OPTIMAL
  bad=JS.DualRunResult{T}(run.status,run.objective_value,run.primal,run.iterations,run.refactorizations,run.message,run.basis,nothing)
  b,x=JS._postsolve_with_dual(h,r,JS.identity_scaling(r.problem),bad,o)
  @test isnothing(b)&&isnothing(x)
  @test isempty(h.metadata) && (isnothing(r.tail_history)||isempty(r.tail_history.metadata))
  empty=LinearProblem(spzeros(T,0,0),T[])
  base=JS.identity_presolve(empty)
  @test JS._with_optional_presolve(base,JS._PostsolveHistory(T),o)===base
 end
 p=setprecision(BigFloat,256) do
  LinearProblem(sparse(BigFloat[1 1]),BigFloat[1,1];row_lower=BigFloat[7],row_upper=BigFloat[8],column_lower=BigFloat[5,0],column_upper=BigFloat[5,5])
 end
 setprecision(BigFloat,64) do
  o=F.options(BigFloat,(false,true,false);scaling=:off)
  r=JS._with_optional_presolve(JS.identity_presolve(p),JS._PostsolveHistory(BigFloat),o)
  @test r.column_step.undo[1].donor_lower.value !== p.column_lower[2].value
  @test precision(r.column_step.undo[1].donor_lower.value)==256
  @test precision(BigFloat)==64
 end
end
