using Test, JSimplex, SparseArrays

@testset "Crash respects fixed, upper-only and free variables with rows" begin
    p = LinearProblem(spdiagm(0=>ones(3)),[0.0,-1.0,1.0];
        column_lower=[2.0,-Inf,-Inf],column_upper=[2.0,3.0,Inf],
        row_lower=[2.0,3.0,1.0],row_upper=[2.0,3.0,1.0])
    for algorithm in (:primal,:dual)
        options = SolverOptions(;verbose=false,algorithm)
        policy = JSimplex.NumericalPolicy(Float64;crash=true)
        basis = JSimplex.crash_basis(p,options,policy,()->false)
        ws = JSimplex.initialize_from_basis(p,basis,options;policy)
        @test ws.primal[1:3] == [2.0,3.0,1.0]
        @test basis.states[1:3] == [JSimplex.AT_LOWER,JSimplex.AT_UPPER,JSimplex.BASIC]
        @test iszero(JSimplex.primal_infeasibility(ws))
    end
end

@testset "Crash rejects objective-aware states with worse primal violation" begin
    p = LinearProblem(sparse([1.0 1.0]),[-1.0,-1.0];column_upper=ones(2),row_upper=[0.0])
    d = JSimplex.SimplexDiagnostics()
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test ws === initial
    @test !expired
    @test ws.primal == zeros(3)
    @test JSimplex.event_count(d,:crash_fallback) == 1
    @test ws.iterations == 0
end

@testset "Crash interruption after final factorization uses no fresh budget" begin
    p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
    done = Ref(false)
    d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        reason == :refactor_other && (done[]=true)
    end)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    ws,expired = JSimplex._crash_workspace(initial,()->done[])
    @test expired
    @test ws === initial
    @test ws.iterations == 2
    @test ws.refactorizations >= 2
    @test ws.basis.basic_indices == [3,4]
    @test JSimplex.event_count(d,:crash_accepted) == 0
end

@testset "Crash handles the empty model" begin
    p = LinearProblem(spzeros(0,0),Float64[])
    options = SolverOptions(verbose=false)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    b = JSimplex.crash_basis(p,options,policy,()->false)
    @test isempty(b.basic_indices) && isempty(b.states)
    ws = JSimplex.initialize_from_basis(p,b,options;policy)
    @test isempty(ws.primal)
    @test JSimplex._recomputed_basis_reliable(ws)
end

module CrashLoggerTests
using Test, JSimplex, Logging, LinearAlgebra
struct FailingLogger <: AbstractLogger
    failure::SingularException
end
Logging.min_enabled_level(::FailingLogger) = Debug
Logging.shouldlog(::FailingLogger,args...) = true
Logging.catch_exceptions(::FailingLogger) = false
function Logging.handle_message(logger::FailingLogger,level,message,args...;kwargs...)
    message == "Refactorizing basis" && throw(logger.failure)
end
@testset "Crash refactorization logger failures propagate unchanged" begin
    p = LinearProblem(JSimplex.sparse(reshape([2.0],1,1)),[1.0];row_lower=[2.0])
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    for algorithm in (:primal,:dual)
        failure = SingularException(42)
        progress = JSimplex.SimplexProgressContext(p;numerical_policy=policy)
        options = SolverOptions(;verbose=false,algorithm)
        try
            with_logger(FailingLogger(failure)) do
                algorithm == :primal ? JSimplex._solve_continuous_primal(p,options;progress) :
                    JSimplex._solve_continuous_dual(p,options;progress)
            end
            @test false
        catch exception
            @test exception === failure
        end
    end
end
end

@testset "Crash refuses a relatively tiny pivot even for a feasible structural basis" begin
    delta = 1e-14
    p = LinearProblem(sparse([1.0 1.0;1.0 1.0+delta]),ones(2);
        row_lower=[2.0,2.0+delta],row_upper=[2.0,2.0+delta])
    options = SolverOptions(;verbose=false,algorithm=:dual,primal_tolerance=1e-16)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    d = JSimplex.SimplexDiagnostics()
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,options;progress)
    ws,expired = JSimplex._crash_workspace(initial,()->false)
    @test !expired
    @test JSimplex.event_count(d,:crash_pivot) == 1
    @test !(1 in ws.basis.basic_indices && 2 in ws.basis.basic_indices)
    @test JSimplex._recomputed_basis_reliable(ws)
end

# One native fallback observer boundary; retained trial values are endpoint observations.
using LinearAlgebra: SingularException

