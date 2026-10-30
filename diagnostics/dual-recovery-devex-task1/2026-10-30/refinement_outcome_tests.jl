# Prospective ordinary tests, UNEXECUTED during Task1 source preparation.
module RefinementOutcomeTests
using Test, LinearAlgebra, SparseArrays
using JSimplex
const J = JSimplex

# Declared fault outputs test the real refinement boundary; they are not
# evidence about numerical fidelity of the delegated LU or any native backend.
mutable struct CorrectionProbe{T,F}
    factor::F
    updates::Vector{J.PackedEta{T}}
    mode::Symbol
    forwards::Int
    backwards::Int
    failure::Union{Nothing,Exception}
end
function probe_solve!(dest,f::CorrectionProbe{T},rhs,transposed) where T
    transposed ? (f.backwards+=1) : (f.forwards+=1) # before genuine entry, including throws
    transposed ? ldiv!(dest,transpose(f.factor),rhs) : ldiv!(dest,f.factor,rhs)
    if f.mode==:zero
        fill!(dest,zero(T))
    elseif f.mode==:negative
        dest .*= -one(T)
    elseif f.mode==:half
        dest ./= T(2)
    elseif f.mode==:infinite
        fill!(dest,T(Inf))
    elseif f.mode==:huge
        fill!(dest,ldexp(one(T),T===Float32 ? 127 : 1023))
    elseif f.mode==:throw
        throw(f.failure)
    end
    dest
end
J.forward_solve!(dest::Vector{T},f::CorrectionProbe{T},rhs::Vector{T}) where T = probe_solve!(dest,f,rhs,false)
J.transpose_solve!(dest::Vector{T},f::CorrectionProbe{T},rhs::Vector{T}) where T = probe_solve!(dest,f,rhs,true)

mutable struct StopProbe{W}
    ws::W
    calls::Int
    true_at::Int
    throw_at::Int
    poison_basis_at::Int
    failure::Union{Nothing,Exception}
end
function (s::StopProbe)()
    s.calls+=1
    if s.calls==s.poison_basis_at
        s.ws.scratch.basis_matrix.nzval[1]=eltype(s.ws.costs)(Inf)
    end
    s.calls==s.throw_at && throw(s.failure)
    s.calls==s.true_at
end
mutable struct ObserverProbe
    calls::Int
    reason::Symbol
    failure::Union{Nothing,Exception}
end
function (p::ObserverProbe)(reason,ws)
    p.calls+=1
    reason==p.reason && throw(p.failure)
    nothing
end

const SIMPLE_CASES = (:reliable,:reliable_zero_limit,:repaired,:repaired_last_iteration,:dense_repaired,:unchanged,:not_improved,
    :zero_limit,:improved_limit,:initial_nonfinite,:initial_nan,:nonfinite_correction,
    :nonfinite_trial,:nonfinite_trial_quality,:stop_before,:stop_adoption,
    :throw_correction,:throw_stop,:throw_observer_attempt,:throw_observer_correction,
    :discarded_nonfinite_cleanup)
