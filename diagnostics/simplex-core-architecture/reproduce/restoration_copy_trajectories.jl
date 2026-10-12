using Test
# Reuse fixture definitions, not accepted measurements or counted instrumentation.
const CENSUS_TEXT=read(joinpath(@__DIR__,"objective_restore_census.jl"),String)
include_string(Main,first(split(CENSUS_TEXT,"main(only(ARGS))")),"S5-B fixture definitions")
function dense_case(algorithm,backend,dense)
 A=dense ? [4.0 1 1;1 4 1;1 1 4] : Matrix{Float64}(I,3,3)
 p=LinearProblem(sparse(A),[-1.0,-2,-3];row_upper=ones(3))
 events=Any[];armed=Ref(false)
 observer=(reason,w)->(armed[] && push!(events,Dict("reason"=>string(reason),"state"=>state(w)));nothing)
 policy=JS.NumericalPolicy(Float64;numerical_profile=:checked,simplex_strategy=:legacy)
 o=SolverOptions(;algorithm,basis_update=:huangfu_hall,basis_refactorization=backend,
      scaling=:off,verbose=false,iteration_limit=100,time_limit=30.0)
 w=JS.initialize_workspace(p,o;progress=JS.SimplexProgressContext(p;numerical_policy=policy,
      diagnostics=JS.SimplexDiagnostics(;observer)))
 j=JS.PerturbationJournal(w);j.active_costs[1]+=0.125;j.active=true
 w.scratch.perturbations=j;w.costs=j.active_costs;w.perturbed=true
 JS.recompute!(w);armed[]=true
 result=JS.run_from_basis!(w,JS.SimplexRunBudget(w),policy,()->false)
 @assert result.status==OPTIMAL && JS._original_primal_feasible(p,result.primal,o.primal_tolerance)
 @assert !JS._has_active_perturbations(w.scratch.perturbations)
 Dict("algorithm"=>string(algorithm),"backend"=>string(backend),"dense"=>dense,
 "status"=>string(result.status),"objective"=>scalar(result.objective_value),"primal"=>vals(result.primal),
 "events"=>events,"final"=>state(w),"original_feasible"=>true)
end
function cases_all()
 modes=(:original,:cost_owned,:cost_detached,:cost_unowned,:bounds_owned,:bounds_alien,:expired,:stop_restored,:observer_throw)
 cases=[(T,a,b,p,m) for T in (Float64,Rational{BigInt}) for a in (:primal,:dual)
   for b in (:native,:markowitz) for p in (:native,:checked) for m in modes]
 rows=[first(run_case(c...,false)) for c in cases]
 append!(rows,[dense_case(a,b,d) for a in (:primal,:dual) for b in (:native,:markowitz) for d in (false,true)])
 rows
end
function main_pairs(out)
 candidate=parsed("simplex_perturbation.jl","function restore_perturbations!")
 src=read(joinpath(ROOT,"test/restoration_alias_copy_tests.jl"),String)
 old,_=Meta.parse(src,first(only(findall("function restoration_legacy_copy!",src))))
 baseline=deepcopy(candidate);baseline.args[2]=old.args[2]
 Core.eval(JS,baseline)
 controls=Base.invokelatest(cases_all)
 Core.eval(JS,candidate)
 current=Base.invokelatest(cases_all)
 @testset "Exact restoration baseline/candidate trajectories" begin
  @test length(controls)==length(current)==152
  for (a,b) in zip(controls,current);@test isequal(a,b);end
 end
 @assert !ispath(out)
 open(out,"w") do io
  TOML.print(io,Dict("pairs"=>current,"pair_count"=>length(current),"exact_selected_state_events"=>true,
   "source_sha256"=>bytes2hex(sha256(read(joinpath(ROOT,"src/simplex_perturbation.jl")))),
   "script_sha256"=>bytes2hex(sha256(read(@__FILE__)))))
 end
end
Base.invokelatest(main_pairs,only(ARGS))
