function price_audit_workspace(::Type{T}, magnitude) where T
    p = LinearProblem(sparse(T[1 1]),T[magnitude,magnitude+one(T)];row_lower=T[0],row_upper=T[1])
    w = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
    w.basis = JSimplex.Basis([1],JSimplex.VariableState[JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    JSimplex.recompute!(w;refactorize=true)
    return w
end

@testset "Price audits measure backward error without cancellation bias" begin
    for (T,power) in ((Float32,20),(Float64,40),(BigFloat,400))
        setprecision(BigFloat,512) do
            magnitude = T(2)^power
            w = price_audit_workspace(T,magnitude)
            correct = copy(w.reduced_costs)
            w.reduced_costs[2] += eps(magnitude)
            @test abs(w.reduced_costs[2]-correct[2]) > w.progress.numerical_policy.solve_tolerance
            @test JSimplex.audit_primal_values!(w)
            @test w.reduced_costs == correct
            w.reduced_costs[2] += magnitude/T(10)
            @test !JSimplex.audit_primal_values!(w)
        end
    end
    # A finite dot-product scale can overflow the working scalar type.
    w = price_audit_workspace(Float64,1e308)
    w.reduced_costs[2] += 1e292
    @test JSimplex.audit_primal_values!(w)
    @test iszero(w.reduced_costs[2])
    # The test must also retain sensitivity when the absolute residual is tiny.
    w = price_audit_workspace(Float64,0.0)
    w.reduced_costs[2] = 1e-300
    w.costs[2] = 0.0
    @test !JSimplex.audit_primal_values!(w)
    w = price_audit_workspace(Rational{BigInt},big(10)^12//1)
    w.reduced_costs[2] += 1//big(10)^8
    @test !JSimplex.audit_primal_values!(w)
end

@testset "Implicit pricing residuals match an explicit system in both directions" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        A = sparse(T[1 2 0;0 -3 4])
        B = JSimplex._PriceAuditMatrix(A)
        explicit = hcat(vcat(Matrix(transpose(A)),-Matrix{T}(I,2,2)),Matrix{T}(I,5,5))
        @test Matrix(B) == explicit
        policy = JSimplex.NumericalPolicy(T)
        for transposed in (false,true)
            rows,cols = transposed ? reverse(size(B)) : size(B)
            x = T.(1:cols)
            rhs = (transposed ? transpose(explicit) : explicit)*x
            scratch = JSimplex.SolveQualityScratch(T,rows)
            q = JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed)
            @test q.reliable
            @test iszero(q.absolute_error)
            rhs[1] += one(T)
            @test !JSimplex.solve_quality!(scratch,B,x,rhs,policy;transposed).reliable
        end
    end
    setprecision(BigFloat,512) do
        w = price_audit_workspace(BigFloat,BigFloat(2)^400)
        correct = copy(w.reduced_costs)
        w.reduced_costs[2] += eps(w.costs[1])
        setprecision(BigFloat,64) do
            @test JSimplex.audit_primal_values!(w)
            @test w.reduced_costs == correct
            @test precision(BigFloat) == 64
        end
    end
end

@testset "Verified audit corrections do not discard a valid new basis" begin
    for update in (:pfi,:forrest_tomlin,:bartels_golub,:suhl_suhl)
        p=LinearProblem(sparse([1.0 0;0 1]),[-1.0,-1.0];row_upper=[1.0,1.0])
        policy=JSimplex.NumericalPolicy(Float64;incremental_primal_pivots=true)
        d=JSimplex.SimplexDiagnostics()
        w=JSimplex.initialize_workspace(p,SolverOptions(verbose=false,pricing=:dantzig,basis_update=update);
            progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d))
        w.iterations=19
        w.reduced_costs[2]=-0.5
        @test isnothing(JSimplex._primal_iteration!(w,()->false,w.options.dual_tolerance))
        @test w.primal == [1,0,1,0]
        @test w.reduced_costs == [0,-1,-1,0]
        @test w.iterations == 20
        @test w.refactorizations == 0
        @test JSimplex.event_count(d,:pivot_rejected) == 0
        @test JSimplex.event_count(d,:pivot_completed) == 1
    end
end

