@testset "Task4 commit equals independent simulated application" begin
    for multirow in (false,true)
        c=multirow ? proposal_case([1. 1.;1. 0.],[0.,1.],[2.,0.];upper=[1.,Inf]) : commit_case(3)
        e=c.e;source_before=snapshot(c.source)
        @test E.propose_step!(e).reason==E.Ready
        expected=simulated_proposal(e);row=e.proposal.leaving_row;entering=e.proposal.entering
        union_size=e.proposal.used;owned=(e.ws.primal,e.ws.reduced_costs,e.ws.costs,e.ws.pricing_weights,e.ws.basis.states)
        slot=Ref{Union{Nothing,E.CompletionEvent}}(nothing)
        @test E.commit_step!(e;event_sink=CaptureEvent(slot)).reason==E.Committed
        @test e.ws.primal==expected.x && e.ws.reduced_costs==expected.prices && e.ws.costs==expected.cost
        @test e.ws.pricing_weights==expected.weights && e.ws.basis.states==expected.states && e.ws.basis.basic_indices==expected.basis
        @test all(i->owned[i]===getfield(e.ws,(:primal,:reduced_costs,:costs,:pricing_weights)[i]),1:4)
        @test owned[5]===e.ws.basis.states
        @test E.assert_invariants(e) && membership_matches(e)
        @test e.counters.accepted_pivots==1 && e.ws.iterations==1
        @test e.recovery.counts.journal_entries==union_size && !e.journal.active
        @test e.recovery.counts.factor_updates==1 && e.recovery.counts.events==1
        @test !isnothing(slot[]) && isbits(slot[]) && slot[].entering==entering && slot[].leaving_row==row
        @test e.clock.start_ns==e.ws.progress.start_ns && isequal(snapshot(c.source),source_before)
        @test factor_matches_committed_basis(e)
    end
end
@testset "Task4 factor failure preserves point but never claims rollback" begin
    c=commit_case(1);f=CommitFaultFactor(c.e.ws.factorization,:factor_fail);e=replace_engine_factor(c.e,f)
    before=committed_snapshot(e)
    @test E.propose_step!(e).reason==E.Ready
    @test E.commit_step!(e).reason==E.FactorInvalid
    @test isequal(committed_snapshot(e),before) && membership_matches(e)
    @test !e.kernels.factor_valid && !e.journal.active && length(f.updates)==1
    counts=(f.forward_calls,f.transpose_calls)
    @test E.basis_solve!(e,:ftran,ones(1)).reason==E.FactorInvalid
    @test counts==(f.forward_calls,f.transpose_calls)
    @test e.recovery.counts.events==0 && e.counters.accepted_pivots==0
    @test E.recover!(e,E.FactorInvalid).reason==E.Ready
    result=E.run_phase!(e)
    @test result.reason==E.PrimalFeasible && !isnothing(result.workspace)
    @test e.recovery.counts.refactor_attempts==1 && E.assert_invariants(e)
    @test factor_matches_committed_basis(e)
    c=commit_case(1);f=CommitFaultFactor(c.e.ws.factorization,:foreign_fail);e=replace_engine_factor(c.e,f)
    @test E.propose_step!(e).reason==E.Ready
    before=committed_snapshot(e);caught=try E.commit_step!(e);nothing catch ex;ex end
    @test caught===f.sentinel && isequal(committed_snapshot(e),before) && !e.kernels.factor_valid
end
@testset "Task4 first middle last numeric failures restore all fields" begin
    for position in (:first,:middle,:last)
        c=proposal_case(ones(1,4),[0.,1.,2.,3.],[4.];upper=[1.,1.,1.,Inf]);e=c.e
        @test E.propose_step!(e).reason==E.Ready
        fields=sum(count_ones(e.proposal.masks[e.proposal.ids[k]]&0x0f) for k in 1:e.proposal.used)
        at=position==:first ? 1 : position==:last ? fields : max(1,fields÷2)
        publisher=ThrowingPublisher(0,at,ErrorException("numeric sentinel"));before=committed_snapshot(e)
        caught=try E._commit_step!(e,publisher,E.NoEvents());nothing catch ex;ex end
        @test caught===publisher.sentinel && publisher.writes==at
        @test isequal(committed_snapshot(e),before) && membership_matches(e)
        @test !e.kernels.factor_valid && !e.invariants.valid && !e.journal.active
        @test e.counters.accepted_pivots==0 && e.recovery.counts.events==0
        @test e.recovery.counts.undo_entries>0
        E.restore_journal!(e)
        @test isequal(committed_snapshot(e),before)
    end
end
@testset "Task4 refusal deadline wrap and postcommit exception" begin
    e=commit_case(1).e;@test E.propose_step!(e).reason==E.Ready
    before=committed_snapshot(e);resize!(e.journal.ids,0)
    @test E.commit_step!(e).reason==E.InvalidState
    @test isequal(committed_snapshot(e),before) && e.recovery.counts.factor_updates==0
    e=commit_case(1).e;@test E.propose_step!(e).reason==E.Ready
    E.write_value!(e,:cost,1,e.ws.costs[1]);before=committed_snapshot(e)
    @test E.commit_step!(e).reason==E.InvalidState
    @test isequal(committed_snapshot(e),before) && e.recovery.counts.factor_updates==0
    c=commit_case(1);flag=Ref(false);f=CommitFaultFactor(c.e.ws.factorization,:deadline;flag)
    e=replace_engine_factor(c.e,f;clock=ControlledClock(flag));@test E.propose_step!(e).reason==E.Ready
    before=committed_snapshot(e)
    @test E.commit_step!(e).reason==E.Stopped
    @test isequal(committed_snapshot(e),before) && !e.kernels.factor_valid && e.recovery.counts.events==0
    @test f.refactor_calls==0
    e=commit_case(1;time_limit=0.).e
    @test E.run_phase!(e).reason==E.Stopped
    @test e.recovery.counts.factor_updates==0
    e=commit_case(1).e;e.generation=typemax(UInt64)
    @test E.propose_step!(e).reason==E.Ready
    @test E.commit_step!(e).reason==E.Committed
    @test e.generation==1 && E.assert_invariants(e) && membership_matches(e)
    e=commit_case(1).e;@test E.propose_step!(e).reason==E.Ready
    sentinel=SingularException(42);caught=try E.commit_step!(e;event_sink=ThrowEvent(sentinel));nothing catch ex;ex end
    @test caught===sentinel && e.counters.accepted_pivots==1 && e.ws.iterations==1
    @test !e.journal.active && e.kernels.factor_valid && E.assert_invariants(e)
end
