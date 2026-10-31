@testset "Task2 original-basis solves and pricing" begin
    for n in (8,64),kind in (:sparse,:band,:dense)
        c=kernel_case(kind,n);e=c.e;A0=copy(c.A.nzval)
        x=[(-1.)^i/8 for i in 1:n];rhs=c.B*x;original=copy(rhs)
        @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
        @test norm(e.supports[2].values-x,Inf)<=1e-12
        @test E.check_direction!(e,rhs,1.).reason==E.Ready
        @test rhs==original
        unit=zeros(n);unit[3]=1
        @test E.basis_solve!(e,:btran,unit).reason==E.Ready
        rho=e.supports[1].values
        @test norm(transpose(c.B)*rho-unit,Inf)<=1e-12
        @test E.check_row!(e,3).reason==E.Ready
        @test E.price_row!(e).reason==E.Ready
        expected=zeros(length(e.ws.costs));J._csc_price!(expected,c.A,rho)
        @test isapprox(e.supports[3].values,expected;atol=1e-13,rtol=1e-13)
        @test c.A.nzval==A0
        @test e.counters.ftran==1 && e.counters.btran==1
        @test e.kernels.counts.output_capture_entries==2n
        @test e.kernels.counts.row_checks==1 && e.kernels.counts.direction_checks==1
    end
end
@testset "Task2 both pricing routes on one matrix" begin
    c=kernel_case(:diagonal,64);e=c.e;rhs=zeros(64);rhs[1]=4
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    @test E.price_row!(e).reason==E.Ready
    @test e.kernels.last_pricing_mode==:sparse
    expected=zeros(length(e.ws.costs));J._csc_price!(expected,c.A,e.supports[1].values)
    @test e.supports[3].values==expected
    @test E.basis_solve!(e,:btran,fill(4.,64)).reason==E.Ready
    @test E.price_row!(e).reason==E.Ready
    @test e.kernels.last_pricing_mode==:dense
    J._csc_price!(expected,c.A,e.supports[1].values)
    @test e.supports[3].values==expected
    @test e.counters.row_index_builds==1
    @test e.kernels.counts.sparse_prices==1 && e.kernels.counts.dense_prices==1
end
@testset "Task2 complete direction residual and scale coverage" begin
    for kind in (:diagonal,:band,:dense)
        c=kernel_case(kind,8);e=c.e;q=e.supports[2]
        cases=([0.,1.,-1.,0.,0.,0.,0.,0.],fill(nextfloat(0.),8),zeros(8),[1.,-1.,1.,-1.,0.,0.,0.,0.])
        for d in cases,err in (0.,1e-12,1e-4)
            rhs=c.B*d;rhs[end]+=err
            E.capture_output!(q,d)
            actual=E.direction_residual_ok!(e,q,rhs,1.)
            expected=full_direction_reference(c.source,d,rhs,1.)
            @test actual==expected
            @test !actual || setprecision(BigFloat,256) do
                r=BigFloat.(Matrix(c.B))*BigFloat.(d)-BigFloat.(rhs)
                maximum(abs,r)<=BigFloat(1e-6)
            end
        end
        # Zero final residual must not erase absolute-scale rows.
        d=ones(8);rhs=c.B*d;E.capture_output!(q,d)
        @test E.direction_residual_ok!(e,q,rhs,1.)
        @test e.supports[5].used==8
        @test all(>(0),e.residual_scale)
        d[2]=NaN
        @test_throws ArgumentError E.capture_output!(q,d)
        @test q.used==0 && all(iszero,q.values)
    end
    c=kernel_case(:diagonal,8);e=c.e;q=e.supports[2]
    for err in (prevfloat(sqrt(eps(Float64))),sqrt(eps(Float64)),nextfloat(sqrt(eps(Float64))))
        d=zeros(8);d[1]=err/4;rhs=zeros(8);E.capture_output!(q,d)
        @test E.direction_residual_ok!(e,q,rhs,1.)==full_direction_reference(c.source,d,rhs,1.)
    end
