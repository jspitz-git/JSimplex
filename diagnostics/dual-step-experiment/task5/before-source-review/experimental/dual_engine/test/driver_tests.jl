@testset "Task5 truthful opt-in activation and full original results" begin
    for n in (16,64),dense in (false,true)
        p=driver_problem(n;dense);before=deepcopy(p);o=driver_options();reference=J.solve(p;options=o)
        record=E.SolveRecord();candidate=E.solve_experimental(p;options=o,record)
        println("TASK5_ACTIVATION n=",n," dense=",dense," status=",candidate.status," entries=",record.entries," commits=",record.accepted_pivots," sparse_prices=",record.sparse_prices," dense_prices=",record.dense_prices," fallbacks=",record.legacy_fallbacks," original_retries=",record.original_retries," original_cleanups=",record.original_cleanups," original_recoveries=",record.original_recoveries," iterations=",candidate.statistics.iterations," refactors=",candidate.statistics.refactorizations)
        @test candidate.status==reference.status==J.OPTIMAL
        @test isapprox(candidate.objective_value,reference.objective_value;rtol=1e-7,atol=1e-7)
        @test J._original_primal_feasible(p,candidate.primal,o.primal_tolerance)
        @test record.entries==1 && record.accepted_pivots>0 && record.legacy_fallbacks==0
        @test record.original_retries==record.original_cleanups==record.original_recoveries==0
        @test dense ? record.dense_prices>0 : record.sparse_prices>0
        @test record.exports==1 && record.imports==1 && record.result_status==candidate.status
        @test all(k->isequal(getfield(p,k),getfield(before,k)),fieldnames(typeof(p)))
        @test record.start_ns>0 && record.elapsed_seconds>=0 && record.phase_reason==E.PrimalFeasible
    end
end
@testset "Task5 zero pivots and unsupported selections stay truthful" begin
    p=J.LinearProblem(sparse(ones(1,1)),ones(1);row_lower=[0.]);r=E.SolveRecord()
    @test E.solve_experimental(p;options=driver_options(),record=r).status==J.OPTIMAL
    @test r.entries==1 && r.accepted_pivots==0
    for (p,o,observer) in ((driver_problem(2;T=Float32),driver_options(Float32),nothing),(driver_problem(2),J.SolverOptions(Float64;pricing=:devex,basis_update=:huangfu_hall,verbose=false,presolve=false),nothing),(driver_problem(2),driver_options(),(reason,ws)->nothing))
        r=E.SolveRecord();solution=E.solve_experimental(p;options=o,record=r,observer)
        @test solution.status==J.OPTIMAL
        @test r.imports==r.accepted_pivots==0 && r.reason==:unsupported
    end
    r=E.SolveRecord();p=driver_problem(1);o=J.SolverOptions(Float64;pricing=:devex,verbose=false,presolve=true)
    @test E.solve_experimental(p;options=o,record=r).status==J.OPTIMAL
    @test r.entries==0 && r.imports==0 && r.reason==:not_reached
end
@testset "Task5 fixed semantic fixture corpus" begin
    root=joinpath(@__DIR__,"..","..","..","test","fixtures","solver")
    for name in ("afiro.mps","netlib/adlittle.mps","netlib/sc50a.mps","generated/degenerate-box.mps","generated/phase-one.mps","generated/scaled-diagonal.mps"),presolve in (false,true)
        p=J.read_mps(joinpath(root,name));o=J.SolverOptions(Float64;pricing=:devex,basis_update=:pfi,simplex_strategy=:legacy,presolve,verbose=false)
        baseline=J.solve(p;options=o);r=E.SolveRecord();s=E.solve_experimental(p;options=o,record=r)
        println("TASK5_CORPUS name=",name," presolve=",presolve," reference=",baseline.status," candidate=",s.status," entries=",r.entries," commits=",r.accepted_pivots," fallbacks=",r.legacy_fallbacks," original_retries=",r.original_retries," original_cleanups=",r.original_cleanups," original_recoveries=",r.original_recoveries," elapsed=",s.statistics.elapsed_seconds," iterations=",s.statistics.iterations," refactors=",s.statistics.refactorizations)
        @test s.status==baseline.status
        if s.status==J.OPTIMAL
            @test J._original_primal_feasible(p,s.primal,o.primal_tolerance)
            @test isapprox(s.objective_value,baseline.objective_value;rtol=1e-6,atol=1e-6)
        else
            @test isnothing(s.primal) && isnothing(s.objective_value)
        end
        @test r.result_status==s.status && r.entries<=1 && r.legacy_fallbacks<=1
    end
end
@testset "Task5 default main hook, limits, events and observer provenance" begin
    p=driver_problem(2);o=driver_options();probe=MainHookProbe(0)
    @test J._solve_diagnosed(p,nothing;options=o,dual_engine=probe).status==J.OPTIMAL
    @test probe.calls==1
    r=E.SolveRecord();o=driver_options(;iteration_limit=1);s=E.solve_experimental(driver_problem(4);options=o,record=r)
    @test s.status==J.ITERATION_LIMIT && isnothing(s.primal) && r.accepted_pivots<=1
    r=E.SolveRecord();o=driver_options(;time_limit=0.);clock=J._SolveDeadline(time_ns(),0.)
    @test E.solve_experimental(p;options=o,record=r,clock).status==J.TIME_LIMIT
    @test r.imports==0
    sentinel=SingularException(73);r=E.SolveRecord()
    caught=try E.solve_experimental(p;options=driver_options(),record=r,events=event->throw(sentinel));nothing catch ex;ex end
    @test caught===sentinel && r.accepted_pivots==1
    sentinel=SingularException(74);r=E.SolveRecord()
    caught=try E.solve_experimental(p;options=driver_options(),record=r,observer=(reason,ws)->throw(sentinel));nothing catch ex;ex end
    @test caught isa J.DiagnosticObserverFailure && caught.cause===sentinel && r.imports==0
