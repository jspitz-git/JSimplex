@testset "Task3 ratio eligibility and pending flips" begin
    cases=(
      (A=reshape([1.],1,1),c=[1.],target=[2.],upper=[Inf],entering=1,flips=0),
      (A=ones(1,4),c=[0.,1.,2.,3.],target=[4.],upper=[1.,1.,1.,Inf],entering=4,flips=3),
      (A=ones(1,3),c=ones(3),target=[2.5],upper=ones(3),entering=1,flips=2),
      (A=ones(1,4),c=[0.,1.,1.,2.],target=[2.5],upper=[1.,1.,1.,Inf],entering=2,flips=2),
      (A=ones(1,2),c=[0.,1.],target=[2.],upper=[0.,Inf],entering=2,flips=0),
      (A=reshape([1.],1,1),c=[0.],target=[1.],upper=[Inf],entering=1,flips=0))
    for c in cases
        e=proposal_case(c.A,c.c,c.target;upper=c.upper).e;before=proposal_snapshot(e)
        @test E.propose_step!(e).reason==E.Ready
        @test e.proposal.entering==c.entering
        @test e.proposal.flip_used==c.flips
        @test isequal(proposal_snapshot(e),before)
        @test full_simulated_oracle(e)
        @test e.counters.btran==1 && e.counters.ftran==1 && e.counters.bfrt_ftran==(c.flips>0 ? 1 : 0)
        @test e.proposal.counts.candidate_checks<=e.policy.max_entering
    end
    c=proposal_case(reshape([1.],1,1),[-1.],[0.];upper=[1.],states=[J.AT_UPPER]);e=c.e
    @test E.propose_step!(e).reason==E.Ready
    @test simulated_proposal(e).x[1]==0. && full_simulated_oracle(e)
    c=proposal_case(reshape([1.],1,1),[0.],[2.];lower=[-Inf],states=[J.FREE_NONBASIC]);e=c.e
    @test E.propose_step!(e).reason==E.Ready
    @test simulated_proposal(e).x[1]==2. && full_simulated_oracle(e)
end
@testset "Task3 uncertain is never an infeasibility certificate" begin
    for (a,width,target,reason) in ((1e-8,Inf,1.,E.RatioUncertain),(1e-300,1e-300,1.,E.RatioUncertain),(-1.,Inf,1.,E.Exhausted),(1.,1.,4.,E.Exhausted))
        e=proposal_case(reshape([a],1,1),[1.],[target];upper=[width]).e;before=proposal_snapshot(e)
        @test E.propose_step!(e).reason==reason
        @test !e.proposal.valid && isequal(proposal_snapshot(e),before)
        @test e.counters.ftran==0 && e.counters.bfrt_ftran==0
    end
end
@testset "Task3 maintained membership and leaving scores" begin
    e=proposal_case(Matrix{Float64}(I,2,2),ones(2),ones(2)).e
    @test E.choose_leaving(e)==1
    E.reject_leaving!(e,1)
    @test E.choose_leaving(e)==2
    E.reject_leaving!(e,2)
    @test E.choose_leaving(e)==0
    E.write_value!(e,:primal,3,-1.)
    @test E.choose_leaving(e)==1
    E.write_value!(e,:price,2,-1.) # outside future row1 support
    before=proposal_snapshot(e)
    @test E.propose_step!(e).reason==E.InvalidState
    @test members(e.invariants.dual_bad)==[2]
    @test e.counters.btran==0 && isequal(proposal_snapshot(e),before)
    e=proposal_case(Matrix{Float64}(I,2,2),ones(2),ones(2);weights=[1.,1.,4.,1.]).e
    @test E.choose_leaving(e)==2
end
