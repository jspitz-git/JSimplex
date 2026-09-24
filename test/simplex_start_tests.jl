using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Guarded crash interfaces" begin
    @test isdefined(JSimplex, :crash_basis)
    @test isdefined(JSimplex, :initialize_from_basis)
end

if isdefined(JSimplex, :crash_basis) && isdefined(JSimplex, :initialize_from_basis)
    @testset "Crash produces an owned feasible structural diagonal basis" begin
        for T in (Float32, Float64, BigFloat, Rational{Int64}, Rational{BigInt}),
            method in (:pfi, :forrest_tomlin, :suhl_suhl, :bartels_golub),
            backend in (:native, :markowitz)
            p = LinearProblem(sparse(T[2 0; 0 3]), ones(T,2); row_lower=T[2,3])
            original = deepcopy(p)
            options = SolverOptions(T; verbose=false, basis_update=method,
                basis_refactorization=backend)
            policy = JSimplex.NumericalPolicy(T; crash=true)
            b = JSimplex.crash_basis(p,options,policy,()->false)
            @test Set(b.basic_indices) == Set([1,2])
            ws = JSimplex.initialize_from_basis(p,b,options; policy)
            @test ws.primal[1:2] ≈ ones(T,2)
            @test iszero(JSimplex.primal_infeasibility(ws))
            @test JSimplex._recomputed_basis_reliable(ws)
            @test ws.basis.basic_indices !== b.basic_indices
            @test ws.basis.states !== b.states
            @test p.A == original.A && p.objective == original.objective
            @test p.column_lower == original.column_lower && p.column_upper == original.column_upper
            @test p.row_lower == original.row_lower && p.row_upper == original.row_upper
        end
    end

    @testset "Crash chooses legal objective-aware nonbasic states" begin
        for sense in (MIN_SENSE,MAX_SENSE)
            p = LinearProblem(spzeros(0,4),[-1.0,1.0,-2.0,3.0];
                column_lower=[0.0,-Inf,2.0,-Inf], column_upper=[4.0,5.0,2.0,Inf],
                objective_sense=sense)
            options = SolverOptions(verbose=false)
            policy = JSimplex.NumericalPolicy(Float64;crash=true)
            b = JSimplex.crash_basis(p,options,policy,()->false)
            @test isempty(b.basic_indices)
            @test b.states == [sense == MIN_SENSE ? JSimplex.AT_UPPER : JSimplex.AT_LOWER,
                JSimplex.AT_UPPER,JSimplex.AT_LOWER,JSimplex.FREE_NONBASIC]
            ws = JSimplex.initialize_from_basis(p,b,options;policy)
            @test ws.primal == [sense == MIN_SENSE ? 4.0 : 0.0,5.0,2.0,0.0]
        end
        p = LinearProblem(spzeros(2,0),Float64[];row_lower=[0.0,1.0])
        b = JSimplex.crash_basis(p,SolverOptions(verbose=false),
            JSimplex.NumericalPolicy(Float64;crash=true),()->false)
        @test b.basic_indices == [1,2]
    end

    @testset "Crash guards dependent columns and zero columns" begin
        p = LinearProblem(sparse([1.0 1 0;1 1+1e-12 0]),ones(3);
            row_lower=[1.0,2.0],row_upper=[1.0,2.0])
        options = SolverOptions(verbose=false)
        policy = JSimplex.NumericalPolicy(Float64;crash=true)
        b = JSimplex.crash_basis(p,options,policy,()->false)
        @test !(1 in b.basic_indices && 2 in b.basic_indices)
        @test !(3 in b.basic_indices)
        ws = JSimplex.initialize_from_basis(p,b,options;policy)
        @test JSimplex._recomputed_basis_reliable(ws)
        slack = JSimplex.initialize_workspace(p,options)
        @test JSimplex.primal_infeasibility(ws) <= JSimplex.primal_infeasibility(slack)
        invalid = JSimplex.Basis([1,1],fill(JSimplex.BASIC,5))
        @test_throws ArgumentError JSimplex.initialize_from_basis(p,invalid,options;policy)
    end

    @testset "Crash consumes the existing clock and completed-step budget" begin
        p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,crash=true)
        for algorithm in (:primal,:dual)
            options = SolverOptions(verbose=false,presolve=false,algorithm=algorithm,iteration_limit=1)
            d = JSimplex.SimplexDiagnostics(kernel_timing=true)
            r = JSimplex._solve_diagnosed(p,d;options,numerical_policy=policy)
            @test r.status == ITERATION_LIMIT
            @test r.statistics.iterations == 1
            @test JSimplex.event_count(d,:crash_pivot) == 1
            progress = JSimplex.SimplexProgressContext(p;start_ns=time_ns()-UInt64(2_000_000_000),
                numerical_policy=policy)
            timed = SolverOptions(verbose=false,presolve=false,algorithm=algorithm,time_limit=0.1)
            run = algorithm == :primal ? JSimplex._solve_continuous_primal(p,timed;progress) :
                JSimplex._solve_continuous_dual(p,timed;progress)
            @test run.status == TIME_LIMIT
            @test run.iterations == 0
        end
        calls = Ref(0)
        b = JSimplex.crash_basis(p,SolverOptions(verbose=false),policy,()->(calls[]+=1)>2)
        @test b.basic_indices == [3,4]
        failure = SingularException(42)
        try
            JSimplex.crash_basis(p,SolverOptions(verbose=false),policy,()->throw(failure))
            @test false
        catch exception
            @test exception === failure
        end
    end
end
