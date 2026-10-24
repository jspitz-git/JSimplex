module StagnationThresholdTests
using Test, JSimplex, SparseArrays

# The unchanged generic method is the reference for all supported scalar types.
reference_values(ws,state,algorithm) = invoke(JSimplex._workspace_stagnation_values,
    Tuple{Any,JSimplex.WorkspaceStagnation,Any},ws,state,algorithm)
same(a,b) = isequal(a,b)
same(a::BigFloat,b::BigFloat) = isequal(a,b) && precision(a)==precision(b)
same(a::Tuple,b::Tuple) = length(a)==length(b) && all(same(a[i],b[i]) for i in eachindex(a))
function metric_fixture(::Type{T},n) where T
    basics=collect(1:(n÷2))
    states=[i<=length(basics) ? JSimplex.BASIC :
        i%3==0 ? JSimplex.FREE_NONBASIC : i%3==1 ? JSimplex.AT_LOWER : JSimplex.AT_UPPER for i in 1:n]
    lower=[JSimplex.Bound(T(-1)) for _ in 1:n]
    upper=[JSimplex.Bound(T(2)) for _ in 1:n]
    for i in 7:7:n
        lower[i]=upper[i]=JSimplex.Bound(T(1))
    end
    ws=(costs=[T(i%11-5)/T(7) for i in 1:n],
        primal=[T(i%13-6)/T(3) for i in 1:n],
        reduced_costs=[T(i%7-3)/T(16) for i in 1:n],
        basis=(basic_indices=basics,states=states),lower=lower,upper=upper,
        options=(primal_tolerance=one(T)/T(16),dual_tolerance=one(T)/T(16)))
    monitor=JSimplex.StagnationMonitor{T}(4;objective_scale=one(T)/T(8),
        primal_scale=one(T)/T(4),dual_scale=one(T)/T(8))
    state=JSimplex.WorkspaceStagnation(monitor,UInt(1),UInt(1),0,T(3),T(7))
    return ws,state
end
function check_metrics(ws,state,algorithm)
    before=deepcopy((ws.costs,ws.primal,ws.reduced_costs,ws.lower,ws.upper))
    owners=map(copy,(ws.costs,ws.primal,ws.reduced_costs,ws.lower,ws.upper))
    actual=JSimplex._workspace_stagnation_values(ws,state,algorithm)
    @test same(actual,reference_values(ws,state,algorithm))
    for (a,b,own) in zip((ws.costs,ws.primal,ws.reduced_costs,ws.lower,ws.upper),before,owners)
        @test isequal(a,b)
        @test all(a[i]===own[i] for i in eachindex(a))
    end
end

@testset "Stagnation normalized tolerances preserve metrics and inputs" begin
    for T in (Float32,Float64,BigFloat,Rational{BigInt}),n in (0,1,8,64),algorithm in (:primal,:dual)
        ws,state=metric_fixture(T,n)
        check_metrics(ws,state,algorithm)
        # A new call must use the current scales, rather than a persistent cache.
        state.cost_scale*=T(2);state.value_scale*=T(3)
        check_metrics(ws,state,algorithm)
    end
    for bits in (64,128,256),rounding_mode in (RoundNearest,RoundDown,RoundUp)
        ws,state=setprecision(BigFloat,192) do
            metric_fixture(BigFloat,8)
        end
        setprecision(BigFloat,bits) do
            setrounding(BigFloat,rounding_mode) do
                for algorithm in (:primal,:dual)
                    check_metrics(ws,state,algorithm)
                end
            end
        end
    end
end

