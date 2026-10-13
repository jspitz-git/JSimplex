# UNEXECUTED S2-C source. Requires a separately admitted candidate package overlay.
# Never include candidate-primal-updates.jl over an already loaded production module.
using Test, SparseArrays, LinearAlgebra, JSimplex

s2c_equal(a::Float32, b::Float32) = reinterpret(UInt32,a) == reinterpret(UInt32,b)
s2c_equal(a::Float64, b::Float64) = reinterpret(UInt64,a) == reinterpret(UInt64,b)
s2c_equal(a::Nothing, b::Nothing) = true
s2c_equal(a::Nothing, b) = false
s2c_equal(a, b::Nothing) = false
s2c_equal(a, b) = a == b
function s2c_array_equal(a,b)
    axes(a) == axes(b) && eltype(a) === eltype(b) &&
        all(i -> s2c_equal(a[i],b[i]),eachindex(a,b))
end

# All six arrays start initialized. Unused arrays remain initialized, so comparison
# also checks early-return preservation rather than reading undefined scratch.
function s2c_pair(A::SparseMatrixCSC{T,Int}, dual, predicted, rhs;
                  transposed=false, reliable=true, finite=true,
                  nonfinite_input=false, tight=false, policy=JSimplex.NumericalPolicy(T)) where T
    B=JSimplex._PriceAuditMatrix(A)
    x=JSimplex._price_audit_values(dual,predicted)
    control=vcat(dual,predicted)
    rows,cols=transposed ? reverse(size(B)) : size(B)
    @test length(x)==cols && length(rhs)==rows
    @test s2c_array_equal(x,control)
    scratch=JSimplex.SolveQualityScratch(T,rows)
    reference=JSimplex.SolveQualityScratch(T,rows)
    # Tight policy requests the existing compensated decision; no arithmetic rewrite.
    p=tight ? JSimplex.NumericalPolicy(T;solve_tolerance=T(8)*eps(T)) : policy
    q=JSimplex.solve_quality!(scratch,B,x,rhs,p;transposed)
    r=JSimplex.solve_quality!(reference,B,control,rhs,p;transposed)
    for field in (:absolute_error,:relative_error,:finite,:reliable)
        @test s2c_equal(getfield(q,field),getfield(r,field))
    end
    @test q.reliable === reliable
    @test q.finite === finite
    for field in fieldnames(typeof(scratch))
        @test s2c_array_equal(getfield(scratch,field),getfield(reference,field))
    end
    if nonfinite_input
        @test all(==(T(Inf)),scratch.residual)
        @test all(iszero,scratch.work_residual) && all(iszero,scratch.work_scale)
        @test all(iszero,scratch.terms)
        @test isempty(scratch.compensation) && isempty(scratch.error_sum)
    end
    return nothing
end

@testset "S2-C indexing, read-only storage and fallback" begin
    for T in (Float32,Float64)
        nan=T===Float32 ? reinterpret(Float32,UInt32(0x7fc00035)) :
                         reinterpret(Float64,UInt64(0x7ff8000000000035))
        for (a,b) in ((T[],T[]),(T[],T[1]),(T[1],T[]),
                      (T[-0.0,nan],T[0.0,nextfloat(zero(T))]))
            v=JSimplex._price_audit_values(a,b); control=vcat(a,b)
            @test axes(v)==axes(control) && size(v)==size(control)
            @test length(v)==length(a)+length(b) && eltype(v)===T
            @test s2c_array_equal(v,control)
            @test_throws BoundsError v[0]
            @test_throws BoundsError v[length(v)+1]
            if isempty(a) || isempty(b)
                @test v isa Vector{T}
                @test v !== a && v !== b
                @test_throws ArgumentError JSimplex._PriceAuditValues(a,b)
            else
                @test v isa JSimplex._PriceAuditValues{T}
                @test Base.IndexStyle(typeof(v))==IndexLinear()
                @test Base.mightalias(v,a) && Base.mightalias(v,b)
                @test !Base.mightalias(v,copy(a))
                # AbstractArray's fallback rejects writes (exception subtype is Base-owned).
                @test_throws Exception setindex!(v,one(T),1)
                @test s2c_array_equal(a,T[-0.0,nan])
                @test s2c_array_equal(b,T[0.0,nextfloat(zero(T))])
            end
        end
        a=T[1,2]; v=JSimplex._price_audit_values(a,a)
        @test s2c_array_equal(v,vcat(a,a)) && Base.mightalias(v,a)
        @test Base.dataids(v)==(Base.dataids(a)...,Base.dataids(a)...)
        @test JSimplex._price_audit_values(view(a,:),a) isa Vector{T}
        # Empty compensation/error_sum owners are materialized before any resize.
        for field in (:compensation,:error_sum)
            scratch=JSimplex.SolveQualityScratch(T,2); empty=getfield(scratch,field)
            v=JSimplex._price_audit_values(empty,T[1,2])
            @test v isa Vector{T} && v !== empty
            resize!(empty,2); fill!(empty,T(9))
            @test s2c_array_equal(v,T[1,2])
        end
    end
    a=Union{Float32,Float64}[1f0]; b=Union{Float32,Float64}[2.0]
    @test JSimplex._price_audit_values(a,b) isa Vector
    @test !(JSimplex._price_audit_values(a,b) isa JSimplex._PriceAuditValues)
    @test_throws ArgumentError JSimplex._PriceAuditValues(a,b)
    @test JSimplex._price_audit_values(Float32[1],Float64[2]) isa Vector{Float64}