mutable struct CrashFallbackObserverProbe
    armed::Bool
    refactor_hits::Int
    fallback_hits::Int
    callback_count::Int
    pivot_hits::Int
    callbacks_after_fallback::Int
    trial::Any
    fallback::Any
    refactor_work::NTuple{2,Int}
    fallback_record::NTuple{7,Int}
    sentinel::SingularException
end

function crash_fallback_observer_owners(ws)
    return (ws,ws.basis,ws.factorization,ws.scratch,ws.basis.basic_indices,
        ws.basis.states,ws.primal,ws.reduced_costs,ws.costs,ws.lower,ws.upper,
        ws.problem,ws.progress,ws.progress.diagnostics,ws.options,
        ws.progress.numerical_policy,ws.progress.scaling)
end

function crash_fallback_observer_record(ws,callbacks)
    d = ws.progress.diagnostics
    return (ws.iterations,ws.refactorizations,
        JSimplex.event_count(d,:crash_pivot),JSimplex.event_count(d,:refactor_other),
        JSimplex.event_count(d,:crash_fallback),JSimplex.event_count(d,:crash_accepted),
        callbacks)
end

function crash_fallback_observer_checks()
    failure = SingularException(42)
    probe = CrashFallbackObserverProbe(false,0,0,0,0,0,nothing,nothing,(-1,-1),
        (-1,-1,-1,-1,-1,-1,-1),failure)
    p = LinearProblem(spdiagm(0=>[2.0,3.0]),ones(2);row_lower=[2.0,3.0])
    done = Ref(false)
    d = JSimplex.SimplexDiagnostics(;observer=(reason,ws)->begin
        probe.armed || return nothing
        probe.callback_count += 1
        probe.fallback_hits > 0 && (probe.callbacks_after_fallback += 1)
        reason == :crash_pivot && (probe.pivot_hits += 1)
        reason == :refactor_other && (done[]=true)
        if reason == :refactor_other
            probe.refactor_hits += 1
            if probe.refactor_hits == 1
                probe.trial = ws
                probe.refactor_work = (ws.iterations,ws.refactorizations)
            end
        elseif reason == :crash_fallback
            probe.fallback_hits += 1
            if probe.fallback_hits == 1
                probe.fallback = ws
                probe.fallback_record = crash_fallback_observer_record(ws,probe.callback_count)
            end
            throw(probe.sentinel)
        end
        return nothing
    end)
    policy = JSimplex.NumericalPolicy(Float64;crash=true)
    progress = JSimplex.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy)
    initial = JSimplex.initialize_workspace(p,SolverOptions(verbose=false);progress)
    entry_owners = crash_fallback_observer_owners(initial)
    entry_values = (basic=copy(initial.basis.basic_indices),states=copy(initial.basis.states),
        primal=copy(initial.primal),prices=copy(initial.reduced_costs),costs=copy(initial.costs),
        lower=copy(initial.lower),upper=copy(initial.upper))
    entry_clock = (progress.start_ns,progress.iteration_offset,progress.refactorization_offset)
    entry_work = (initial.iterations,initial.refactorizations)
    probe.armed = true
    caught = nothing
    returned = false
    try
        ws,expired = JSimplex._crash_workspace(initial,()->done[])
        returned = true
    catch exception
        caught = exception
    end
    after_record = crash_fallback_observer_record(initial,probe.callback_count)
    after_owners = crash_fallback_observer_owners(initial)
    trial_present = !isnothing(probe.trial)
    trial_owners = trial_present ? crash_fallback_observer_owners(probe.trial) : nothing
    checks = (
        no_return = !returned,
        wrapped_type = caught isa JSimplex.DiagnosticObserverFailure,
        original_cause = caught isa JSimplex.DiagnosticObserverFailure && caught.cause === failure,
        sentinel_identity = probe.sentinel === failure,
        refactor_once = probe.refactor_hits == 1,
        fallback_once = probe.fallback_hits == 1,
        two_pivot_callbacks = probe.pivot_hits == 2,
        done_latched = done[],
        trial_captured = trial_present,
        trial_distinct = trial_present && probe.trial !== initial,
        fallback_initial = probe.fallback === initial,
        trial_owned_containers = trial_present && all(i->trial_owners[i] !== entry_owners[i],1:11),
        trial_shared_problem = trial_present && trial_owners[12] === entry_owners[12],
        trial_shared_progress = trial_present && trial_owners[13] === entry_owners[13],
        trial_shared_diagnostics = trial_present && trial_owners[14] === entry_owners[14],
        trial_options_value = trial_present && trial_owners[15] === entry_owners[15],
        trial_shared_policy = trial_present && trial_owners[16] === entry_owners[16],
        trial_shared_scaling = trial_present && trial_owners[17] === entry_owners[17],
        initial_owners_preserved = all(i->after_owners[i] === entry_owners[i],1:17),
        basic_values_preserved = initial.basis.basic_indices == entry_values.basic,
        state_values_preserved = initial.basis.states == entry_values.states,
        primal_values_preserved = initial.primal == entry_values.primal,
        price_values_preserved = initial.reduced_costs == entry_values.prices,
        cost_values_preserved = initial.costs == entry_values.costs,
        lower_values_preserved = initial.lower == entry_values.lower,
        upper_values_preserved = initial.upper == entry_values.upper,
        slack_indices = length(initial.basis.basic_indices) == 2 &&
            initial.basis.basic_indices[1] == 3 && initial.basis.basic_indices[2] == 4,
        merged_iterations = probe.fallback_record[1] == max(entry_work[1],probe.refactor_work[1]),
        merged_refactorizations = probe.fallback_record[2] == max(entry_work[2]+1,probe.refactor_work[2]),
        inherited_iterations = probe.fallback_record[1] == 2,
        inherited_refactor_bound = probe.fallback_record[2] >= 2,
        pivot_recorded = probe.fallback_record[3] == 2,
        refactor_recorded = probe.fallback_record[4] == 1,
        fallback_already_recorded = probe.fallback_record[5] == 1,
        no_acceptance = probe.fallback_record[6] == 0,
        no_later_selected_work_events = after_record == probe.fallback_record,
        no_later_callback = probe.callbacks_after_fallback == 0,
        start_clock_preserved = progress.start_ns === entry_clock[1],
        iteration_offset_preserved = progress.iteration_offset == entry_clock[2],
        refactor_offset_preserved = progress.refactorization_offset == entry_clock[3],
        native_refinement_off = !policy.solve_refinement,
        native_recovery_off = !policy.recovery,
        native_profile = !policy.stable_ratio && !policy.pivot_validation,
        hypersparse_off = !policy.hypersparse,
        sparse_pricing_off = !policy.sparse_pricing,
        phase_one_off = !policy.phase_one,
        timing_off = !d.kernel_timing,
        infinite_time = initial.options.time_limit == Inf,
        unchanged_limits = initial.options.iteration_limit == 100_000 && initial.options.refactorization_interval == 20,
        unchanged_routing = initial.options.algorithm === :dual && initial.options.basis_update === :pfi &&
            initial.options.basis_refactorization === :native && initial.options.simplex_strategy === :legacy,
    )
    return checks
