@testset "Task3 complete planned union and proposal lifetime" begin
    e=proposal_case(ones(1,4),[0.,1.,2.,3.],[4.];upper=[1.,1.,1.,Inf]).e
    before=proposal_snapshot(e);lengths=(length(e.proposal.ids),map(length,e.proposal.values),length(e.proposal.flips))
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.valid && e.proposal.generation==e.generation
    @test length(unique(@view(e.proposal.ids[1:e.proposal.used])))==e.proposal.used
    @test all(i->e.proposal.masks[i]!=0,@view(e.proposal.ids[1:e.proposal.used]))
    @test E.validate_proposal!(e).reason==E.Ready
    @test e.counters.ftran==1 && e.counters.bfrt_ftran==1
    @test E.plan_writes!(e).reason==E.Ready
    @test isequal(proposal_snapshot(e),before)
    @test simulated_proposal(e).x==[1.,1.,1.,1.,4.]
    @test all(>(0),simulated_proposal(e).weights)
    @test full_simulated_oracle(e)
    @test E.propose_step!(e).reason==E.Ready
    @test lengths==(length(e.proposal.ids),map(length,e.proposal.values),length(e.proposal.flips))
    E.write_value!(e,:cost,1,e.ws.costs[1])
    @test E.validate_proposal!(e).reason==E.InvalidState
    @test !e.proposal.valid
end
@testset "Task3 cost shift and changed weights stay pending" begin
    e=proposal_case(reshape([1.],1,1),[-5e-8],[1.]).e;before=proposal_snapshot(e)
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.dual_step==0.
    @test e.proposal.masks[1]&0x04!=0 && e.proposal.values[3][1]==0.
    @test e.proposal.planned_perturbed
    @test isequal(proposal_snapshot(e),before) && full_simulated_oracle(e)
    e=proposal_case(reshape([floatmax(Float64)],1,1),[1.],[1.]).e;before=proposal_snapshot(e)
    @test E.propose_step!(e).reason!=E.Ready
    @test !e.proposal.valid && isequal(proposal_snapshot(e),before)
end
@testset "Task3 full-row eligibility reference and equations" begin
    for n in (8,64),kind in (:sparse,:band,:dense)
        A=Matrix{Float64}(I,n,n)
        for j in 1:n,i in 1:n
            (kind==:dense || abs(i-j)<=1 || kind==:sparse && mod(i+3j,13)==0) && i!=j && (A[i,j]=1/128)
        end
        c=proposal_case(A,ones(n),ones(n));e=c.e;before=proposal_snapshot(e)
        @test E.propose_step!(e).reason==E.Ready
        p=e.proposal
        reference=J.propose_dual_step!(c.source,copy(e.supports[3].values),p.orientation,p.violation,c.source.progress.numerical_policy)
        @test reference.outcome==:pivot
        @test J._dual_pivot_eligible(e.ws,p.entering,p.orientation*e.supports[3].values[p.entering],0.)
        @test full_simulated_oracle(e)
        @test isequal(proposal_snapshot(e),before)
        @test e.counters.btran==1 && e.counters.ftran==1 && e.counters.bfrt_ftran==0
    end
end
