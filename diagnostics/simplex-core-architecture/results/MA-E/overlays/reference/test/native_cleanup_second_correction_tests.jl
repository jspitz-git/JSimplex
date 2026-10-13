using Test, JSimplex, SparseArrays, LinearAlgebra

function native_second_correction_fixture(T; manager=:pfi, budget=3, error=nothing)
    B = sparse(T[1 0; 0 2])
    rhs = T[1, 2]
    problem = LinearProblem(B, zeros(T, 2))
    diagnostics = JSimplex.SimplexDiagnostics()
    options = SolverOptions(T; verbose=false, basis_update=manager)
    progress = JSimplex.SimplexProgressContext(problem; diagnostics,
        numerical_policy=JSimplex.NumericalPolicy(T; max_refinements=budget))
    ws = JSimplex.initialize_workspace(problem, options; progress)
    # Model an inaccurate inverse action with a real, slightly perturbed LU.
    # For B*x=rhs the exact answer is [1,1]. One correction leaves O(error),
    # beyond the local reconstruction cutoff; two leave O(error^2).
    perturbation = isnothing(error) ? (T === Float32 ? T(1e-3) : T(1e-8)) : T(error)
    JSimplex.refactorize!(ws.factorization, (one(T)+perturbation)*B)
    return ws, B, rhs, zeros(T, 2), diagnostics
end

@testset "Native terminal cleanup permits one improving second correction" begin
    for T in (Float32, Float64), manager in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub,:huangfu_hall), transposed in (false,true)
        ws,B,rhs,x,d = native_second_correction_fixture(T; manager)
        @test JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->false;
            transposed,local_reconstruction=true)
        @test x ≈ ones(T,2)
        @test norm(B*x-rhs,Inf) <= T(256)*eps(T)*norm(rhs,Inf)
        @test JSimplex.event_count(d,:correction_attempt) == 2
    end
end

@testset "Second native correction respects scope, budget and rejection" begin
    for T in (Float32,Float64), mode in (:ordinary,:budget,:wrong_factor,:stagnant)
        ws,B,rhs,x,d = native_second_correction_fixture(T;
            budget=mode===:budget ? 1 : 3,
            error=mode===:wrong_factor ? 1 : mode===:stagnant ? -2 : nothing)
        before=copy(x)
        @test !JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->false;
            local_reconstruction=mode!==:ordinary)
        @test isequal(x,before)
        @test JSimplex.event_count(d,:correction_attempt) <= (mode===:wrong_factor ? 2 : 1)
    end
end

@testset "Second native correction does not publish on cancellation" begin
    for T in (Float32,Float64)
        ws,B,rhs,x,_ = native_second_correction_fixture(T)
        calls=Ref(0)
        @test JSimplex._native_cleanup_solve!(x,ws,B,rhs,()->(calls[]+=1;false);
            local_reconstruction=true)
        total=calls[]
        for throwing in (false,true), boundary in 1:total
            ws,B,rhs,x,_ = native_second_correction_fixture(T)
            before=copy(x);calls[]=0;failure=ErrorException("cancel second correction")
            stop=()->begin
                calls[]+=1
                if calls[]==boundary
                    throwing && throw(failure)
                    return true
                end
                false
            end
            result=try
                JSimplex._native_cleanup_solve!(x,ws,B,rhs,stop;local_reconstruction=true)
            catch exception
                exception
            end
            @test result === (throwing ? failure : false)
            @test isequal(x,before)
        end
    end
end
