using Test,JSimplex,SparseArrays

function bound_roundoff_workspace(T,sign,manager=:pfi)
    tolerance=T(1e-7)
    lower=T(-1.2e-6)
    inside=lower-tolerance
    lower-inside>tolerance && (inside=nextfloat(inside))
    outside=prevfloat(inside)
    @assert lower-inside<=tolerance<lower-outside
    value=T(sign)*outside
    bound=T(sign)*lower
    p=LinearProblem(spdiagm(0=>ones(T,2)),zeros(T,2);
        column_lower=fill(sign>0 ? bound : T(-Inf),2),
        column_upper=fill(sign>0 ? T(Inf) : bound,2),
        row_lower=fill(sign>0 ? T(-Inf) : value,2),
        row_upper=fill(sign>0 ? value : T(Inf),2))
    options=SolverOptions(T;algorithm=:primal,basis_update=manager,
        basis_refactorization=:native,primal_tolerance=tolerance,verbose=false)
    diagnostics=JSimplex.SimplexDiagnostics()
    ws=JSimplex.initialize_workspace(p,options;
        progress=JSimplex.SimplexProgressContext(p;diagnostics))
    row_state=sign>0 ? JSimplex.AT_UPPER : JSimplex.AT_LOWER
    ws.basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,row_state,row_state])
    JSimplex.recompute!(ws;refactorize=true)
    ws.primal .= value
    return ws,diagnostics
end

@testset "One-ULP basic bound errors admit fully certified native recovery" begin
    for T in (Float32,Float64), sign in (-1,1), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub)
        ws,diagnostics=bound_roundoff_workspace(T,sign,manager)
        original=copy(ws.primal)
        candidate=copy(ws.primal[ws.basis.basic_indices])
        @test !JSimplex._legacy_primal_point_certified(ws)
        terminal=JSimplex._finish_legacy_primal_point!(ws,candidate,()->false)
        @test isnothing(terminal)
        @test JSimplex._legacy_primal_point_certified(ws)
        @test ws.primal[3:4]==original[3:4]
        @test all(abs(ws.primal[j]-original[j])==eps(abs(original[j])) for j in (1,2))
        @test ws.scratch.row_solution==ws.primal[ws.basis.basic_indices]
        @test JSimplex.event_count(diagnostics,:primal_bound_roundoff_corrected)==1
    end
end

@testset "Inward rounding remains bounded and correction trials roll back" begin
    for T in (Float32,Float64), mode in (:two_ulps,:equations,:nonbasic,:stop,:throw)
        ws,diagnostics=bound_roundoff_workspace(T,1)
        if mode==:two_ulps
            ws.primal[2]=prevfloat(ws.primal[2])
            ws.primal[4]=ws.primal[2]
        elseif mode==:equations
            # Power-of-two products are exact before the trial. One inward ULP
            # then amplifies beyond the row tolerance despite fixing both bounds.
            scale=ldexp(one(T),80)
            ws.problem.A.nzval .*= scale
            for j in 1:2
                activity=scale*ws.primal[j]
                ws.upper[j+2]=Bound(activity)
                ws.problem.row_upper[j]=Bound(activity)
            end
            JSimplex.recompute!(ws;refactorize=true)
        elseif mode==:nonbasic
            # A nonbasic violation cannot be repaired by this basic-only trial.
            ws.upper[3]=Bound(ws.primal[3]-2ws.options.primal_tolerance)
        end
        original=copy(ws.primal)
        cache=copy(ws.scratch.row_solution)
        metadata=(copy(ws.lower),copy(ws.upper),copy(ws.costs),copy(ws.basis.basic_indices),copy(ws.basis.states))
        stop=()->begin
            if mode in (:stop,:throw) && JSimplex._legacy_primal_point_certified(ws)
                mode==:throw && error("cancel rounded correction")
                return true
            end
            false
        end
        if mode==:throw
            @test_throws ErrorException("cancel rounded correction") JSimplex._try_native_primal_point_correction!(ws,stop)
        else
            @test !JSimplex._try_native_primal_point_correction!(ws,stop)
        end
        @test ws.primal==original
        @test ws.scratch.row_solution==cache
        @test metadata==(ws.lower,ws.upper,ws.costs,ws.basis.basic_indices,ws.basis.states)
        @test JSimplex.event_count(diagnostics,:correction)==0
        @test JSimplex.event_count(diagnostics,:primal_bound_roundoff_corrected)==0
    end
end
