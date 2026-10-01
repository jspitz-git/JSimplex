using JSimplex, Test, SparseArrays

@testset "Presolve does not reject a point within the configured primal tolerance" begin
    for T in (Float32, Float64, BigFloat, Rational{BigInt}), algorithm in (:primal, :dual)
        tolerance = T(1//1024)
        gap = T(1//4096)
        problem = LinearProblem(sparse(reshape(T[1],1,1)), T[2];
            row_lower=T[1+gap], column_lower=T[1], column_upper=T[1])
        # The stored model is exactly inconsistent, but x=1 satisfies the
        # configured absolute tolerance in the original row and column units.
        @test JSimplex._original_primal_feasible(problem,T[1],tolerance)
        strict = JSimplex.presolve_problem(problem)
        @test strict isa JSimplex.PresolveFailure && strict.status == INFEASIBLE
        for presolve in (false,true)
            options = SolverOptions(T;algorithm,presolve,primal_tolerance=tolerance,
                scaling=:off,verbose=false,time_limit=30)
            result = solve(problem;options)
            @test result.status == OPTIMAL
            if result.status == OPTIMAL
                @test JSimplex._original_primal_feasible(problem,result.primal,tolerance)
                @test result.objective_value == T(2)
            end
        end
    end
end

@testset "Presolve infeasibility proof uses original row and column units" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt})
        tolerance=T(1//1024)
        # A common x=tolerance satisfies both rows at their respective tolerance.
        p=LinearProblem(sparse(reshape(T[1,1],2,1)),T[7];
            row_lower=[T(2)*tolerance,nothing],row_upper=[nothing,T(0)],
            column_lower=[nothing])
        @test JSimplex._original_primal_feasible(p,T[tolerance],tolerance)
        result=JSimplex._presolve_for_solve(p,tolerance)
        @test result isa JSimplex.PresolveResult
        @test result.problem === p && isempty(result.postsolve_stack)
        # A fixed-column deviation is magnified by the row coefficient. Applying
        # tolerance only to the reduced row would still wrongly reject this LP.
        p=LinearProblem(sparse(reshape(T[1048576],1,1)),T[3];
            row_lower=T[1],column_lower=T[0],column_upper=T[0])
        @test JSimplex._original_primal_feasible(p,T[1//1048576],tolerance)
        result=JSimplex._presolve_for_solve(p,tolerance)
        @test result isa JSimplex.PresolveResult
        @test result.problem === p && isempty(result.postsolve_stack)
        @test p.objective==T[3] && p.row_lower[1].value==T(1)
        @test p.column_lower[1].value==p.column_upper[1].value==T(0)
        proof=JSimplex._presolve_tolerance_model(p,tolerance)
        @test JSimplex._original_primal_feasible(proof,T[0,1//1048576,0],zero(T))
        @test iszero(proof.objective[1]) && iszero(proof.objective_constant)
        @test eltype(proof.A)==T
    end
end

@testset "Conclusive presolve contradictions and zero tolerance remain strict" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}), gap in (T(1//4096),T(1//256))
        tolerance=T(1//1024)
        p=LinearProblem(spzeros(T,1,1),T[0];row_lower=T[gap])
        exact=JSimplex._presolve_for_solve(p,zero(T))
        @test exact isa JSimplex.PresolveFailure && exact.status==INFEASIBLE
        result=JSimplex._presolve_for_solve(p,tolerance)
        @test (result isa JSimplex.PresolveFailure)==(gap>tolerance)
        for algorithm in (:dual,:primal)
            r=solve(p;options=SolverOptions(T;algorithm,primal_tolerance=tolerance,verbose=false))
            @test r.status==(gap>tolerance ? INFEASIBLE : OPTIMAL)
        end
    end
    # The sum of both row tolerances is insufficient for this contradiction.
    p=LinearProblem(sparse(reshape([1.0,1.0],2,1)),[0.0];
        row_lower=[0.004,nothing],row_upper=[nothing,0.0],column_lower=[nothing])
    result=JSimplex._presolve_for_solve(p,0.001)
    @test result isa JSimplex.PresolveFailure && result.status==INFEASIBLE
end

@testset "Presolve proof retains small allowances beside large bounds" begin
    Q=Rational{BigInt}
    for T in (Float32,Float64,BigFloat)
        tolerance=eps(one(T))/T(4)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[1];
            row_lower=T[1],row_upper=T[1],column_lower=T[1],column_upper=T[1])
        proof=JSimplex._presolve_tolerance_model(p,tolerance)
        # This lifted point allows the tiny column deviation while its separate
        # row error preserves the exact row value, even below the original ulp.
        point=Q[1,Q(tolerance),-Q(tolerance)]
        @test Q.(proof.A)*point==Q[1]
        @test proof.row_lower==p.row_lower && proof.row_upper==p.row_upper
        @test proof.column_lower[1]==p.column_lower[1] && proof.column_upper[1]==p.column_upper[1]
        @test proof.column_upper[2].value==proof.column_upper[3].value==tolerance
        @test all(j->Q(proof.column_lower[j].value)<=point[j]<=Q(proof.column_upper[j].value),1:3)
    end
    for T in (Float32,Float64)
        p=LinearProblem(sparse(reshape(T[1],1,1)),T[1];
            row_lower=T[-floatmax(T)],row_upper=T[floatmax(T)],
            column_lower=T[-floatmax(T)],column_upper=T[floatmax(T)])
        proof=JSimplex._presolve_tolerance_model(p,floatmax(T))
        @test all(isfinite,proof.row_lower) && all(isfinite,proof.row_upper)
        @test all(isfinite,proof.column_lower) && all(isfinite,proof.column_upper)
        @test proof.column_upper[1].value==proof.column_upper[2].value==floatmax(T)
    end
    p=LinearProblem(sparse(reshape(Rational{Int}[1],1,1)),Rational{Int}[0];
        column_upper=Rational{Int}[typemax(Int)])
    proof=JSimplex._presolve_tolerance_model(p,1//1)
    @test proof.column_upper[1].value==typemax(Int)//1
    @test proof.column_upper[2].value==1//1
    # Outward addition at 1e16 would spuriously expand each bound by 2.
    # Separate errors preserve the small tolerance and its infeasibility proof.
    p=LinearProblem(sparse([1.0 1.0 0.0]),[0.0,0.0,-1.0];row_lower=[0.1],
        column_lower=[0.0,-1e16,0.0],column_upper=[1e16,-1e16,Inf])
    @test JSimplex._presolve_for_solve(p,1e-7) isa JSimplex.PresolveFailure
    @test solve(p;options=SolverOptions(verbose=false)).status==INFEASIBLE
end

@testset "Presolve proof respects stop requests and relaxation domains" begin
    p=LinearProblem(sparse(reshape([1.0],1,1)),[1.0];
        row_lower=[1.00001],column_lower=[1.0],column_upper=[1.0])
    for at in (1,2)
        checks=Ref(0)
        result=JSimplex._presolve_for_solve(p,0.001;
            stop_requested=()->(checks[]+=1;checks[]==at))
        @test checks[]==at
        @test result.problem === p && isempty(result.postsolve_stack)
    end
    @test solve(p;options=SolverOptions(time_limit=0,verbose=false)).status==TIME_LIMIT
    # The public solver must build the proof from the continuous LP, so binary
    # constructor normalization cannot erase the outward column relaxation.
    p=LinearProblem(sparse(reshape([1024.0],1,1)),[0.0];
        row_lower=[1024.25],variable_domains=[JSimplex.BINARY])
    tolerance=1/1024
    continuous=JSimplex.relax_integrality(p)
    proof=JSimplex._presolve_tolerance_model(continuous,tolerance)
    @test proof.column_upper[1].value==1.0
    @test proof.column_upper[2].value==tolerance
    @test JSimplex._original_primal_feasible(proof,[1.0,1/4096,0.0],0.0)
    @test JSimplex._original_primal_feasible(p,[1+1/4096],tolerance)
    @test JSimplex._presolve_for_solve(continuous,tolerance) isa JSimplex.PresolveResult
    entered=Ref(false)
    original_models=Bool[]
    diagnostics=JSimplex.SimplexDiagnostics(;observer=(event,ws)->begin
        if event==:phase_dual
            entered[]=true
            model=ws.problem
            push!(original_models,model.A==continuous.A &&
                model.objective==continuous.objective &&
                model.row_lower==continuous.row_lower && model.row_upper==continuous.row_upper &&
                model.column_lower==continuous.column_lower && model.column_upper==continuous.column_upper)
        end
    end)
    # This fixture also exposes the separate strict-bound simplex infeasibility
    # certificate issue; the diagnostic core probe records it explicitly. Here
    # verify the presolve contract: enter simplex with the unchanged original LP.
    JSimplex._solve_diagnosed(p,diagnostics;relax_integrality=true,
        options=SolverOptions(primal_tolerance=tolerance,verbose=false,scaling=:off))
    @test entered[] && !isempty(original_models)
    @test all(original_models)
    @test p.column_upper[1].value==1.0
end

@testset "Presolve proof preserves mixed-precision BigFloat enclosures" begin
    original_precision=precision(BigFloat)
    p,tolerance=setprecision(BigFloat,192) do
        value=BigFloat(1)+BigFloat(2)^(-100)
        delta=BigFloat(2)^(-105)
        model=LinearProblem(sparse(reshape(BigFloat[1],1,1)),BigFloat[0];
            row_lower=[value],row_upper=[value],column_lower=[value],column_upper=[value])
        model,delta
    end
    exact_tolerance=Rational{BigInt}(tolerance)
    for mode in (RoundNearest,RoundDown,RoundUp)
        setprecision(BigFloat,64) do
            setrounding(BigFloat,mode) do
                proof=JSimplex._presolve_tolerance_model(p,tolerance)
                @test Rational{BigInt}(proof.column_lower[2].value)<=-exact_tolerance
                @test Rational{BigInt}(proof.column_upper[2].value)==exact_tolerance
                @test proof.row_lower==p.row_lower && proof.row_upper==p.row_upper
                @test precision(proof.column_lower[2].value)==64
                @test precision(proof.column_upper[2].value)==192
                @test precision(BigFloat)==64
            end
        end
    end
    @test precision(BigFloat)==original_precision
    @test precision(p.row_lower[1].value)==192
end