end

@testset "S2-C nonempty ordinary owner alias rejection" begin
    # A is 1x1, B is 2x3: both parents can independently be a length-two scratch
    # owner, with the other parent length one. No foreign unsafe_wrap guarantee.
    for T in (Float32,Float64), field in (:residual,:work_residual,:work_scale,:compensation,:error_sum), side in (:dual,:predicted)
        scratch=JSimplex.SolveQualityScratch(T,2)
        owner=getfield(scratch,field); resize!(owner,2); fill!(owner,one(T))
        other=T[1]
        v=side===:dual ? JSimplex._price_audit_values(owner,other) :
                         JSimplex._price_audit_values(other,owner)
        @test Base.mightalias(owner,v)
        @test_throws ArgumentError JSimplex.solve_quality!(scratch,
            JSimplex._PriceAuditMatrix(sparse(reshape(T[2],1,1))),v,T[1,0],JSimplex.NumericalPolicy(T))
    end
end

@testset "S2-C frozen hardware quality pairs" begin
    for T in (Float32,Float64)
        A=sparse(reshape(T[2],1,1))
        s2c_pair(A,T[1],T[-1,1],T[1,0])                          # finite
        s2c_pair(A,T[1],T[-1,1],T[2,0];reliable=false)           # perturbed
        s2c_pair(A,T[1],T[-1,1],T[1,0];tight=true)               # compensated candidate
        s2c_pair(A,T[-0.0],T[0.0,-0.0],T[-0.0,0.0])            # signed zero
        nan=T===Float32 ? reinterpret(Float32,UInt32(0x7fc00035)) :
                         reinterpret(Float64,UInt64(0x7ff8000000000035))
        s2c_pair(A,T[nan],T[0,0],T[0,0];reliable=false,finite=false,nonfinite_input=true)
        s2c_pair(sparse(reshape(T[Inf],1,1)),T[1],T[0,1],T[0,0];reliable=false,finite=false,nonfinite_input=true)
        s2c_pair(A,T[1],T[0,1],T[nan,0];reliable=false,finite=false,nonfinite_input=true)
        mag=T(2)^(T===Float32 ? 20 : 40)
        s2c_pair(sparse(reshape(T[1,1],1,2)),T[mag],T[-mag,-mag,mag],T[0,0,0])
        s2c_pair(sparse(reshape(T[floatmax(T)],1,1)),T[2],T[0,2],T[0,0];reliable=false,finite=false)
        s2c_pair(sparse(reshape(T[nextfloat(zero(T))],1,1)),T[0.5],T[0,0.5],T[0,0];reliable=false)
        s2c_pair(A,T[1],T[2],T[0,1,2];transposed=true)
        s2c_pair(A,T[1],T[2],T[1,1,2];transposed=true,reliable=false)
        s2c_pair(spzeros(T,0,0),T[],T[],T[])
        s2c_pair(spzeros(T,0,2),T[],T[1,2],T[1,2])
    end
end

@testset "S2-C exact and stored precision fallback" begin
    T=Rational{BigInt}; a=T[1]; b=T[-1,1]
    @test JSimplex._price_audit_values(a,b) isa Vector{T}
    s2c_pair(sparse(reshape(T[2],1,1)),a,b,T[1,0])
    setprecision(BigFloat,256) do
        A=sparse(reshape(BigFloat[2],1,1)); a=BigFloat[1]; b=BigFloat[-1,1]
        rhs=BigFloat[1,0]; policy=JSimplex.NumericalPolicy(BigFloat)
        setprecision(BigFloat,64) do
            v=JSimplex._price_audit_values(a,b)
            @test v isa Vector{BigFloat}
            @test all(x -> precision(x)==256,v)
            @test JSimplex._stored_quality_bits(BigFloat,JSimplex._PriceAuditMatrix(A),v,rhs,policy)==256
            s2c_pair(A,a,b,rhs;policy)
            @test precision(BigFloat)==64 && rounding(BigFloat)==RoundNearest
        end
        @test precision(BigFloat)==256
    end
end

# Exact unchanged existing helper and three integration testsets follow.
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