function scenario(name,::Type{T}) where T
    B=Matrix{T}(I,2,2);x=zeros(T,2);rhs=T[1,0]
    mode=:real;limit=3;refine=false;want=:reliable;invalid=false;calls=0;stops=0
    true_at=0;throw_at=0;poison=0;observer_reason=:never;failure=nothing;identity_delegate=false
    expected_point=T[1,0]
    if name in (:reliable,:reliable_zero_limit)
        x=T[1,0]
        name==:reliable_zero_limit && (limit=0)
    elseif name in (:repaired,:repaired_last_iteration,:dense_repaired)
        calls=1;stops=2
        name==:repaired_last_iteration && (limit=1)
        if name==:dense_repaired
            B=T[2 0.125;0.25 3];rhs=T[1.875,-2.75];expected_point=T[1,-1]
        end
    elseif name==:unchanged
        mode=:zero;want=:unchanged;calls=1;stops=1;expected_point=copy(x)
    elseif name==:not_improved
        mode=:negative;want=:not_improved;calls=1;stops=1;expected_point=copy(x)
    elseif name==:zero_limit
        limit=0;want=:limit;expected_point=copy(x)
    elseif name==:improved_limit
        mode=:half;limit=1;want=:limit;calls=1;stops=2;expected_point=T[0.5,0]
    elseif name in (:initial_nonfinite,:initial_nan)
        x=T[name==:initial_nan ? NaN : Inf,0];want=:nonfinite_initial_quality;invalid=true;expected_point=copy(x)
    elseif name==:nonfinite_correction
        mode=:infinite;want=:nonfinite_correction;invalid=true;calls=1;stops=1;expected_point=copy(x)
    elseif name==:nonfinite_trial
        e=T===Float32 ? 127 : 1023
        B=reshape(T[ldexp(one(T),-(e-7))],1,1);x=T[ldexp(one(T),e)];rhs=T[256]
        want=:nonfinite_trial;invalid=true;calls=1;stops=1;expected_point=copy(x)
    elseif name==:nonfinite_trial_quality
        e=T===Float32 ? 127 : 1023
        B=reshape(T[ldexp(one(T),e-7)],1,1);x=zeros(T,1);rhs=T[1];mode=:huge
        want=:nonfinite_trial_quality;invalid=true;calls=1;stops=1;expected_point=copy(x)
    elseif name==:stop_before
        true_at=1;want=:stopped;stops=1;expected_point=copy(x)
    elseif name==:stop_adoption
        true_at=2;want=:stopped;stops=2;calls=1;expected_point=copy(x)
    elseif name==:throw_correction
        mode=:throw;failure=SingularException(19);want=nothing;calls=1;stops=1
    elseif name==:throw_stop
        throw_at=1;failure=SingularException(23);want=nothing;stops=1
    elseif name in (:throw_observer_attempt,:throw_observer_correction)
        observer_reason=name==:throw_observer_attempt ? :correction_attempt : :correction
        failure=SingularException(29);want=nothing
        calls=name==:throw_observer_attempt ? 0 : 1;stops=name==:throw_observer_attempt ? 1 : 2
    elseif name==:discarded_nonfinite_cleanup
        e=T===Float32 ? 127 : 1023;large=ldexp(one(T),e);small=ldexp(one(T),-e)
        B=T[-large 1 1;0 small 0;0 0 small];x=T[1,large,large];rhs=T[0,1,1]
        # The identity delegate is explicitly a wrong factor for this B. Its
        # output is discarded to zero: only real quality/cleanup arithmetic is
        # being tested, not factorization of this extreme-range matrix.
        identity_delegate=true;mode=:zero;refine=true;want=:not_improved;invalid=true
        calls=1;stops=T===Float64 ? 2 : 1;expected_point=copy(x)
    elseif name==:nonfinite_wide_quality
        T===Float64 || error("wide entry case is Float64 only")
        refine=true;poison=1;want=:nonfinite_quality;invalid=true;stops=1;expected_point=copy(x)
    elseif name==:stop_before_wide
        T===Float64 || error("wide entry case is Float64 only")
        refine=true;true_at=1;want=:stopped;stops=1;expected_point=copy(x)
    else
        error("unknown case")
    end
    (;name,B,x,rhs,mode,limit,refine,want,invalid,calls,stops,true_at,throw_at,
       poison,observer_reason,failure,identity_delegate,expected_point)
end
function owners(ws)
    b=J._pivot_quality_buffers(ws)
    map(objectid,(b.rhs,b.unit,b.correction,b.trial,b.singletons,
        b.row.residual,b.row.work_residual,b.row.work_scale,b.row.terms,b.row.compensation,b.row.error_sum,
        b.column.residual,b.column.work_residual,b.column.work_scale,b.column.terms,b.column.compensation,b.column.error_sum,
        ws.problem.A.nzval,ws.basis.basic_indices,ws.basis.states,ws.scratch.basis_matrix))
end
function fixture(sc,transposed)
    T=eltype(sc.x);B=transposed ? copy(transpose(sc.B)) : copy(sc.B);n=length(sc.x)
    A=sparse(B);problem=J.LinearProblem(A,zeros(T,n);column_lower=fill(nothing,n),name="refinement-outcome-control")
    options=J.SolverOptions(T;verbose=false,time_limit=Inf)
    policy=J.NumericalPolicy(T;solve_refinement=sc.refine,max_refinements=sc.limit,adaptive_refactor=true,refactor_timing=false)
    observer=ObserverProbe(0,sc.observer_reason,sc.failure)
    diag=J.SimplexDiagnostics(;observer)
    progress=J.SimplexProgressContext(problem;numerical_policy=policy,diagnostics=diag)
    delegate=sc.identity_delegate ? Matrix{T}(I,n,n) : Matrix(B)
    native=lu(delegate)
    f=CorrectionProbe{T,typeof(native)}(native,J.PackedEta{T}[],sc.mode,0,0,sc.failure)
    states=vcat(fill(J.BASIC,n),fill(J.FREE_NONBASIC,n))
    ws=J.SimplexWorkspace(problem,options,progress,zeros(T,2n),
        vcat(problem.column_lower,problem.row_lower),vcat(problem.column_upper,problem.row_upper),
        J.Basis(collect(1:n),states),zeros(T,2n),zeros(T,2n),ones(T,2n),falses(2n),f,
        J.SimplexScratch(T,n,2n),0,0,false,0,false,false,options.refactorization_interval,0,typemax(Int),0,0)
    J._basis_matrix!(ws);J._pivot_quality_buffers(ws);ws.scratch.refactorization.healthy_cycles=3
    stop=StopProbe(ws,0,sc.true_at,sc.throw_at,sc.poison,sc.failure)
    (;ws,policy,stop,factor=f,point=copy(sc.x),rhs=copy(sc.rhs),observer,owner_ids=owners(ws),B=copy(B))
end
function exercise(api,sc,transposed)
    f=fixture(sc,transposed);value=nothing;failure=nothing
    try
        value=api(f.point,f.ws,f.rhs,f.policy,f.stop;transposed)
    catch e
        failure=e
    end
    (;f,value,failure)
