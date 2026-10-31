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
