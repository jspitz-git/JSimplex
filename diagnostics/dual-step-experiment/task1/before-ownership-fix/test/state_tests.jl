@testset "Task1 eligibility and frozen policy" begin
    ws,clock=fixture();p=E.EnginePolicy(ws)
    @test E.eligible(ws,clock)
    @test !E.eligible(ws,()->false)
    @test !E.eligible(ws,clock;observer=(args...)->nothing)
    @test !E.eligible(first(fixture(Float32)),clock)
    @test !E.eligible(first(fixture(Float64;update=:forrest_tomlin)),clock)
    @test !E.eligible(first(fixture(Float64;pricing=:steepest_edge)),clock)
    @test (p.max_entering,p.max_leaving,p.max_rebuilds,p.max_corrections,p.stagnation_window)==(8,8,2,3,64)
    @test p.solve_tolerance==256eps(Float64)
    @test p.pivot_error_tolerance==sqrt(eps(Float64))
    @test (p.primal_tolerance,p.dual_tolerance,p.zero_tolerance,p.refactor_limit)==(ws.options.primal_tolerance,ws.options.dual_tolerance,ws.options.zero_tolerance,ws.options.refactorization_interval)
    @test_throws ArgumentError E.EnginePolicy(ws;max_entering=9)
    @test_throws ArgumentError E.EnginePolicy(ws;max_corrections=-1)
    @test_throws ArgumentError E.import_phase(ws,()->false,p)
end
@testset "Task1 private phase ownership and retained capacity" begin
    ws,clock=fixture();before=snapshot(ws);e=E.import_phase(ws,clock,E.EnginePolicy(ws));v=e.ws
    for name in (:costs,:lower,:upper,:primal,:reduced_costs,:pricing_weights,:devex_reference)
        @test getfield(v,name)!==getfield(ws,name)
        @test isequal(getfield(v,name),getfield(ws,name))
    end
    @test v.basis.basic_indices!==ws.basis.basic_indices
    @test v.basis.states!==ws.basis.states
    @test v.scratch!==ws.scratch
    @test v.factorization!==ws.factorization
    @test v.factorization.work!==ws.factorization.work
    @test v.factorization.base.factorization!==ws.factorization.base.factorization
    @test v.progress!==ws.progress
    @test v.progress.objective!==ws.progress.objective
    @test v.progress.scaling.row_factors!==ws.progress.scaling.row_factors
    @test (v.progress.start_ns,v.progress.iteration_offset,v.progress.refactorization_offset)==(clock.start_ns,7,11)
    @test e.clock===clock && v.options===ws.options
    @test v.problem===ws.problem # read-only epoch borrow, not an owner claim
    @test e.counters.phase_factor_builds==1 && e.counters.phase_factor_copies==0
    @test e.counters.row_index_builds==1
    @test v.refactorizations==ws.refactorizations+1
    N=length(v.costs);m=length(v.basis.basic_indices)
    @test length(e.proposal.values)==4 && all(a->length(a)==N,e.proposal.values)
    @test all(a->length(a)==N,e.journal.values)
    @test length(e.journal.ids)==N && length(e.journal.stamps)==N && length(e.journal.masks)==N && length(e.journal.states)==N
    @test map(q->length(q.values),e.supports)==(m,m,N,m,m)
    @test all(q->length(q.ids)==length(q.values)==length(q.stamps),e.supports)
    E.write_value!(e,:primal,v.basis.basic_indices[1],-2.)
    E.write_value!(e,:price,1,-3.)
    @test E.assert_invariants(e)
    @test isequal(snapshot(ws),before)
    @test_throws ArgumentError E.write_value!(e,:weight,1,0.)
    @test_throws ArgumentError E.write_value!(e,:cost,1,NaN)
    @test_throws ArgumentError E.import_phase(ws,clock,E.EnginePolicy(first(fixture(Float64;pricing=:dantzig))))
    # Source calls remain usable after independent factor reconstruction.
    x=zeros(m);J.forward_solve!(x,v.factorization,ones(m));@test all(isfinite,x)
    @test isequal(snapshot(ws),before)
end
@testset "Task1 source invalid state is rejected" begin
    for field in (:primal,:reduced_costs,:costs,:pricing_weights)
        ws,clock=fixture();getfield(ws,field)[end]=NaN
        @test_throws ArgumentError E.import_phase(ws,clock,E.EnginePolicy(ws))
    end
    for bad in (0.,-1.,Inf)
        ws,clock=fixture();ws.pricing_weights[end]=bad
        @test_throws ArgumentError E.import_phase(ws,clock,E.EnginePolicy(ws))
    end
    ws,clock=fixture();ws.basis.basic_indices[2]=ws.basis.basic_indices[1]
    @test_throws ArgumentError E.import_phase(ws,clock,E.EnginePolicy(ws))
end
