using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Phase export retains certified nonbasic values" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        options=SolverOptions(T;algorithm=:primal,basis_update=manager,verbose=false)
        delta=options.primal_tolerance/T(2)
        p=LinearProblem(sparse(reshape(T[1,1],1,2)),zeros(T,2);row_lower=T[1],row_upper=T[1])
        aux=LinearProblem(sparse(reshape(T[1,1,1],1,3)),T[0,0,1];row_lower=T[1],row_upper=T[1])
        original=JSimplex.initialize_workspace(p,options)
        phase=JSimplex.initialize_workspace(aux,options)
        phase.basis=JSimplex.Basis([2],[JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
        phase.iterations=1
        phase.primal.=T[-delta,1+delta,0,1]
        JSimplex.recompute!(phase;refactorize=true)
        mapping=JSimplex.PhaseOneMap([1,2,4],[1,2,0,3],[3])
        @test JSimplex._legacy_primal_point_certified(phase)
        @test JSimplex.remove_artificials!(phase,mapping,original,phase.progress.numerical_policy,()->false)
        @test original.primal[1]==-delta
        @test JSimplex._original_primal_feasible(original,original.primal[1:2])
    end
end

@testset "Local phase rows preserve tiny right-hand sides and reject cycles" begin
    for T in (Float32,Float64)
        tiny=T === Float32 ? T(1e-20) : T(1e-66)
        noise=T === Float32 ? T(1e-10) : T(1e-30)
        cutoff=T === Float32 ? T(1e-8) : T(1e-21)
        B=sparse(T[1 1;0 1]);rhs=T[0,tiny]
        policy=JSimplex.NumericalPolicy(T)
        x=T[noise,tiny]
        @test JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
        @test x==T[-tiny,tiny]
        for (initial,limit) in ((T[0,tiny],cutoff),(T[noise,tiny],zero(T)))
            x=copy(initial)
            @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,limit,()->false;coupled=false)
            @test isequal(x,initial)
        end
        for throwing in (false,true)
            x=T[noise,tiny];before=copy(x);calls=Ref(0);error=ErrorException("cancel local rows")
            stop=()->begin
                calls[]+=1
                if calls[]==8
                    throwing && throw(error)
                    return true
                end
                false
            end
            result=try JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) catch e; e end
            @test result === (throwing ? error : false)
            @test isequal(x,before)
        end
        x=T[noise,tiny];before=copy(x)
        old=get_zero_subnormals()
        try
            set_zero_subnormals(true)
            @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
            @test isequal(x,before)
        finally
            set_zero_subnormals(old)
        end
    end
end

@testset "Phase export clears coupled homogeneous roundoff without erasing tiny data" begin
    for T in (Float32,Float64)
        noise=T===Float32 ? T(1e-10) : T(1e-30)
        tiny=T===Float32 ? T(1e-20) : T(1e-66)
        cutoff=T(100)*noise
        # The first five equations form the coupled homogeneous block seen at
        # runtime's export. The sixth propagates cleanup to a satisfied row.
        block=T[-1 0 1 0 0 0; 0 -1 0 -1 1 0;
            -0.50137362625 -0.50137362625 0 -1.825 0 0;
            -1 -1 0 -1 0 0; 0 0 -0.1 0 1.9 0; 0 0 1 0 0 -1]
        B=blockdiag(sparse(block),sparse(T[1 1;0 1]))
        rhs=vcat(zeros(T,7),tiny)
        initial=vcat(noise*T[-1.3,1,-1.3,-0.4,-0.07,-1.3],T[noise,tiny])
        policy=JSimplex.NumericalPolicy(T)
        x=copy(initial)
        @test JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,()->false)
        @test all(iszero,x[1:6])
        @test x[7:8]==T[-tiny,tiny]
        @test JSimplex.solve_quality!(JSimplex.SolveQualityScratch(T,8),B,x,rhs,policy).reliable
        # A neighboring large coordinate must never join the cleanup. An
        # insignificant connection passes; an amplified connection must fail
        # the full-system certificate and leave the entire input unchanged.
        for coefficient in (one(T),inv(noise))
            boundary=blockdiag(B,sparse(reshape(T[1],1,1)))
            boundary[9,1]=coefficient
            values=vcat(initial,T(4))
            boundary_rhs=vcat(rhs,T(4)+coefficient*initial[1])
            saved=copy(values)
            accepted=JSimplex._native_phase_local_rows!(values,boundary,boundary_rhs,
                policy,cutoff,()->false)
            @test accepted == (coefficient==one(T))
            @test values[9]==T(4)
            if accepted
                @test all(iszero,values[1:6])
            else
                @test isequal(values,saved)
            end
        end
        # The final stop checks are inside the component-clearing loop and
        # then its certificate. Interrupt mid-clear, after tentative zeroing.
        calls=Ref(0)
        @test JSimplex._native_phase_local_rows!(copy(initial),B,rhs,policy,cutoff,
            ()->begin calls[]+=1;false end)
        cancel_at=calls[]-4
        for throwing in (false,true)
            x=copy(initial);calls[]=0;error=ErrorException("cancel component cleanup")
            stop=()->begin
                calls[]+=1
                if calls[]==cancel_at
                    throwing && throw(error)
                    return true
                end
                false
            end
            result=try JSimplex._native_phase_local_rows!(x,B,rhs,policy,cutoff,stop) catch e; e end
            @test result === (throwing ? error : false)
            @test calls[]==cancel_at
            @test isequal(x,initial)
        end
        # A nonzero RHS makes clearing invalid, even when coupled solving is disabled.
        unsafe_rhs=copy(rhs);unsafe_rhs[1]=tiny
        x=copy(initial)
        @test !JSimplex._native_phase_local_rows!(x,B,unsafe_rhs,policy,cutoff,()->false;coupled=false)
        @test isequal(x,initial)
        x=copy(initial)
        @test !JSimplex._native_phase_local_rows!(x,B,rhs,policy,zero(T),()->false)
        @test isequal(x,initial)
    end
