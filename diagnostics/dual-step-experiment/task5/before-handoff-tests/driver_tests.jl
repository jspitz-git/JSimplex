@testset "Task5 truthful opt-in activation and full original results" begin
    for n in (16,64),dense in (false,true)
        p=driver_problem(n;dense);before=deepcopy(p);o=driver_options();reference=J.solve(p;options=o)
        record=E.SolveRecord();candidate=E.solve_experimental(p;options=o,record)
        @test candidate.status==reference.status==J.OPTIMAL
        @test isapprox(candidate.objective_value,reference.objective_value;rtol=1e-7,atol=1e-7)
        @test J._original_primal_feasible(p,candidate.primal,o.primal_tolerance)
        @test record.entries==1 && record.accepted_pivots>0 && record.legacy_fallbacks==0
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