end
@testset "Task2 provenance alias and mutation boundaries" begin
    c=kernel_case(:band,8);e=c.e;rhs=ones(8)
    @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
    @test E.check_direction!(e,rhs,1.).reason==E.Ready
    rhs[1]=2
    @test E.check_direction!(e,rhs,1.).reason==E.DirectionUnreliable
    @test_throws ArgumentError E.basis_solve!(e,:ftran,@view(e.supports[2].values[:]))
    @test_throws ArgumentError E.basis_solve!(e,:ftran,e.ws.factorization.work)
    @test_throws DimensionMismatch E.basis_solve!(e,:ftran,ones(7))
    @test_throws ArgumentError E.basis_solve!(e,:other,ones(8))
    u=zeros(8);u[2]=1
    @test E.basis_solve!(e,:btran,u).reason==E.Ready
    @test E.check_row!(e,3).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,u).reason==E.Ready
    E.set_scratch!(e.supports[1],1,2.)
    @test E.price_row!(e).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,u).reason==E.Ready
    E.write_value!(e,:price,9,0.)
    @test E.check_row!(e,2).reason==E.RowUnreliable
    E.invalidate!(e,:repair);@test E.basis_solve!(e,:ftran,ones(8)).reason!=E.Ready
    E.rebuild_invariants!(e)
    @test E.basis_solve!(e,:bfrt,ones(8)).reason==E.Ready
    @test e.counters.bfrt_ftran==1
    @test E.check_direction!(e,e.kernels.solves[3].rhs,1.;kind=:bfrt).reason==E.Ready
    q=E.StampedScratch(zeros(8));E.capture_output!(q,[0.,1.,-0.,nextfloat(0.),0.,0.,0.,0.])
    @test q.used==2 && length(q.ids)==8
    E.capture_output!(q,q.values);@test q.used==2
    @test_throws ArgumentError E.capture_output!(q,@view(q.values[:]))
    # No external caller reference is retained as the saved solve RHS.
    @test all(r->r.rhs!==rhs,e.kernels.solves)
end
@testset "Task2 failed attempts and stop accounting" begin
    c=kernel_case(:diagonal,8)
    for (kind,field) in ((:btran,:btran),(:ftran,:ftran),(:bfrt,:bfrt_ftran))
        e=throwing_engine(c.e,SingularException(31));before=getfield(e.counters,field)
        @test E.basis_solve!(e,kind,ones(8)).reason==E.FactorInvalid
        @test getfield(e.counters,field)==before+1
        @test !e.kernels.factor_valid
        E.rebuild_invariants!(e) # numeric rebuild is not a factor repair
        @test E.basis_solve!(e,kind,ones(8)).reason==E.FactorInvalid
        @test getfield(e.counters,field)==before+1
        c=kernel_case(:diagonal,8)
    end
    sentinel=ErrorException("kernel sentinel");e=throwing_engine(c.e,sentinel)
    caught=try E.basis_solve!(e,:ftran,ones(8));nothing catch ex;ex end
    @test caught===sentinel && e.counters.ftran==1
    expired=kernel_case(:diagonal,8;time_limit=0.).e
    @test E.basis_solve!(expired,:ftran,ones(8)).reason==E.Stopped
    @test expired.counters.ftran==0
end