@testset "Unused BigFloat thresholds remain lazy" begin
    _,state=metric_fixture(BigFloat,0)
    # No options field: eager threshold computation would introduce a new error.
    empty_ws=(costs=BigFloat[],basis=(basic_indices=Int[],states=JSimplex.VariableState[]))
    @test same(JSimplex._workspace_stagnation_values(empty_ws,state,:dual),reference_values(empty_ws,state,:dual))
    # A nonempty objective loop can still have no eligible comparison.
    basic_ws=(costs=BigFloat[1],primal=BigFloat[2],
        basis=(basic_indices=Int[],states=[JSimplex.BASIC]))
    @test same(JSimplex._workspace_stagnation_values(basic_ws,state,:dual),reference_values(basic_ws,state,:dual))
    # Each tolerance is independently lazy, not just the pair as a whole.
    bounds=(lower=[JSimplex.Bound(BigFloat(0))],upper=[JSimplex.Bound(BigFloat(1))])
    dual_ws=merge(basic_ws,bounds,(reduced_costs=BigFloat[-1],
        basis=(basic_indices=Int[],states=[JSimplex.AT_LOWER]),options=(dual_tolerance=BigFloat(0),)))
    primal_ws=merge(basic_ws,bounds,(basis=(basic_indices=[1],states=[JSimplex.BASIC]),
        options=(primal_tolerance=BigFloat(0),)))
    for ws in (dual_ws,primal_ws)
        @test same(JSimplex._workspace_stagnation_values(ws,state,:dual),reference_values(ws,state,:dual))
    end
    # Earlier data errors must still precede access to the unused tolerance.
    bad_dual=merge(dual_ws,(reduced_costs=BigFloat[],options=NamedTuple()))
    bad_primal=merge(primal_ws,(lower=JSimplex.Bound{BigFloat}[],options=NamedTuple()))
    for ws in (bad_dual,bad_primal)
        @test_throws BoundsError reference_values(ws,state,:dual)
        @test_throws BoundsError JSimplex._workspace_stagnation_values(ws,state,:dual)
    end
end

@testset "BigFloat observer retains context, callbacks and stored precision" begin
    count=Ref(0);mode=Ref(:mutate);sentinel=ErrorException("stagnation threshold observer")
    callback=(reason,ws)->begin
        count[]+=1
        if reason==:stagnation_watch
            mode[]==:throw && throw(sentinel)
            if mode[]==:mutate
                ws.upper[1]=JSimplex.Bound(BigFloat(7));mode[]=:throw
            end
        end
        nothing
    end
    ws=setprecision(BigFloat,192) do
        problem=LinearProblem(sparse(BigFloat[1;;]),BigFloat[1];row_lower=BigFloat[1])
        policy=JSimplex.NumericalPolicy(BigFloat;adaptive_stalling=true,stagnation_window=4,
            refactor_timing=false)
        diagnostics=JSimplex.SimplexDiagnostics(;observer=callback)
        JSimplex._initialize_workspace_state(problem,SolverOptions(BigFloat;verbose=false);
            progress=JSimplex.SimplexProgressContext(problem;numerical_policy=policy,diagnostics))
    end
    setprecision(BigFloat,64) do
        for i in 1:4
            ws.iterations=i
            @test JSimplex._observe_stagnation!(ws,:dual,0,0)==(i==4 ? :watch : :progress)
            @test precision(BigFloat)==64
        end
        old=ws.scratch.stagnation
        ws.iterations=5
        @test JSimplex._observe_stagnation!(ws,:dual,0,0)==:progress
        @test ws.scratch.stagnation!==old
        @test ws.scratch.stagnation.monitor.observations==1
        for i in 6:7
            ws.iterations=i
            @test JSimplex._observe_stagnation!(ws,:dual,0,0)==:progress
        end
        ws.iterations=8
        error=try
            JSimplex._observe_stagnation!(ws,:dual,0,0);nothing
        catch exception
            exception
        end
        @test error isa JSimplex.DiagnosticObserverFailure && error.cause===sentinel
        @test precision(BigFloat)==64
        @test count[]==2
        @test JSimplex.event_count(ws.progress.diagnostics,:stagnation_watch)==2
        @test precision(ws.scratch.stagnation.monitor.end_objective)==192
        @test precision(ws.scratch.stagnation.cost_scale)==192
        # A cost-only dual rebase retains this history object and its cadence.
        mode[]=:count;history=ws.scratch.stagnation
        ws.costs[1]+=BigFloat(1);ws.iterations=9
        JSimplex._observe_stagnation!(ws,:dual,0,0)
        @test ws.scratch.stagnation===history
        @test history.monitor.observations==5
        @test JSimplex.event_count(ws.progress.diagnostics,:stagnation_cost_rebase)==1
        @test precision(BigFloat)==64
    end
end

@noinline function allocated_values(ws::W,state::S) where {W,S}
    reference=@allocated reference_values(ws,state,:dual)
    actual=@allocated JSimplex._workspace_stagnation_values(ws,state,:dual)
    return reference,actual
end
@testset "BigFloat normalization removes repeated scalar allocations" begin
    ws,state=metric_fixture(BigFloat,128)
    reference_values(ws,state,:dual)
    JSimplex._workspace_stagnation_values(ws,state,:dual)
    allocated_values(ws,state) # Compile both typed measurement paths first.
    reference,actual=allocated_values(ws,state)
    @test actual < reference
end
end # module
