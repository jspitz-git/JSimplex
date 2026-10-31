@testset "Task1 exact maintained violation sets" begin
    ws,clock=fixture();ws.reduced_costs[1]=-1.;ws.reduced_costs[3]=-2.
    # Nonadjacent bad prices must survive even if a future row coefficient is0.
    e=E.import_phase(ws,clock,E.EnginePolicy(ws))
    @test members(e.invariants.dual_bad)==[1,3]
    @test E.assert_invariants(e)
    for (field,i,value) in ((:price,1,0.),(:price,3,1.),(:primal,e.ws.basis.basic_indices[2],2.),(:primal,e.ws.basis.basic_indices[1],1.),(:price,2,-0.5),(:price,2,-0.0))
        E.write_value!(e,field,i,value)
        a,b=independent_members(e.ws)
        @test members(e.invariants.primal_bad)==a
        @test members(e.invariants.dual_bad)==b
        @test E.assert_invariants(e)
    end
    # Declared bound/state changes explicitly reclassify; none implies a solve.
    e.ws.basis.states[1]=J.AT_UPPER;e.ws.reduced_costs[1]=1.;E.classify_variable!(e,1)
    @test 1 in members(e.invariants.dual_bad)
    e.ws.basis.states[1]=J.FREE_NONBASIC;e.ws.reduced_costs[1]=-1.;E.classify_variable!(e,1)
    @test 1 in members(e.invariants.dual_bad)
    e.ws.lower[1]=J.Bound(2.);e.ws.upper[1]=J.Bound(2.);E.classify_variable!(e,1)
    @test !(1 in members(e.invariants.dual_bad))
    @test E.assert_invariants(e)
    rebuilds=e.counters.invariant_rebuilds
    for k in 1:100;E.write_value!(e,:price,2,isodd(k) ? -1. : 0.);end
    @test e.counters.invariant_rebuilds==rebuilds
    @test E.assert_invariants(e)
    e.proposal.valid=true;e.proposal.generation=e.generation
    E.invalidate!(e,:unknown_writer)
    @test !e.proposal.valid && !e.invariants.valid
    @test !E.assert_invariants(e)
    E.rebuild_invariants!(e);@test E.assert_invariants(e)
    e.generation=typemax(UInt64);e.proposal.valid=true
    E.write_value!(e,:price,2,0.)
    @test e.generation==UInt64(1) && !e.proposal.valid
    E.rebuild_invariants!(e);@test E.assert_invariants(e)
end
@testset "Task1 reusable sparse sets and stamped support" begin
    s=E.SparseSet(8);owners=(s.ids,s.position)
    for i in (2,7,2,4);E.set_present!(s,i,true);end
    @test members(s)==[2,4,7]
    E.set_present!(s,2,false);E.set_present!(s,2,true)
    @test members(s)==[2,4,7] && s.used==3
    @test (s.ids,s.position)===owners || (s.ids===owners[1] && s.position===owners[2])
    @test_throws BoundsError E.set_present!(s,9,true)
    values=zeros(8);q=E.StampedScratch(values);ids=q.ids;stamps=q.stamps
    E.set_scratch!(q,2,1.);E.add_scratch!(q,2,-1.);E.add_scratch!(q,2,2.)
    @test q.used==1 && q.values[2]==2.
    E.set_scratch!(q,7,nextfloat(0.));E.set_scratch!(q,4,-0.0)
    E.compact_scratch!(q)
    @test sort(collect(@view q.ids[1:q.used]))==[2,7]
    @test q.values[7]==nextfloat(0.)
    E.clear_scratch!(q)
    @test q.used==0 && all(iszero,values)
    @test q.ids===ids && q.stamps===stamps && length(ids)==8 && length(stamps)==8
    q.epoch=typemax(UInt32);fill!(q.stamps,typemax(UInt32));E.clear_scratch!(q)
    @test q.epoch==UInt32(1) && all(iszero,q.stamps)
    E.set_scratch!(q,1,3.);@test q.used==1 && q.values[1]==3.
    @test_throws ArgumentError E.add_scratch!(q,1,Inf)
    @test q.values[1]==3.
end
