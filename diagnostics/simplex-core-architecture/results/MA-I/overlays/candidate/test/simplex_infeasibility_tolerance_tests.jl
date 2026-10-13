using JSimplex, Test, SparseArrays

@testset "Infeasibility certificates include column and row tolerances" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), sign in (-1, 1)
        tolerance = T(1//1024)
        for gap in (T(1//4), T(2)), scaling in (:off, :on)
            T <: Rational && scaling == :on && continue
            # For gap=1/4, x=sign*(1+1/4096) satisfies the row exactly
            # and exceeds its column bound by less than tolerance.
            p = LinearProblem(sparse(reshape(T[1024],1,1)), T[0];
                row_lower=sign > 0 ? T[1024+gap] : [nothing],
                row_upper=sign > 0 ? [nothing] : T[-1024-gap],
                column_lower=sign > 0 ? T[0] : T[-1],
                column_upper=sign > 0 ? T[1] : T[0])
            working, factors = scaling == :off ? (p,JSimplex.identity_scaling(p)) : JSimplex.scale_problem(p)
            options = SolverOptions(T;primal_tolerance=tolerance,verbose=false,scaling,presolve=false)
            progress = JSimplex.SimplexProgressContext(p;scaling=factors)
            ws = JSimplex.initialize_workspace(working,options;progress)
            @test JSimplex._primal_infeasibility_certified(ws,T[sign]) == (gap == T(2))
            if gap == T(1//4)
                @test JSimplex._original_primal_feasible(p,T[sign*T(1+1//4096)],tolerance)
            end
        end
        # Only the ROW allowance makes the envelope feasible here.
        p = LinearProblem(sparse(reshape(T[1,1],2,1)),T[0];
            row_lower=[T(3//2048),nothing],row_upper=[nothing,T(0)],column_lower=[nothing])
        ws = JSimplex.initialize_workspace(p,SolverOptions(T;primal_tolerance=tolerance,verbose=false))
        @test !JSimplex._primal_infeasibility_certified(ws,T[1,-1])
        @test JSimplex._original_primal_feasible(p,T[3//4096],tolerance)
    end
end

@testset "Public simplex cannot reject a tolerance-feasible original point" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), algorithm in (:dual,:primal), presolve in (false,true)
        p = LinearProblem(sparse(reshape(T[1024],1,1)),T[0];
            row_lower=T[1024+1//4],column_upper=T[1])
        options=SolverOptions(T;algorithm,presolve,scaling=:off,verbose=false,
            primal_tolerance=T(1//1024),time_limit=30)
        r=solve(p;options)
        # Rejecting an inconclusive certificate need not produce an optimum.
        @test r.status in (OPTIMAL,NUMERICAL_ERROR)
        if r.status == OPTIMAL
            @test JSimplex._original_primal_feasible(p,r.primal,T(1//1024))
        end
    end
end

@testset "Scaled columns and summed row allowances use original units" begin
    for T in (Float32,Float64,BigFloat), gap in (T(1//4096),T(1//256))
        tolerance=T(1//1024)
        # Row scaling is 1024 and the first column scaling is 1/1024.
        p=LinearProblem(sparse(reshape(T[1,1024],1,2)),T[0,0];
            row_lower=T[1+gap],column_upper=T[1,0])
        scaled,factors=JSimplex.scale_problem(p)
        ws=JSimplex.initialize_workspace(scaled,
            SolverOptions(T;primal_tolerance=tolerance,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;scaling=factors))
        @test JSimplex._primal_infeasibility_certified(ws,T[1]) == false
        # The fixed second column also has an original tolerance; omitting it
        # would incorrectly prove the larger gap infeasible after scaling.
        @test JSimplex._original_primal_feasible(p,T[1,gap/T(1024)],tolerance)
        # Without that second finite-bound contribution, row and first-column
        # allowances total 2*tolerance, so the larger gap is conclusive.
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
            row_lower=T[1+gap],column_upper=T[1])
        scaled=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
            row_lower=T[(1+gap)/1024],column_upper=T[1//1024])
        ws=JSimplex.initialize_workspace(scaled,
            SolverOptions(T;primal_tolerance=tolerance,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;
                scaling=JSimplex.Scaling(T[1024],T[1//1024])))
        @test JSimplex._primal_infeasibility_certified(ws,T[1]) == (gap==T(1//256))
    end
end

@testset "Strict contradictions and zero tolerance retain infeasibility" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), algorithm in (:dual,:primal),
        tolerance in (zero(T),T(1//1024)), general_phase in (false,true)
        T <: AbstractFloat && iszero(tolerance) && continue
        gap=iszero(tolerance) ? T(1//4) : T(2)
        p=LinearProblem(sparse(reshape(T[1024],1,1)),T[0];
            row_lower=T[1024+gap],column_upper=T[1])
        options=SolverOptions(T;algorithm,presolve=false,scaling=:off,
            primal_tolerance=tolerance,verbose=false,time_limit=30)
        policy=JSimplex.NumericalPolicy(T;phase_one=general_phase)
        r=JSimplex._solve_diagnosed(p,nothing;options,numerical_policy=policy)
        @test r.status==INFEASIBLE
    end
end

@testset "General phase I also rejects the tolerance-inconsistent proof" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        p=LinearProblem(sparse(reshape(T[1024],1,1)),T[0];
            row_lower=T[1024+1//4],column_upper=T[1])
        options=SolverOptions(T;algorithm=:primal,presolve=false,scaling=:off,
            primal_tolerance=T(1//1024),verbose=false,time_limit=30)
        policy=JSimplex.NumericalPolicy(T;phase_one=true)
        r=JSimplex._solve_diagnosed(p,nothing;options,numerical_policy=policy)
        @test r.status in (OPTIMAL,NUMERICAL_ERROR)
    end
end

@testset "Certificate is conservative at the tolerance boundary" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        tolerance=T(1//1024)
        for gap in (T(2)*tolerance,T(3)*tolerance), multiplier in (T(1//1024),T(1024))
            p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
                row_lower=T[1+gap],column_upper=T[1])
            ws=JSimplex.initialize_workspace(p,SolverOptions(T;primal_tolerance=tolerance,verbose=false))
            @test JSimplex._primal_infeasibility_certified(ws,T[multiplier])==(gap==T(3)*tolerance)
        end
        # An unbounded column precludes this row-combination proof.
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];row_lower=T[2])
        ws=JSimplex.initialize_workspace(p,SolverOptions(T;primal_tolerance=tolerance,verbose=false))
        @test !JSimplex._primal_infeasibility_certified(ws,T[1])
    end
end

@testset "Floating proof retains mixed-precision and subnormal allowances" begin
    ws,witness,p,tolerance=setprecision(BigFloat,256) do
        tolerance=BigFloat(1//1024)+BigFloat(2)^(-70)
        p=LinearProblem(sparse(reshape(BigFloat[1],1,1)),BigFloat[0];
            row_lower=BigFloat[1+2tolerance],column_upper=BigFloat[1])
        ws=JSimplex.initialize_workspace(p,SolverOptions(BigFloat;primal_tolerance=tolerance,verbose=false))
        ws,BigFloat[1+tolerance],p,tolerance
    end
    @test JSimplex._original_primal_feasible(p,witness,tolerance)
    for rounding in (RoundNearest,RoundDown,RoundUp)
        setprecision(BigFloat,64) do
            setrounding(BigFloat,rounding) do
                @test !JSimplex._primal_infeasibility_certified(ws,BigFloat[1])
                @test precision(BigFloat)==64
            end
        end
    end
    for T in (Float32,Float64)
        tiny=nextfloat(zero(T))
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
            row_lower=T[2tiny],column_upper=T[0])
        @test JSimplex._original_primal_feasible(p,T[tiny],tiny)
        scaled=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
            row_lower=T[tiny],column_upper=T[0])
        ws=JSimplex.initialize_workspace(scaled,SolverOptions(T;primal_tolerance=tiny,verbose=false);
            progress=JSimplex.SimplexProgressContext(p;scaling=JSimplex.Scaling(T[2],T[1//2])))
        @test !JSimplex._primal_infeasibility_certified(ws,T[1])
    end
end

@testset "Bounded rational overflow makes a proof inconclusive" begin
    T=Rational{Int}
    large=typemax(Int)
    p=LinearProblem(sparse(reshape(T[1],1,1)),T[0];
        row_lower=T[large],column_upper=T[large-1])
    ws=JSimplex.initialize_workspace(p,SolverOptions(T;primal_tolerance=1//1024,verbose=false))
    @test !JSimplex._primal_infeasibility_certified(ws,T[1])
end
