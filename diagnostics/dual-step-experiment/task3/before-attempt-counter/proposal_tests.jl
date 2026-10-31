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

@testset "Task3 receipt expiry, real weight writes, capacity and stop" begin
    e=proposal_case(reshape([1.],1,1),[1.],[1.];weights=[1.,0.25]).e
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.masks[2]&0x08!=0 && e.proposal.values[4][2]==1.
    @test e.ws.pricing_weights[2]==0.25 && full_simulated_oracle(e)
    rhs=ones(1)
    @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
    @test E.validate_proposal!(e).reason==E.InvalidState
    e=proposal_case(reshape([1.],1,1),[1.],[1.];time_limit=0.).e
    @test E.propose_step!(e).reason==E.Stopped
    @test e.counters.btran==0 && !e.proposal.valid
    e=proposal_case(reshape([1.],1,1),[1.],[1.]).e
    e.proposal.epoch=typemax(UInt32)
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.counts.metadata_resets==2length(e.ws.costs)
    @test full_simulated_oracle(e)
    # Source ownership/immutable matrix is preserved for an actual pending step.
    c=proposal_case(ones(1,3),ones(3),[2.5];upper=ones(3));before=snapshot(c.source);a=copy(c.A.nzval)
    @test E.propose_step!(c.e).reason==E.Ready
    @test isequal(snapshot(c.source),before) && c.A.nzval==a
end
@testset "Task3 general basis and nonzero original multiplier" begin
    c=general_proposal_case([2. 1.;0. 1.],reshape([-2.,0.],2,1),[2.,1.,-1.],[-2.,0.]);e=c.e
    @test factor_matches_committed_basis(e)
    before=proposal_snapshot(e);source_before=snapshot(c.source)
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.entering==3 && e.proposal.leaving==1
    @test simulated_proposal(e).x==[0.,0.,1.,-2.,0.]
    @test full_simulated_oracle(e)
    @test isequal(proposal_snapshot(e),before) && isequal(snapshot(c.source),source_before)
    @test factor_matches_committed_basis(e)
end
@testset "Task3 multirow BFRT-only and canceled basic writes" begin
    c=proposal_case([1. 1.;1. 0.],[0.,1.],[2.,0.];upper=[1.,Inf]);e=c.e
    before=proposal_snapshot(e)
    @test E.propose_step!(e).reason==E.Ready
    @test e.supports[2].values[2]==0. && e.supports[4].values[2]==-1.
    @test e.proposal.masks[4]&0x01!=0 && e.proposal.values[1][4]==1.
    @test full_simulated_oracle(e) && isequal(proposal_snapshot(e),before)
    @test e.counters.btran==1 && e.counters.ftran==1 && e.counters.bfrt_ftran==1
    c=proposal_case([1. 1.;1. -1.],[0.,1.],[2.,0.];upper=[1.,Inf]);e=c.e
    @test E.propose_step!(e).reason==E.Ready
    @test e.supports[2].values[2]==1. && e.supports[4].values[2]==-1.
    @test simulated_proposal(e).x[4]==0. && full_simulated_oracle(e)
    c=proposal_case([1. 1. 1.;1. -1. 0.],[0.,1.,2.],[3.,0.];upper=[1.,1.,Inf]);e=c.e
    @test E.propose_step!(e).reason==E.Ready
    @test e.proposal.flip_used==2 && e.supports[4].values[2]==0.
    @test simulated_proposal(e).x[5]==0. && full_simulated_oracle(e)
end
@testset "Task3 scaled raw flip underflow requests repair before BFRT" begin
    B=reshape([2.0^-1000],1,1);C=reshape([-2.0^-500,-2.0^-1000],1,2)
    e=general_proposal_case(B,C,[0.,0.,1.],[-2.0^-1000];upper=[2.0^-575,Inf]).e
    before=proposal_snapshot(e)
    @test_throws ArgumentError E._column_rhs!(e,2,2.0^-575)
    @test E.propose_step!(e).reason==E.DirectionUnreliable
    @test e.proposal.gains[2]==2.0^-75
    @test e.counters.btran==1 && e.counters.ftran==1 && e.counters.bfrt_ftran==0
    @test !e.proposal.valid && isequal(proposal_snapshot(e),before)
    # A failed validation cannot silently repeat native work in the same proposal.
    @test E.validate_proposal!(e).reason==E.InvalidState
    @test e.counters.ftran==1 && e.counters.bfrt_ftran==0
end
