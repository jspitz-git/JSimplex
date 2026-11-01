@testset "Task4 real same-precision correction equations" begin
    for slot in (1,2)
        c=general_proposal_case([2. 1.;0. 1.],reshape([-2.,0.],2,1),[2.,1.,-1.],[-2.,0.]);e=c.e
        rhs=slot==1 ? [1.,0.] : [1.,1.];expected=slot==1 ? [0.5,-0.5] : [0.,1.]
        approximate=expected+[2.0^-20,0.];original=copy(rhs);before=committed_snapshot(e)
        @test E._correct_equation!(e,slot,approximate,rhs).reason==E.Ready
        @test approximate==expected && rhs==original
        B=[2. 1.;0. 1.];M=slot==1 ? transpose(B) : B
        @test M*approximate==rhs
        @test e.counters.corrections==1 && (slot==1 ? e.counters.btran : e.counters.ftran)==1
        @test isequal(committed_snapshot(e),before) && E.assert_invariants(e)
    end
end
@testset "Task4 correction reuses successful dependencies" begin
    for mode in (:row_once,:direction_once)
        c=commit_case(1);f=CommitFaultFactor(c.e.ws.factorization,mode);e=replace_engine_factor(c.e,f)
        result=E.run_phase!(e)
        @test result.reason==E.PrimalFeasible && !isnothing(result.workspace)
        @test e.counters.accepted_pivots==1 && e.counters.corrections==1
        @test e.counters.btran==(mode==:row_once ? 2 : 1)
        @test e.counters.ftran==(mode==:direction_once ? 2 : 1) && e.counters.bfrt_ftran==0
        @test e.recovery.counts.refactor_attempts==0 && E.assert_invariants(e)
        @test result.workspace===e.ws && result.exportable
        @test E.run_phase!(e).reason==E.InvalidState
    end
end
@testset "Task4 bounded recurrence invalid factor and honest boundary" begin
    for mode in (:row_always,:refactor_fail)
        c=commit_case(1);f=CommitFaultFactor(c.e.ws.factorization,mode);e=replace_engine_factor(c.e,f)
        mode==:refactor_fail&&(e.kernels.factor_valid=false;E.invalidate!(e,:test_damaged_factor))
        result=E.run_phase!(e)
        @test result.reason==E.Exhausted
        @test isnothing(result.workspace) && !result.exportable
        @test e.recovery.counts.refactor_attempts==e.policy.max_rebuilds==2
        @test e.recovery.rebuilds==2 && e.counters.accepted_pivots==0
        @test e.counters.corrections<=3*(e.recovery.rebuilds+1)
        @test e.recovery.counts.events==0
    end
    e=proposal_case(reshape([-1.],1,1),[1.],[1.]).e
    result=E.run_phase!(e)
    @test result.reason==E.Exhausted && result.exportable && !isnothing(result.workspace)
    @test e.counters.legacy_boundaries==1 && e.recovery.counts.refactor_attempts==2
    @test E.run_phase!(e).reason==E.InvalidState && e.counters.legacy_boundaries==1
end
@testset "Task4 ceiling offsets local limit and cost restoration" begin
    c=commit_case(3;interval=2);e=c.e;clock=e.clock
    result=E.run_phase!(e)
    @test result.reason==E.PrimalFeasible && e.counters.accepted_pivots==3
    @test e.recovery.counts.refactor_attempts==1 && length(e.ws.factorization.updates)==1
    @test e.clock===clock && e.ws.progress.start_ns==clock.start_ns
    @test (e.ws.progress.iteration_offset,e.ws.progress.refactorization_offset)==(7,11)
    @test E.assert_invariants(e) && membership_matches(e)
    e=commit_case(3;interval=2,iteration_limit=2).e;result=E.run_phase!(e)
    @test result.reason==E.Exhausted && result.message==:iteration_limit
    @test e.counters.accepted_pivots==2 && e.recovery.counts.refactor_attempts==0 && isnothing(result.workspace)
    e=proposal_case(reshape([1.],1,1),[-5e-8],[1.]).e
    @test E.propose_step!(e).reason==E.Ready
    @test E.commit_step!(e).reason==E.Committed
    @test e.ws.perturbed && e.ws.costs[1]==0.
    before_f=e.counters.ftran
    @test E.recover!(e,:restore_costs).reason==E.Ready
    result=E.run_phase!(e)
    @test result.reason==E.PrimalFeasible && !e.ws.perturbed && e.ws.costs[1]==-5e-8
    @test e.recovery.counts.cost_restores==1 && e.counters.ftran==before_f
    @test E.assert_invariants(e) && membership_matches(e)
end
