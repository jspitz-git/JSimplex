# S5-F diagnostic text: not executed during preparation. Two cases only.
# No production method extension, adapter, residual solve, or public solver call.
module S5JournalInterruption
using TOML, SHA
# A future launcher independently pins this manifest and driver before process start.
# No package imports or fixture work until every frozen file is checked.
const PIN_MANIFEST = TOML.parsefile(joinpath(@__DIR__,"source-pins-reviewed.toml"))
for (path,expected) in PIN_MANIFEST["sha256"]
    bytes2hex(open(sha256,path))==expected || error("source/runtime pin mismatch: "*path)
end
using JSimplex, SparseArrays, LinearAlgebra
const JS = JSimplex
identity_token(x) = isnothing(x) ? "nothing" : string(objectid(x))

# Immutable scalar encoding: never retain a mutable BigFloat from a workspace.
function scalar(x::AbstractFloat)
    return (kind=string(typeof(x)), value=isfinite(x) ? string(Rational{BigInt}(x)) : string(x),
            precision=precision(x), negative=signbit(x),
            bits=x isa Float64 ? bitstring(x) : "")
end
scalar(x::Bound) = isfinite(x) ? (bound="finite", payload=scalar(bound_value(x))) : (bound="absent",)
scalar(x) = string(x)
semantic(x) = x
function semantic(x::NamedTuple)
    haskey(x,:kind) && return (value=x.value,negative=x.negative)
    haskey(x,:payload) && return (bound=x.bound,payload=semantic(x.payload))
    return x
end
function fields(x)
    return NamedTuple{fieldnames(typeof(x))}(Tuple(scalar(getfield(x,k)) for k in fieldnames(typeof(x))))
end
same_typed_values(a,b) = keys(a)==keys(b) && all(semantic(a[k])==semantic(b[k]) for k in keys(a))
same_vector_values(a,b) = length(a)==length(b) && all(semantic(a[i])==semantic(b[i]) for i in eachindex(a))
function stored128(x)
    x isa NamedTuple || return true
    haskey(x,:payload) && return stored128(x.payload)
    return !haskey(x,:kind) || x.precision==128
end
array_record(a) = (identity=identity_token(a),values=map(scalar,a))

function snapshot(ws; checkpoint::Bool)
    j=ws.scratch.perturbations; b=j.bounds; p=ws.problem; g=ws.progress
    arrays=Dict{Symbol,Any}()
    # Exactly 26 arrays / 63 scalar entries for this m=1,n=2 fixture.
    for (key,a) in (
        (:costs,ws.costs),(:lower,ws.lower),(:upper,ws.upper),
        (:original_costs,j.original_costs),(:active_costs,j.active_costs),
        (:original_lower,b.original_lower),(:original_upper,b.original_upper),
        (:active_lower,b.active_lower),(:active_upper,b.active_upper),
        (:primal,ws.primal),(:reduced_costs,ws.reduced_costs),(:weights,ws.pricing_weights),
        (:basis,ws.basis.basic_indices),(:states,ws.basis.states),(:devex,ws.devex_reference),
        (:colptr,p.A.colptr),(:rowval,p.A.rowval),(:nzval,p.A.nzval),(:objective,p.objective),
        (:row_lower,p.row_lower),(:row_upper,p.row_upper),
        (:column_lower,p.column_lower),(:column_upper,p.column_upper),
        (:progress_objective,g.objective),(:row_scaling,g.scaling.row_factors),
        (:column_scaling,g.scaling.column_factors))
        arrays[key]=array_record(a)
    end
    ck=nothing
    if checkpoint
        @assert length(ws.scratch.checkpoints)==1
        c=only(ws.scratch.checkpoints)
        for (key,a) in ((:checkpoint_basis,c.basis.basic_indices),(:checkpoint_states,c.basis.states),
                        (:checkpoint_costs,c.costs),(:checkpoint_lower,c.lower),(:checkpoint_upper,c.upper))
            arrays[key]=array_record(a)
        end
        ck=(identity=identity_token(c),model=c.working_model,phase=c.phase,perturbed=c.perturbed)
    end
    cache=ws.scratch.sparse_pricing
    metadata=(workspace=identity_token(ws),scalar_type=string(eltype(ws.costs)),journal=identity_token(j),bounds=identity_token(b),
        owner=string(j.workspace_id),active=j.active,bound_active=b.active,
        original_perturbed=j.original_perturbed,perturbed=ws.perturbed,
        level=j.level,bound_level=b.level,cooldown=j.cooldown_until,bound_cooldown=b.cooldown_until,
        monitor=identity_token(j.last_monitor),bound_monitor=identity_token(b.last_monitor),
        observation=j.last_observation,bound_observation=b.last_observation,
        stagnation=identity_token(ws.scratch.stagnation),factor=identity_token(ws.factorization),
        updates=length(ws.factorization.updates),model=identity_token(p.A),
        cache=identity_token(cache),cache_model=isnothing(cache) ? "nothing" : identity_token(cache.rows.matrix),
        checkpoint_count=length(ws.scratch.checkpoints),checkpoint=ck,
        diagnostics=identity_token(g.diagnostics),start=string(g.start_ns),
        iteration_offset=g.iteration_offset,refactorization_offset=g.refactorization_offset,
        objective_constant=scalar(p.objective_constant),progress_constant=scalar(g.objective_constant),
        objective_sense=string(p.objective_sense),options=fields(ws.options),policy=fields(g.numerical_policy))
    @assert length(arrays)==(checkpoint ? 31 : 26)
    @assert sum(length(a.values) for a in values(arrays))==(checkpoint ? 76 : 63)
    return (arrays=arrays,metadata=metadata)
