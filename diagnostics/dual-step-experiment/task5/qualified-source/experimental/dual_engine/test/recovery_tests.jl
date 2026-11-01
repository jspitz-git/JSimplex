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

@testset "Task4 correction aliases and consumed publication owner" begin
    e=commit_case(1).e;before=committed_snapshot(e)
    @test_throws ArgumentError E._correct_equation!(e,2,e.ws.factorization.work,ones(1))
    @test_throws ArgumentError E._correct_equation!(e,2,zeros(1),e.proposal.rhs.values)
    @test e.counters.corrections==0 && isequal(committed_snapshot(e),before)
    result=E.run_phase!(e);after=committed_snapshot(e)
    @test result.exportable && result.workspace===e.ws
    @test_throws ArgumentError E.write_value!(e,:primal,1,2.)
    @test E.commit_step!(e).reason==E.InvalidState && E.recover!(e,E.RowUnreliable).reason==E.InvalidState
    @test isequal(committed_snapshot(e),after)
    c=commit_case(1);flag=Ref(false);f=CommitFaultFactor(c.e.ws.factorization,:native;flag)
    e=replace_engine_factor(c.e,f;clock=ControlledClock(flag))
    @test E.propose_step!(e).reason==E.Ready
    before=committed_snapshot(e);flag[]=true
    @test E.commit_step!(e).reason==E.Stopped
    @test isequal(committed_snapshot(e),before) && e.kernels.factor_valid && f.update_calls==0
    @test !e.journal.active && e.recovery.counts.events==0
end

@testset "Task4 BFRT correction retains row and entering direction" begin
    c=proposal_case(ones(1,4),[0.,1.,2.,3.],[4.];upper=[1.,1.,1.,Inf])
    source_before=snapshot(c.source);f=CommitFaultFactor(c.e.ws.factorization,:bfrt_once);e=replace_engine_factor(c.e,f)
    before=committed_snapshot(e)
    @test E.propose_step!(e).reason==E.DirectionUnreliable
    @test e.recovery.failed_slot==3 && e.proposal.flip_used==3
    entering=copy(e.supports[2].values);entering_ticket=e.kernels.solves[2].ticket;row_ticket=e.kernels.solves[1].ticket
    @test E.recover!(e,E.DirectionUnreliable).reason==E.Ready
    @test e.proposal.valid && e.proposal.stage==0x03
    @test e.supports[2].values==entering && e.kernels.solves[2].ticket==entering_ticket && e.kernels.solves[1].ticket==row_ticket
    @test e.counters.btran==1 && e.counters.ftran==1 && e.counters.bfrt_ftran==2 && e.counters.corrections==1
    @test f.forward_calls==3 && f.transpose_calls==1 && e.recovery.counts.refactor_attempts==0
    @test isequal(committed_snapshot(e),before) && full_simulated_oracle(e)
    @test E.commit_step!(e).reason==E.Committed
    result=E.run_phase!(e)
    @test result.reason==E.PrimalFeasible && result.exportable && e.counters.accepted_pivots==1
    @test E.assert_invariants(e) && membership_matches(e) && factor_matches_committed_basis(e)
    @test isequal(snapshot(c.source),source_before)
end
