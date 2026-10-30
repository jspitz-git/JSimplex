module Task4Endpoint
using Test,JSimplex,LinearAlgebra,SparseArrays,TOML
using ..RecoveryDevexFallbackTests
const J=JSimplex
const R=RecoveryDevexFallbackTests
# Additional methods apply ONLY to the declared private test wrapper. They
# forward existing PFI work; no production method is replaced or instrumented.
function J.replace_column!(f::R.RecoveryFactor,column,row;zero_tolerance)
    J.replace_column!(f.base,column,row;zero_tolerance)
    f.updates=f.base.updates
    f
end
function J.refactorize!(f::R.RecoveryFactor,B)
    J.refactorize!(f.base,B);f.updates=f.base.updates;f
end
J._finite_updated_factor(f::R.RecoveryFactor)=J._finite_updated_factor(f.base)
J.copy_basis_factorization(f::R.RecoveryFactor)=R.wrap(J.copy_basis_factorization(f.base),0)
function fixture(::Type{T}) where T
    # min x1: x>=0, x1>=1, x2>=0. Initial slack basis -I is dual feasible,
    # backward-error reliable and primal infeasible in row1. Optimum=(1,0),1.
    p=J.LinearProblem(sparse(Matrix{T}(I,2,2)),T[1,0];row_lower=T[1,0])
    options=J.SolverOptions(T;verbose=false,time_limit=Inf,pricing=:auto,presolve=false)
    policy=J.NumericalPolicy(T;solve_refinement=false,recovery=false,adaptive_refactor=false,refactor_timing=false,hypersparse=false)
    diag=J.SimplexDiagnostics(;kernel_timing=true)
    context=J.SimplexProgressContext(p;diagnostics=diag,numerical_policy=policy)
    factor=R.wrap(J._basis_factorization(sparse(-Matrix{T}(I,2,2)),options),0)
    states=vcat(fill(J.AT_LOWER,2),fill(J.BASIC,2))
    ws=J.SimplexWorkspace(p,options,context,vcat(p.objective,zeros(T,2)),
        vcat(p.column_lower,p.row_lower),vcat(p.column_upper,p.row_upper),J.Basis([3,4],states),
        zeros(T,4),T[1,0,0,0],ones(T,4),falses(4),factor,J.SimplexScratch(T,2,4),
        0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
    state=J.PricingState(T);state.algorithm=:dual;ws.scratch.pricing=state
    J.reset_devex!(ws)
    c=J.checkpoint_basis(ws);builder=R.Builder{typeof(factor)}(0,1,nothing,nothing)
    (;ws,c,builder)
end
stats(t)=Dict("seconds"=>t.time,"bytes"=>t.bytes,"events"=>Base.gc_alloc_count(t.gcstats),
    "gc_seconds"=>t.gctime,"compile_seconds"=>t.compile_time,"recompile_seconds"=>t.recompile_time)
function run_case(::Type{T}) where T
    prep=@timed fixture(T);f=prep.value
    original=f.ws.factorization;before=f.ws.refactorizations
    invalid=J.BasisCheckpoint(J.Basis([3,3],f.c.basis.states),f.c.costs,f.c.lower,f.c.upper,
        f.c.working_model,f.c.phase,f.c.perturbed)
    @test_throws ArgumentError J._recovery_trial_with_pricing(f.ws,invalid,J._guard_stop_callback(()->false);algorithm=:dual,build_factor=f.builder)
    @test f.builder.calls==0 && f.ws.factorization===original && f.ws.refactorizations==before
    build=@timed J._recovery_trial_with_pricing(f.ws,f.c,J._guard_stop_callback(()->false);algorithm=:dual,build_factor=f.builder)
    pending=build.value
    weight_rows=f.builder.last.units
    @test pending isa J._RecoveryTrialResult && pending.devex_fallback && pending.failed_weight_row==1
    @test f.ws.factorization===original && !f.ws.dual_devex_fallback
    @test f.builder.calls==1 && f.ws.refactorizations==before+1
    @test (f.builder.last.forwards,f.builder.last.backwards,f.builder.last.units,f.builder.last.corrections)==(1,3,1,1)
    # Separate diagnostic-only owned state clone, not another recovery solve.
    # The shared factor is read-only for these quality/reset component calls.
    component_prep=@timed begin
        probe=J._candidate_workspace(pending.workspace)
        J._copy_pricing_state!(probe,f.ws)
        probe.scratch.recovery_active=true
        probe
    end
    probe=component_prep.value;count=(f.builder.last.forwards,f.builder.last.backwards)
    revalidation=@timed (J._finite_workspace(probe) && J._recomputed_basis_reliable(probe))
    @test revalidation.value
    reset=@timed J._prepare_recovery_devex!(probe)
    @test reset.value===nothing && J._weight_pricing(probe,:dual)==:devex
    @test (f.builder.last.forwards,f.builder.last.backwards)==count
    @test J._publish_recovery!(f.ws,pending,:repair,J._guard_stop_callback(()->false))
    @test J._weight_pricing(f.ws,:dual)==:devex
    # Devex must not make an inaccurate selected row pass its actual guard.
    bad=J.PivotCandidate(1,1,-one(T),T[-1,0],T[-0.5,0])
    @test J.validate_pivot!(f.ws,bad,f.ws.progress.numerical_policy)==:refresh
    good=J.PivotCandidate(1,1,-one(T),T[-1,0],T[-1,0])
    @test J.validate_pivot!(f.ws,good,f.ws.progress.numerical_policy)==:accept
    calls=(f.builder.last.forwards,f.builder.last.backwards)
    first=J.dual_iteration!(f.ws,()->false;perturb_degenerate=false)
    @test first===nothing && f.ws.iterations==1
    @test f.ws.basis.basic_indices==[1,4] && f.ws.primal[1:2]==T[1,0]
    @test J._weight_pricing(f.ws,:dual)==:devex && J._finite_workspace(f.ws)
    @test length(f.ws.factorization.updates)==1
    terminal=J.dual_iteration!(f.ws,()->false;perturb_degenerate=false)
    @test terminal isa J.DualTermination && terminal.status==J.OPTIMAL
    @test f.ws.iterations==1
    point=copy(f.ws.primal[1:2]);witness=T[1,0]
    @test J._original_primal_feasible(f.ws.problem,point,f.ws.options.primal_tolerance)
    @test J._original_witness_certified(f.ws.problem,f.ws.options,f.ws.basis,point,witness)
    @test !J._original_witness_certified(f.ws.problem,f.ws.options,f.ws.basis,point,T[2,0])
    @test dot(f.ws.problem.objective,point)==one(T)
    Dict("type"=>string(T),"preparation"=>stats(prep),"whole_fallback"=>stats(build),
        "component_preparation"=>stats(component_prep),"component_revalidation"=>stats(revalidation),"component_reset"=>stats(reset),
        "attempted_weight_rows"=>weight_rows,"avoided_weight_rows"=>2-weight_rows,
        "factorizations"=>f.builder.calls,"core_and_weight_ftran"=>calls[1],"core_and_weight_btran"=>calls[2],
        "final_ftran"=>f.builder.last.forwards,"final_btran"=>f.builder.last.backwards,"iterations"=>f.ws.iterations,
        "original_primal_certified"=>true,"original_optimality_certified"=>true,"invalid_witness_rejected"=>true,
        "invalid_row_rejected"=>true,"point"=>Float64.(point),"witness"=>Float64.(witness),
        "retained_julia_bytes"=>Base.summarysize((f.ws,pending,probe)),"trajectory_changed"=>true)
end
function run(path)
    records=Dict{String,Any}[]
    @testset "TASK4_POST_FALLBACK" begin
        for T in (Float32,Float64)
            push!(records,run_case(T))
        end
    end
    ispath(path) && error("output exists")
    open(path,"w") do io;TOML.print(io,Dict("cases"=>records);sorted=true);end
end
end
