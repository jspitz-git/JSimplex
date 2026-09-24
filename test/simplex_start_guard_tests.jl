using Test, JSimplex, SparseArrays, LinearAlgebra

@testset "Crash fill rejection retains verified slack state" begin
    p = LinearProblem(sparse([1.0 1;1 2]),ones(2);row_lower=[1.0,2.0])
    d = JSimplex.SimplexDiagnostics()
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    baseline = copy(initial.primal)
    ws,expired = JSimplex._crash_workspace(initial,()->false;fill_limit=1)
    @test !expired
    @test ws.basis.basic_indices == [3,4]
    @test ws.primal == baseline
    @test JSimplex.event_count(d,:crash_rejected_fill) > 0
    @test JSimplex._recomputed_basis_reliable(ws)
    @test_throws ArgumentError JSimplex._crash_workspace(initial,()->false;fill_limit=Inf)
end

@testset "Crash interruption retains completed work and latches the stop" begin
    for algorithm in (:primal,:dual)
        p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
        policy = JSimplex.NumericalPolicy(Float64;crash=true)
        interrupted = Ref(false)
        d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
            reason == :crash_pivot && (interrupted[]=true)
        end)
        progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
        options = SolverOptions(;verbose=false,presolve=false,algorithm)
        stop = ()->begin
            value = interrupted[]
            interrupted[] = false
            value
        end
        run = algorithm == :primal ? JSimplex._solve_continuous_primal(p,options;progress,stop_requested=stop) :
            JSimplex._solve_continuous_dual(p,options;progress,stop_requested=stop)
        @test run.status == TIME_LIMIT
        @test run.iterations == 1
        @test JSimplex.event_count(d,:crash_fallback) == 1
        @test JSimplex.event_count(d,:phase_one) == 0
        @test JSimplex.event_count(d,:phase_dual) == 0
    end
end

@testset "Crash observer failures retain their cause" begin
    p = LinearProblem(sparse(reshape([2.0],1,1)),[1.0];row_lower=[2.0])
    for event in (:phase_crash,:crash_pivot,:crash_accepted)
        failure = SingularException(42)
        d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->reason == event ? throw(failure) : nothing)
        policy = JSimplex.NumericalPolicy(Float64;crash=true)
        progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
        try
            JSimplex._solve_continuous_primal(p,SolverOptions(verbose=false);progress)
            @test false
        catch exception
            @test exception isa JSimplex.DiagnosticObserverFailure
            @test exception.cause === failure
        end
    end
end

@testset "Crash skips phase one only after measured feasibility" begin
    p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
    for algorithm in (:primal,:dual), crash in (false,true)
        d = JSimplex.SimplexDiagnostics(kernel_timing=true)
        policy = JSimplex.NumericalPolicy(Float64;simplex_strategy=:adaptive,crash)
        options = SolverOptions(;verbose=false,presolve=false,algorithm,simplex_strategy=:adaptive)
        result = JSimplex._solve_diagnosed(p,d;options,numerical_policy=policy)
        @test result.status == OPTIMAL
        @test result.objective_value ≈ 2.0
        @test result.primal ≈ ones(2)
        @test JSimplex.event_count(d,:crash_pivot) == (crash ? 2 : 0)
        @test d.kernel_calls[:crash] == (crash ? 1 : 0)
        if algorithm == :primal
            @test JSimplex.event_count(d,:phase_one) == (crash ? 0 : 1)
        end
    end
end

@testset "Imported start rejects singular bases and illegal nonbasic bounds" begin
    p = LinearProblem(sparse([1.0 1;1 1]),ones(2);row_lower=ones(2))
    options = SolverOptions(verbose=false)
    b = JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    @test_throws Union{SingularException,ZeroPivotException,JSimplex._UnreliableBasisSolve} JSimplex.initialize_from_basis(p,b,options)
    b = JSimplex.Basis([3,4],[JSimplex.FREE_NONBASIC,JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC])
    @test_throws ArgumentError JSimplex.initialize_from_basis(p,b,options)
    b = JSimplex.Basis([3,4],[JSimplex.AT_UPPER,JSimplex.AT_LOWER,JSimplex.BASIC,JSimplex.BASIC])
    @test_throws ArgumentError JSimplex.initialize_from_basis(p,b,options)
end

@testset "Crash preserves stored BigFloat precision below ambient precision" begin
    setprecision(BigFloat,256) do
        coefficient = 1+BigFloat(2)^-100
        p = LinearProblem(sparse(reshape([coefficient],1,1)),BigFloat[1];row_lower=[coefficient])
        policy = JSimplex.NumericalPolicy(BigFloat;crash=true)
        options = SolverOptions(BigFloat;verbose=false)
        setprecision(BigFloat,64) do
            b = JSimplex.crash_basis(p,options,policy,()->false)
            ws = JSimplex.initialize_from_basis(p,b,options;policy)
            @test ws.primal[1] == 1
            @test precision(ws.primal[1]) >= 256
            @test precision(BigFloat) == 64
            @test p.A[1,1] == coefficient
        end
    end
end

@testset "Crash arithmetic overflow falls back without changing exact input" begin
    T = Rational{Int64}
    p = LinearProblem(sparse(reshape(T[1,1],1,2)),T[-1,-1];
        column_upper=T[typemax(Int64),typemax(Int64)])
    original = deepcopy(p)
    policy = JSimplex.NumericalPolicy(T;crash=true)
    d = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d)
    initial = JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test ws === initial
    @test !expired
    @test JSimplex.event_count(d,:crash_fallback) == 1
    @test p.A == original.A && p.column_upper == original.column_upper
    @test eltype(ws.primal) == T
end

@testset "Crash drivers create the slack fallback at stored precision" begin
    setprecision(BigFloat,256) do
        p = LinearProblem(sparse(reshape(BigFloat[1+BigFloat(2)^-100],1,1)),BigFloat[1];
            column_lower=BigFloat[1],row_lower=BigFloat[1])
        policy = JSimplex.NumericalPolicy(BigFloat;crash=true)
        for algorithm in (:primal,:dual)
            first_slack = Ref{Union{Nothing,BigFloat}}(nothing)
            d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
                if reason == :refactor_initial && isnothing(first_slack[])
                    first_slack[] = copy(ws.primal[2])
                end
            end)
            progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy,diagnostics=d)
            options = SolverOptions(BigFloat;verbose=false,algorithm)
            setprecision(BigFloat,64) do
                stop = ()->!isnothing(first_slack[])
                run = algorithm == :primal ? JSimplex._solve_continuous_primal(p,options;progress,stop_requested=stop) :
                    JSimplex._solve_continuous_dual(p,options;progress,stop_requested=stop)
                @test run.status == TIME_LIMIT
                @test first_slack[] == p.A[1,1]
                @test precision(first_slack[]) >= 256
                @test precision(BigFloat) == 64
            end
        end
    end
end