end

# Fixed keys; these are existing finally-counted kernels, not PREforward/native totals.
function work(ws,budget,d)
    return (iterations=ws.iterations,refactorizations=ws.refactorizations,
        budget_iterations=budget.iterations,budget_refactorizations=budget.refactorizations,
        budget_start=string(budget.start_ns),budget_limit=budget.time_limit_seconds,
        kernel_calls=Tuple(get(d.kernel_calls,k,0) for k in JS.SIMPLEX_KERNEL_KEYS),
        event_counts=Tuple(get(d.counts,k,0) for k in JS.SIMPLEX_EVENT_REASONS))
end

function fixture(d)
    # BEGIN EXISTING FIXTURE (only progress injection differs)
    p=LinearProblem(sparse([1.0 1.0]),[1.0,2.0];row_lower=[1.0])
    policy=JS.NumericalPolicy(Float64;simplex_strategy=:adaptive,sparse_pricing=true)
    ws=JS.initialize_from_basis(p,
        JS.Basis([1],[JS.BASIC,JS.AT_LOWER,JS.AT_LOWER]),
        SolverOptions(;verbose=false);policy,
        progress=JS.SimplexProgressContext(p;diagnostics=d,numerical_policy=policy))
    journal=JS.PerturbationJournal(ws)
    journal.bounds=JS.BoundPerturbationState(ws)
    journal.active_costs[1]=1.125;journal.active_costs[2]=2.25
    journal.bounds.active_lower[2]=Bound(-0.125)
    journal.bounds.active_lower[3]=Bound(0.75)
    journal.active=true;journal.bounds.active=true
    journal.level=2;journal.bounds.level=1
    journal.cooldown_until=11;journal.bounds.cooldown_until=13
    monitor=JS._new_workspace_stagnation(ws,UInt(0),:dual)
    journal.last_monitor=monitor.monitor;journal.bounds.last_monitor=monitor.monitor
    journal.last_observation=9;journal.bounds.last_observation=8
    ws.scratch.stagnation=monitor
    ws.costs=journal.active_costs;ws.lower=journal.bounds.active_lower;ws.upper=journal.bounds.active_upper
    ws.scratch.perturbations=journal;ws.perturbed=true
    JS.recompute!(ws)
    JS._sparse_pricing_workspace!(ws)
    push!(ws.scratch.checkpoints,JS.checkpoint_basis(ws))
    # END EXISTING FIXTURE
    return ws,policy
end