@testset "Task2 ordinary indexed residual union and overflow" begin
    # Zero RHS has no producer support; a nonzero direction must still visit
    # every affected original-B row even when the RHS support is empty.
    c=kernel_case(:band,8);e=perturbed_engine(c.e,1.);rhs=zeros(8)
    @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
    @test e.kernels.solves[2].rhs_used==0
    @test E.check_direction!(e,e.kernels.solves[2].rhs,1.).reason==E.DirectionUnreliable
    @test e.supports[5].used>=3
    @test all(i->e.supports[5].stamps[i]==e.supports[5].epoch,1:3)
    @test all(i->e.residual_scale[i]>0,1:3)
    # A genuine ordinary solve with RHS[2]==0 still needs the canceled row's
    # two nonzero basis contributions in its absolute-scale/error check.
    e=c.e;d=zeros(8);d[1]=1.;d[2]=-1/2048;rhs=c.B*d
    @test rhs[2]==0.
    @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
    r=e.kernels.solves[2]
    @test !(2 in @view(r.rhs_ids[1:r.rhs_used]))
    @test E.check_direction!(e,r.rhs,1.).reason==E.Ready
    @test e.supports[5].stamps[2]==e.supports[5].epoch && e.residual_scale[2]>0
    c=kernel_case(:diagonal,8);e=perturbed_engine(c.e,floatmax(Float64))
    @test E.basis_solve!(e,:ftran,zeros(8)).reason==E.Ready
    @test E.check_direction!(e,e.kernels.solves[2].rhs,1.).reason==E.DirectionUnreliable
    @test !isfinite(e.supports[5].values[1]) && !isfinite(e.residual_scale[1])
    # The same owned residual buffers can be cleared after a failed check.
    @test E.basis_solve!(e,:bfrt,[-floatmax(Float64),0.,0.,0.,0.,0.,0.,0.]).reason==E.Ready
    # Independently exercise a clean check after prior overflow, using the cold
    # component with coherent support; no forged receipt is treated as genuine.
    q=e.supports[2];E.capture_output!(q,zeros(8))
    @test E.direction_residual_ok!(e,q,zeros(8),1.)
    @test all(iszero,e.supports[5].values) && all(iszero,e.residual_scale)
    c=kernel_case(:diagonal,64;extra=:overflow);e=c.e;before=copy(c.A.nzval)
    rhs=zeros(64);rhs[1]=8
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    @test E.price_row!(e).reason==E.RowUnreliable
    @test e.supports[3].used==0 && all(iszero,e.supports[3].values)
    @test e.supports[3].evidence_generation==0 && e.kernels.price_ticket==0
    rhs[1]=1
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    @test E.price_row!(e).reason==E.Ready
    @test all(isfinite,e.supports[3].values) && c.A.nzval==before
end
@testset "Task2 nonordered CSC falls back without rebuilding" begin
    c=kernel_case(:diagonal,64;extra=:nonordered);e=c.e
    @test !e.rows.ordered_csc
    rhs=zeros(64);rhs[1]=4
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    @test E.price_row!(e).reason==E.Ready
    @test e.kernels.last_pricing_mode==:dense && e.counters.row_index_builds==1
    expected=zeros(length(e.ws.costs));J._csc_price!(expected,c.A,e.supports[1].values)
    @test e.supports[3].values==expected
end
@testset "Task2 receipt identity and ticket lifetime" begin
    c=kernel_case(:diagonal,8);e=c.e;rhs=zeros(8);rhs[1]=1
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    r=e.kernels.solves[1];r.owner=Ref{Nothing}(nothing)
    @test E.price_row!(e).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    r.output=copy(r.output)
    @test E.check_row!(e,1).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    r.factor_id=UInt(0)
    @test E.price_row!(e).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    e.kernels.latest=Base.setindex(e.kernels.latest,r.ticket+UInt64(1),1)
    @test E.check_row!(e,1).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    e.kernels.next_ticket=typemax(UInt64)
    @test E.basis_solve!(e,:ftran,rhs).reason==E.Ready
    @test e.kernels.solves[2].ticket==1
    @test E.check_direction!(e,e.kernels.solves[2].rhs,1.).reason==E.Ready
    @test E.price_row!(e).reason==E.RowUnreliable
    @test E.basis_solve!(e,:btran,rhs).reason==E.Ready
    # Replacing the actual private owner, rather than only the recorded ID,
    # invalidates an old receipt. The modified phase is then discarded.
    e.ws.factorization=J._basis_factorization(c.B,e.ws.options)
    @test E.check_row!(e,1).reason==E.RowUnreliable
    E.invalidate!(e,:unknown_factor_writer)
    @test E.basis_solve!(e,:ftran,rhs).reason!=E.Ready
    # Unknown scratch/index/model mutation is NOT repaired by invariant rebuild;
    # reconstruct from an unmodified source instead of recertifying that phase.
    fresh=E.import_phase(c.source,c.e.clock,E.EnginePolicy(c.source))
    @test fresh.owner!==e.owner && all(iszero,fresh.supports[3].values)
    @test E.basis_solve!(fresh,:btran,rhs).reason==E.Ready
    @test E.price_row!(fresh).reason==E.Ready
end
