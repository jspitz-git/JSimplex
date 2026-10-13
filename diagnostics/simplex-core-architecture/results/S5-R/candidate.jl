# S5-R UNEXECUTED diagnostic candidate. A separate reviewed launcher is required.
using JSimplex, SparseArrays, TOML

mutable struct S5RProbe
    workspace::Any
    default_indices::Any
    default_states::Any
    imported_indices::Any
    imported_states::Any
    stage::Int
    ordered::Bool
    callbacks::Int
    initial_hits::Int
    imported_hits::Int
    checkpoint_hits::Int
    stop_calls::Int
    throws::Int
    armed::Bool
    at_throw::Any
end
S5RProbe() = S5RProbe(nothing,nothing,nothing,nothing,nothing,0,true,0,0,0,0,0,0,false,nothing)

function s5r_selected_work(ws)
    d=ws.progress.diagnostics
    return (ftran=d.kernel_calls[:ftran],btran=d.kernel_calls[:btran],
        factor=d.kernel_calls[:refactorization],iterations=ws.iterations,
        refactors=ws.refactorizations,checkpoint=d.counts[:checkpoint],
        initial=d.counts[:refactor_initial],other=d.counts[:refactor_other],
        correction=d.counts[:correction],attempt=d.counts[:correction_attempt],
        events=length(d.events),last=isempty(d.events) ? :none : d.events[end],
        phase=ws.scratch.phase_generation,history=length(ws.scratch.checkpoints))
end

function (probe::S5RProbe)(reason,state)
    probe.callbacks += 1
    if reason === :checkpoint && probe.stage == 0
        probe.ordered &= probe.callbacks == 1
        probe.stage = 1
    elseif reason === :refactor_initial && probe.stage == 1
        probe.initial_hits += 1
        probe.workspace = state
        probe.default_indices = state.basis.basic_indices
        probe.default_states = state.basis.states
        probe.ordered &= probe.callbacks == 2 && state.refactorizations == 0
        probe.stage = 2
    elseif reason === :refactor_other && probe.stage == 2 && state === probe.workspace
        probe.imported_hits += 1
        probe.imported_indices = state.basis.basic_indices
        probe.imported_states = state.basis.states
        probe.ordered &= probe.callbacks == 3 && state.refactorizations == 1
        probe.stage = 3
    elseif reason === :checkpoint && probe.stage == 3 && state === probe.workspace
        probe.checkpoint_hits += 1
        probe.ordered &= probe.callbacks == 4 && probe.stop_calls == 1
        probe.stage = 4
        probe.armed = true
    else
        probe.ordered = false
    end
    return nothing
end