end

# A small independent zero-artificial exchange reconstructs roundoff in a
# homogeneous row. Feasible bounds alone do not certify the basis equations.
function artificial_exchange_roundoff_fixture(T,manager;max_refinements=3,diagnostics=nothing)
    A=sparse(T[8 -2 0 1 -3 2; 2 6 1 2 -2 -2; 1 -2 3 0 -1 3;
               3 -1 0 5 -2 -2; 0 0 -1 0 6 -3; 0 0 -1 -2 -1 8])
    rhs=Vector(A[:,1]+A[:,2])
    policy=JSimplex.NumericalPolicy(T;max_refinements)
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,verbose=false)
    p=LinearProblem(A,zeros(T,6);row_lower=rhs,row_upper=rhs)
    auxiliary=LinearProblem(hcat(A,A[:,6:6]),vcat(zeros(T,6),one(T));row_lower=rhs,row_upper=rhs)
    original=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics))
    phase=JSimplex.initialize_workspace(auxiliary,options;
        progress=JSimplex.SimplexProgressContext(auxiliary;numerical_policy=policy,diagnostics))
    phase.basis=JSimplex.Basis([1,2,3,4,5,7],vcat(fill(JSimplex.BASIC,5),
        JSimplex.AT_LOWER,JSimplex.BASIC,fill(JSimplex.AT_LOWER,6)))
    JSimplex.recompute!(phase;refactorize=true)
    # The exact known feasible point has a zero basic artificial. It models the
    # maintained Phase-I point, independently of the refactorized reconstruction.
    phase.primal.=vcat(T[1,1,0,0,0,0,0],rhs)
    mapping=JSimplex.PhaseOneMap(vcat(1:6,8:13),vcat(1:6,0,7:12),[7])
    return phase,mapping,original,policy
end

@testset "Artificial exchanges certify native reconstruction before export" begin
    for T in (Float32,Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        phase,mapping,original,policy=artificial_exchange_roundoff_fixture(T,manager)
        @test JSimplex._legacy_primal_point_certified(phase)
        accepted=JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test accepted
        if accepted
            @test original.iterations==1
            @test original.basis.basic_indices==collect(1:6)
            @test JSimplex._recomputed_basis_reliable(original)
            @test JSimplex._legacy_primal_point_certified(original)
            @test JSimplex._original_primal_feasible(original,original.primal[1:6])
        end
    end
end

@testset "Artificial exchange recovery preserves cancellation and policy limits" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        for mode in (:budget,:cancel,:exception,:bounds)
            correcting=Ref(false)
            diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
                event==:correction_attempt && (correcting[]=true)
            end)
            phase,mapping,original,policy=artificial_exchange_roundoff_fixture(Float64,manager;
                max_refinements=mode==:budget ? 0 : 3,diagnostics)
            before=deepcopy((original.basis,original.primal,original.costs,original.lower,
                original.upper,original.reduced_costs))
            mode==:bounds && (phase.upper[1]=Bound(0.5))
            failure=ErrorException("cancel artificial exchange correction")
            stop=()->begin
                correcting[] && mode==:exception && throw(failure)
                correcting[] && mode==:cancel
            end
            result=try JSimplex.remove_artificials!(phase,mapping,original,policy,stop) catch e; e end
            @test result === (mode==:exception ? failure : false)
            @test original.basis.basic_indices==before[1].basic_indices
            @test original.basis.states==before[1].states
            @test isequal((original.primal,original.costs,original.lower,original.upper,
                original.reduced_costs),before[2:end])
            @test original.iterations==1
            @test original.refactorizations>=phase.refactorizations
            mode in (:cancel,:exception) && (@test correcting[])
            mode==:budget && (@test !correcting[])
        end
    end
end

@testset "Reliable artificial exchanges need no reconstruction recovery" begin
    for manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        diagnostics=JSimplex.SimplexDiagnostics()
        phase,mapping,original,policy=artificial_exchange_roundoff_fixture(Float32,manager;
            max_refinements=0,diagnostics)
        @test JSimplex.remove_artificials!(phase,mapping,original,policy,()->false)
        @test original.iterations==1
        @test JSimplex._recomputed_basis_reliable(original)
        @test JSimplex.event_count(diagnostics,:correction_attempt)==0
    end
end