end

@testset "Crash fallback observer preserves initial ownership after work merge" begin
    checks = crash_fallback_observer_checks()
    @test checks.no_return
    @test checks.wrapped_type
    @test checks.original_cause
    @test checks.sentinel_identity
    @test checks.refactor_once
    @test checks.fallback_once
    @test checks.two_pivot_callbacks
    @test checks.done_latched
    @test checks.trial_captured
    @test checks.trial_distinct
    @test checks.fallback_initial
    @test checks.trial_owned_containers
    @test checks.trial_shared_problem
    @test checks.trial_shared_progress
    @test checks.trial_shared_diagnostics
    @test checks.trial_options_value
    @test checks.trial_shared_policy
    @test checks.trial_shared_scaling
    @test checks.initial_owners_preserved
    @test checks.basic_values_preserved
    @test checks.state_values_preserved
    @test checks.primal_values_preserved
    @test checks.price_values_preserved
    @test checks.cost_values_preserved
    @test checks.lower_values_preserved
    @test checks.upper_values_preserved
    @test checks.slack_indices
    @test checks.merged_iterations
    @test checks.merged_refactorizations
    @test checks.inherited_iterations
    @test checks.inherited_refactor_bound
    @test checks.pivot_recorded
    @test checks.refactor_recorded
    @test checks.fallback_already_recorded
    @test checks.no_acceptance
    @test checks.no_later_selected_work_events
    @test checks.no_later_callback
    @test checks.start_clock_preserved
    @test checks.iteration_offset_preserved
    @test checks.refactor_offset_preserved
    @test checks.native_refinement_off
    @test checks.native_recovery_off
    @test checks.native_profile
    @test checks.hypersparse_off
    @test checks.sparse_pricing_off
    @test checks.phase_one_off
    @test checks.timing_off
    @test checks.infinite_time
    @test checks.unchanged_limits
    @test checks.unchanged_routing
end