end

@testset "Task5 logical scratch export keeps actual backing owners" begin
    c=commit_case(2);e=c.e;source_before=snapshot(c.source)
    result=E.run_phase!(e);w=result.workspace;r=E.SolveRecord()
    arrays=(w.scratch.candidates,w.scratch.ratio_optional,w.scratch.flips)
    memory=map(a->getfield(getfield(a,:ref),:mem),arrays)
    values=(w.primal,w.reduced_costs,w.costs,w.pricing_weights,w.factorization)
    exported=E._legacy_workspace!(w,c.source,r)
    @test all(isempty,arrays)
    @test all(i->getfield(getfield(arrays[i],:ref),:mem)===memory[i],1:3)
    @test values===(exported.primal,exported.reduced_costs,exported.costs,exported.pricing_weights,exported.factorization)
    @test exported.progress.start_ns==c.source.progress.start_ns && exported.progress.iteration_offset==7 && exported.progress.refactorization_offset==11
    @test r.exports==1 && r.export_metadata_refreshes==1 && r.export_entries==3length(w.costs)
    @test exported.scratch.basic_mask==[state==J.BASIC for state in exported.basis.states]
    @test r.export_mask_entries==length(w.costs)+length(w.basis.basic_indices)
    @test isequal(snapshot(c.source),source_before)
    @test E.commit_step!(e).reason==E.InvalidState
end
@testset "Task5 honest legacy boundary and original cleanup accounting" begin
    p=J.LinearProblem(sparse(reshape([-1.],1,1)),[1.];row_lower=[1.]);r=E.SolveRecord();o=driver_options()
    s=E.solve_experimental(p;options=o,record=r);reference=J.solve(p;options=o)
    @test s.status==reference.status==J.INFEASIBLE
    @test isnothing(s.primal) && isnothing(s.objective_value)
    @test r.reason==:legacy_boundary && r.legacy_fallbacks==1 && r.exports==1 && r.imports==1
    @test r.repair_counts.refactor_attempts==2 && r.accepted_pivots==0
    p=driver_problem(2);r=E.SolveRecord();o=J.SolverOptions(Float64;pricing=:devex,presolve=true,verbose=false)
    s=E.solve_experimental(p;options=o,record=r)
    @test s.status==J.OPTIMAL && r.original_cleanups+r.original_retries>0
    @test r.entries==0 && r.accepted_pivots==0
end
@testset "Task5 terminal rejection and unsafe state never publish a point" begin
    p=driver_problem(1);o=driver_options();hook=TerminalFaultHook(0)
    s=J._solve_diagnosed(p,nothing;options=o,dual_engine=hook,numerical_policy=J.NumericalPolicy(Float64;max_refinements=0))
    @test hook.calls==1 && s.status==J.NUMERICAL_ERROR
    @test occursin("certificate",s.message) && isnothing(s.primal) && isnothing(s.objective_value)
    s=J._solve_diagnosed(p,nothing;options=o,dual_engine=NoPayloadHook())
    @test s.status==J.NUMERICAL_ERROR && s.message=="deliberate unsafe handoff"
    @test s.statistics.iterations==17 && s.statistics.refactorizations==9
    @test isnothing(s.primal) && isnothing(s.objective_value)
end

@testset "Task5 handoff preserves shortened safety ceiling and monitor scalars" begin
    c=commit_case(3);source=c.source;source.dual_refactorization_interval=1
    r=E.SolveRecord();r.start_ns=c.e.clock.start_ns
    handoff=E.PhaseAdapter(r,c.e.clock,E.NoEvents())(source,J._guard_stop_callback(c.e.clock))
    @test handoff.recoverable && handoff.terminal.status==J.OPTIMAL
    @test r.accepted_pivots==3 && r.repair_counts.refactor_attempts==2
    @test handoff.workspace.dual_refactorization_interval==1 && source.dual_refactorization_interval==1
    @test handoff.workspace.zero_dual_step_streak==r.zero_dual_streak
    @test handoff.workspace.scratch.last_dual_step==r.last_dual_step
    @test handoff.workspace.scratch.last_primal_step==r.last_primal_step
    @test handoff.workspace.progress.start_ns==source.progress.start_ns && r.exports==1
end

@testset "Task5 event output record cannot replace private monitor state" begin
    r=E.SolveRecord();seen=Ref{Union{Nothing,E.CompletionEvent}}(nothing)
    events=event->begin
        seen[]=event;r.zero_dual_streak=typemax(Int);r.last_dual_step=NaN;r.last_primal_step=NaN
    end
    s=E.solve_experimental(driver_problem(2);options=driver_options(),record=r,events)
    @test s.status==J.OPTIMAL && !isnothing(seen[])
    @test r.last_dual_step==seen[].dual_step && r.last_primal_step==seen[].primal_step
    @test 0<=r.zero_dual_streak<=r.accepted_pivots
end