function run_case(mode)
    @assert mode in (:stop,:throw)
    armed=Ref(false);flag=Ref(false);hits=Ref(0);true_stop_calls=Ref(0);retained=Ref{Any}(nothing)
    sentinel=SingularException(7)
    observer=(reason,trial)->begin
        if armed[] && reason==:refactor_other
            hits[]+=1
            retained[]=trial
            if mode==:stop
                flag[]=true
            else
                throw(sentinel)
            end
        end
        nothing
    end
    stop=()->begin
        flag[] && (true_stop_calls[]+=1)
        flag[]
    end
    d=JS.SimplexDiagnostics(;observer,kernel_timing=true)
    ws,policy=fixture(d)
    j=ws.scratch.perturbations
    ws.costs=copy(ws.costs);ws.lower=copy(ws.lower);ws.upper=copy(ws.upper)
    @assert ws.costs==j.active_costs && ws.costs!==j.active_costs
    @assert ws.lower==j.bounds.active_lower && ws.lower!==j.bounds.active_lower
    @assert ws.upper==j.bounds.active_upper && ws.upper!==j.bounds.active_upper
    @assert !policy.solve_refinement && !policy.recovery && policy.max_refinements==3
    @assert ws.options.pricing==:steepest_edge && ws.options.basis_update==:pfi
    before=snapshot(ws;checkpoint=true)
    budget=JS.SimplexRunBudget(ws)
    setup_work=work(ws,budget,d)
    ambient=(precision=precision(BigFloat),rounding=string(rounding(BigFloat)))
    returned=nothing;caught=nothing
    armed[]=true
    try
        returned=JS.transfer_precision(ws,BigFloat,128,budget,policy;stop)
    catch exception
        caught=exception
    finally
        armed[]=false
    end
    # Preserve exception identity before snapshots or formatting.
    wrapped_cause=caught isa JS.DiagnosticObserverFailure && caught.cause===sentinel
    observed_outcome=(stop_flag=flag[],returned_type=string(typeof(returned)),
        returned_identity=identity_token(returned),caught_type=string(typeof(caught)),
        caught_identity=identity_token(caught),sentinel_type=string(typeof(sentinel)),
        sentinel_identity=identity_token(sentinel),
        cause_type=caught isa JS.DiagnosticObserverFailure ? string(typeof(caught.cause)) : "none",
        cause_identity=caught isa JS.DiagnosticObserverFailure ? identity_token(caught.cause) : "none")
    ambient_after=(precision=precision(BigFloat),rounding=string(rounding(BigFloat)))
    after=snapshot(ws;checkpoint=true)
    final_work=work(ws,budget,d)
    checks=Dict{Symbol,Bool}()
    checks[:source_arrays]=isequal(before.arrays,after.arrays)
    checks[:source_metadata]=isequal(before.metadata,after.metadata)
    checks[:one_final_hit]=hits[]==1
    checks[:ambient_restored]=ambient==ambient_after
    checks[:outcome]=mode==:stop ? isnothing(caught) && isnothing(returned) && flag[] && true_stop_calls[]>0 :
        wrapped_cause && isnothing(returned) && !flag[] && true_stop_calls[]==0
    checks[:consumed_refactor]=final_work.refactorizations==setup_work.refactorizations+1
    checks[:no_iteration]=final_work.iterations==setup_work.iterations
    checks[:shared_budget]=final_work.budget_iterations==ws.progress.iteration_offset+ws.iterations &&
        final_work.budget_refactorizations==ws.progress.refactorization_offset+ws.refactorizations &&
        final_work.budget_start==setup_work.budget_start && final_work.budget_limit==setup_work.budget_limit
    event_index=findfirst(==(:refactor_other),JS.SIMPLEX_EVENT_REASONS)
    checks[:one_final_event]=final_work.event_counts[event_index]==setup_work.event_counts[event_index]+1
    fresh=retained[]
    checks[:fresh_retained]=!isnothing(fresh) && fresh!==ws && eltype(fresh.costs)===BigFloat
    fresh_snapshot=nothing
    if checks[:fresh_retained]
        fresh_snapshot=snapshot(fresh;checkpoint=false)
        f=fresh_snapshot;fm=f.metadata;sm=before.metadata
        fj=fresh.scratch.perturbations;fb=fj.bounds
        checks[:fresh_owner]=fj.workspace_id==objectid(fresh) && fj.workspace_id!=j.workspace_id && fj!==j && fb!==j.bounds
        checks[:active_aliases]=fresh.costs===fj.active_costs && fresh.lower===fb.active_lower && fresh.upper===fb.active_upper
        journal_keys=(:original_costs,:active_costs,:original_lower,:original_upper,:active_lower,:active_upper)
        checks[:journal_ownership]=all(f.arrays[k].identity!=before.arrays[k].identity for k in journal_keys) &&
            fj.original_costs!==fj.active_costs &&
            all(f.arrays[journal_keys[a]].identity!=f.arrays[journal_keys[b]].identity for a in 3:6 for b in a+1:6)
        checks[:journal_values]=all(same_vector_values(f.arrays[k].values,before.arrays[k].values) for k in journal_keys)
        checks[:history_reset]=fm.monitor==fm.bound_monitor==fm.stagnation=="nothing" && fm.observation==fm.bound_observation==0
        checks[:activity_preserved]=all(getfield(fm,k)==getfield(sm,k) for k in
            (:active,:bound_active,:original_perturbed,:perturbed,:level,:bound_level,:cooldown,:bound_cooldown))
        owned_keys=(:basis,:states,:colptr,:rowval,:nzval,:objective,:row_lower,:row_upper,:column_lower,:column_upper,
                    :progress_objective,:row_scaling,:column_scaling)
        checks[:model_basis_owned]=all(f.arrays[k].identity!=before.arrays[k].identity for k in owned_keys)
        checks[:model_basis_values]=all(same_vector_values(f.arrays[k].values,before.arrays[k].values) for k in owned_keys)
        checks[:constants]=semantic(fm.objective_constant)==semantic(sm.objective_constant) &&
            semantic(fm.progress_constant)==semantic(sm.progress_constant) && fm.objective_sense==sm.objective_sense
        checks[:typed_configuration]=same_typed_values(fm.options,sm.options) && same_typed_values(fm.policy,sm.policy)
        checks[:fresh_factor]=fm.factor!=sm.factor && fm.updates==0
        checks[:no_old_caches]=fm.cache=="nothing" && fm.checkpoint_count==0 && sm.checkpoint_count==1 && sm.cache_model==sm.model
        checks[:shared_progress]=fm.diagnostics==sm.diagnostics && fm.start==setup_work.budget_start &&
            fm.iteration_offset==sm.iteration_offset && fm.refactorization_offset==sm.refactorization_offset
        checks[:stored_precision]=all(all(stored128,f.arrays[k].values) for k in
            (:costs,:lower,:upper,:original_costs,:active_costs,:original_lower,:original_upper,
             :active_lower,:active_upper,:nzval,:objective,:row_lower,:row_upper,:column_lower,:column_upper,
             :progress_objective,:row_scaling,:column_scaling)) &&
            all(stored128,(fm.objective_constant,fm.progress_constant,fm.options.primal_tolerance,
                fm.options.dual_tolerance,fm.options.zero_tolerance,fm.policy.solve_tolerance,fm.policy.pivot_error_tolerance))
    end
    record=(mode=mode,checks=checks,all_passed=all(values(checks)),before=before,after=after,fresh=fresh_snapshot,
        setup_work=setup_work,final_work=final_work,hits=hits[],true_stop_calls=true_stop_calls[],
        wrapped_cause=wrapped_cause,exception=isnothing(caught) ? "none" : sprint(showerror,caught),
        observed_outcome=observed_outcome,ambient=ambient,ambient_after=ambient_after)
    retained[]=nothing # Only encoded values/identity tokens escape, no fresh graph.
    return record