function s5r_case(output)
    T=Float64; update=:pfi; backend=:native
    probe=S5RProbe()
    d=JSimplex.SimplexDiagnostics(;observer=probe,kernel_timing=true)
    sentinel=ErrorException("S5-R explicit imported-checkpoint stop")
    stop = () -> begin
        probe.stop_calls += 1
        if probe.armed
            probe.ordered &= probe.stage == 4 && probe.stop_calls == 2
            probe.throws += 1
            probe.at_throw = s5r_selected_work(probe.workspace)
            throw(sentinel)
        end
        probe.ordered &= probe.stage == 3 && probe.stop_calls == 1
        return false
    end
    guard=JSimplex._guard_stop_callback(stop)
    # BEGIN SOURCE SETUP
    p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];objective_constant=T(3.5),
        objective_sense=MAX_SENSE,column_lower=[Bound(zero(T)),Bound{T}(nothing)],
        column_upper=[Bound(T(2)),Bound{T}(nothing)],row_lower=T[2,0],row_upper=T[2,0],
        name="precision",row_names=["first","second"],column_names=["boxed","free"])
    options=SolverOptions(T;verbose=false,presolve=false,iteration_limit=30,
        basis_update=update,basis_refactorization=backend,pricing=:devex)
    policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true,crash=true,recovery=true,
        sparse_pricing=true,hypersparse=true,refactor_timing=false,max_refinements=4,
        max_recovery_rounds=5,stagnation_window=8)
    progress=JSimplex.SimplexProgressContext{T,typeof(d)}(time_ns(),T[2,3,4,5],T(7),
        JSimplex.Scaling(T[2,4],T[0.5,2]),7,11,d,policy)
    basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
    # END SOURCE SETUP
    entry=(indices=basis.basic_indices,states=basis.states,start=progress.start_ns,
        objective=progress.objective,scaling=progress.scaling,diagnostics=d,
        policy=policy,options=options,problem=p)
    saved_indices=copy(basis.basic_indices)
    saved_states=copy(basis.states)
    ws=nothing
    caught=nothing
    returned=false
    try
        # BEGIN SOURCE CALL
        ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress,stop=guard)
        # END SOURCE CALL
        returned=true
    catch exception
        caught=exception
    end
    retained=probe.workspace
    present=retained !== nothing
    after=present ? s5r_selected_work(retained) : nothing
    expected=(ftran=2,btran=2,factor=1,iterations=0,refactors=1,checkpoint=1,
        initial=1,other=1,correction=0,attempt=0,events=3,last=:refactor_other,
        phase=UInt(1),history=0)
    checks=(
        no_return=!returned && ws === nothing,
        original_exception=caught === sentinel,
        guarded_exception=guard.exception === sentinel,
        workspace_observed=present,
        exact_order=probe.ordered && probe.stage == 4,
        initial_once=probe.initial_hits == 1,
        imported_once=probe.imported_hits == 1,
        target_once=probe.checkpoint_hits == 1,
        four_callbacks=probe.callbacks == 4,
        two_stops=probe.stop_calls == 2,
        one_throw=probe.throws == 1,
        armed=probe.armed,
        caller_indices_owner=basis.basic_indices === entry.indices,
        caller_states_owner=basis.states === entry.states,
        caller_indices_values=basis.basic_indices == saved_indices,
        caller_states_values=basis.states == saved_states,
        imported_indices_owner=present && retained.basis.basic_indices === probe.imported_indices,
        imported_states_owner=present && retained.basis.states === probe.imported_states,
        indices_not_caller=present && retained.basis.basic_indices !== entry.indices,
        states_not_caller=present && retained.basis.states !== entry.states,
        indices_not_default=present && retained.basis.basic_indices !== probe.default_indices,
        states_not_default=present && retained.basis.states !== probe.default_states,
        imported_indices_values=present && retained.basis.basic_indices == saved_indices,
        imported_states_values=present && retained.basis.states == saved_states,
        problem_shared=present && retained.problem === entry.problem,
        diagnostics_shared=present && retained.progress.diagnostics === entry.diagnostics,
        objective_shared=present && retained.progress.objective === entry.objective,
        objective_constant=present && retained.progress.objective_constant === progress.objective_constant,
        scaling_shared=present && retained.progress.scaling === entry.scaling,
        original_clock=present && retained.progress.start_ns === entry.start,
        iteration_offset=present && retained.progress.iteration_offset == progress.iteration_offset == 7,
        refactor_offset=present && retained.progress.refactorization_offset == progress.refactorization_offset == 11,
        policy_shared=present && retained.progress.numerical_policy === entry.policy,
        native_recovery=policy.numerical_profile === :native && policy.recovery && !policy.solve_refinement,
        sparse_policy=policy.sparse_pricing && policy.hypersparse,
        options_preserved=present && retained.options === entry.options,
        infinite_limit=options.time_limit == Inf,
        selected_at_throw=probe.at_throw == expected,
        selected_after_unwind=after == expected,
        no_later_selected_work=after == probe.at_throw && probe.at_throw !== nothing,
    )
    observations=Dict(
        "caught_type"=>string(typeof(caught)),"sentinel_type"=>string(typeof(sentinel)),
        "guard_exception_type"=>string(typeof(guard.exception)),
        "returned"=>returned,"callbacks"=>probe.callbacks,"stop_calls"=>probe.stop_calls,
        "throws"=>probe.throws,"stage"=>probe.stage,
        "start_ns"=>string(progress.start_ns),"scalar"=>string(T),
        "update"=>string(update),"backend"=>string(backend))
    work_record(x) = isnothing(x) ? Dict("present"=>false) :
        Dict(string(k)=>(v isa Symbol ? string(v) : v) for (k,v) in pairs(x))
    raw=Dict("checks"=>Dict(string(k)=>v for (k,v) in pairs(checks)),
        "observations"=>observations,"at_throw"=>work_record(probe.at_throw),
        "after_unwind"=>work_record(after))
    open(output,"w") do io
        TOML.print(io,raw)
    end
    @assert all(values(checks)) "S5-R selected oracle failed; preserve and stop"
    return nothing
end

length(ARGS) == 1 || error("Expected one fresh raw TOML output path")
ispath(only(ARGS)) && error("Refusing to overwrite an existing result")
s5r_case(only(ARGS))