end
quality_fields(q)=(q.absolute_error,q.relative_error,q.finite,q.reliable)
function same_execution(a,b)
    @test isequal(a.f.point,b.f.point)
    @test isequal(a.f.rhs,b.f.rhs)
    @test a.f.stop.calls==b.f.stop.calls
    @test (a.f.factor.forwards,a.f.factor.backwards)==(b.f.factor.forwards,b.f.factor.backwards)
    @test J.recent_events(a.f.ws.progress.diagnostics)==J.recent_events(b.f.ws.progress.diagnostics)
    @test a.f.observer.calls==b.f.observer.calls
    @test a.f.owner_ids==owners(a.f.ws) && b.f.owner_ids==owners(b.f.ws)
    sa,sb=a.f.ws.scratch.refactorization,b.f.ws.scratch.refactorization
    @test sa.healthy_cycles==sb.healthy_cycles && sa.residual_bad==sb.residual_bad
    if isnothing(sa.latest_quality) || isnothing(sb.latest_quality)
        @test isnothing(sa.latest_quality) && isnothing(sb.latest_quality)
    else
        @test isequal(quality_fields(sa.latest_quality),quality_fields(sb.latest_quality))
    end
end
function runtests()
    @testset "Refinement outcome matches legacy quality" begin
        for T in (Float32,Float64),transposed in (false,true)
            names=T===Float64 ? (SIMPLE_CASES...,:nonfinite_wide_quality,:stop_before_wide) : SIMPLE_CASES
            for name in names
                sc=scenario(name,T)
                old=exercise(J.refine_basis_solve!,sc,transposed)
                detailed=exercise(J._refine_basis_solve_outcome!,sc,transposed)
                same_execution(old,detailed)
                @test old.f.stop.calls==sc.stops
                @test old.f.factor.forwards+old.f.factor.backwards==sc.calls
                @test isequal(old.f.rhs,sc.rhs) && old.f.ws.problem.A==sparse(old.f.B)
                if isnothing(sc.want)
                    if sc.observer_reason==:never
                        @test old.failure===sc.failure && detailed.failure===sc.failure
                    else
                        @test old.failure isa J.DiagnosticObserverFailure && detailed.failure isa J.DiagnosticObserverFailure
                        @test old.failure.cause===sc.failure && detailed.failure.cause===sc.failure
                    end
                    @test isnothing(old.value) && isnothing(detailed.value)
                else
                    @test isnothing(old.failure) && isnothing(detailed.failure)
                    @test old.value isa J.SolveQuality{T}
                    @test detailed.value isa J._BasisRefinementOutcome{T}
                    @test isequal(quality_fields(old.value),quality_fields(detailed.value.quality))
                    @test detailed.value.cause==getfield(J,Symbol("_refine_",sc.want))
                    @test detailed.value.invalid_seen==sc.invalid
                    if sc.name==:dense_repaired
                        @test isapprox(old.f.point,sc.expected_point;rtol=T(256)*eps(T),atol=zero(T))
                    else
                        @test isequal(old.f.point,sc.expected_point)
                    end
                    @test isequal(quality_fields(old.f.ws.scratch.refactorization.latest_quality),quality_fields(old.value))
                    if sc.want in (:nonfinite_correction,:nonfinite_trial,:nonfinite_trial_quality,:not_improved)
                        @test detailed.value.quality.finite
                    end
                end
            end
        end
    end
    @testset "Refinement guards remain checked before numeric work" begin
        sc=scenario(:repaired,Float64)
        for api in (J.refine_basis_solve!,J._refine_basis_solve_outcome!)
            f=fixture(sc,true)
            @test_throws ArgumentError api(f.point,f.ws,f.point,f.policy,f.stop;transposed=true)
            @test_throws ArgumentError api(J._pivot_quality_buffers(f.ws).row.residual,f.ws,f.rhs,f.policy,f.stop;transposed=true)
            @test_throws DimensionMismatch api(zeros(1),f.ws,f.rhs,f.policy,f.stop;transposed=true)
            @test f.factor.forwards+f.factor.backwards==0 && f.stop.calls==0
            @test f.point==sc.x && f.rhs==sc.rhs
        end
    end
    @testset "Existing multiprecision and exact API stays unchanged" begin
        for T in (BigFloat,Rational{BigInt}),transposed in (false,true)
            sc=scenario(:reliable,T)
            ambient=(precision(BigFloat),rounding(BigFloat))
            old=exercise(J.refine_basis_solve!,sc,transposed)
            detailed=exercise(J._refine_basis_solve_outcome!,sc,transposed)
            @test isnothing(old.failure) && isnothing(detailed.failure)
            @test old.value.reliable && detailed.value.quality.reliable
            @test detailed.value.cause==J._refine_reliable && !detailed.value.invalid_seen
            same_execution(old,detailed)
            @test (precision(BigFloat),rounding(BigFloat))==ambient
            if T===BigFloat
                @test precision(old.value.absolute_error)==precision(detailed.value.quality.absolute_error)
                @test precision(old.value.relative_error)==precision(detailed.value.quality.relative_error)
            end
        end
    end
end
end # module
Base.invokelatest(RefinementOutcomeTests.runtests)