end

portable(x::NamedTuple)=Dict(string(k)=>portable(v) for (k,v) in pairs(x))
portable(x::AbstractDict)=Dict(string(k)=>portable(v) for (k,v) in pairs(x))
portable(x::Union{AbstractArray,Tuple})=[portable(v) for v in x]
portable(x::Union{Symbol,Unsigned})=string(x)
portable(::Nothing)="nothing"
portable(x)=x

function main()
    length(ARGS)==1 || error("one NEW output directory required")
    mkdir(ARGS[1]) # Existing result directory is an error; never overwrite a run.
    records=Any[] # Exactly two slots, populated once; no per-solve ledger.
    for mode in (:stop,:throw)
        record=try
            run_case(mode)
        catch exception
            (mode=mode,all_passed=false,unexpected_error=sprint(showerror,exception))
        end
        push!(records,record)
        open(joinpath(ARGS[1],string(mode)*".toml"),"w") do io
            TOML.print(io,portable(record))
        end
    end
    result=(all_passed=all(r.all_passed for r in records),cases=length(records),
        kernel_keys=JS.SIMPLEX_KERNEL_KEYS,event_keys=JS.SIMPLEX_EVENT_REASONS,
        source=bytes2hex(sha256(read(@__FILE__))))
    open(joinpath(ARGS[1],"summary.toml"),"w") do io
        TOML.print(io,portable(result))
    end
    result.all_passed || error("S5 journal interruption qualification failed; preserve all output")
end
main()
end
