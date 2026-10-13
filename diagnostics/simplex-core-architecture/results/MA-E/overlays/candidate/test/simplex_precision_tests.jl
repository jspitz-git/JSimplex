using Test,JSimplex,SparseArrays,LinearAlgebra

@testset "Working precision transfer interfaces" begin
    @test isdefined(JSimplex,:copy_working_values)
    @test isdefined(JSimplex,:transfer_precision)
end

# Canonical exact binary values compare model contents across storage types.
function precision_model_key(p)
    exact(v)=Rational{BigInt}.(v)
    bounds(v)=[isfinite(b) ? Rational{BigInt}(bound_value(b)) : nothing for b in v]
    return hash((size(p.A),p.A.colptr,p.A.rowval,exact(p.A.nzval),exact(p.objective),
        Rational{BigInt}(p.objective_constant),p.objective_sense,
        bounds(p.column_lower),bounds(p.column_upper),bounds(p.row_lower),bounds(p.row_upper),
        p.variable_domains,p.name,p.row_names,p.column_names))
end

if isdefined(JSimplex,:copy_working_values) && isdefined(JSimplex,:transfer_precision)
    @testset "Precision copies preserve stored values and own storage" begin
        v=setprecision(BigFloat,512) do
            [BigFloat(1)+BigFloat(2)^(-200)]
        end
        for requested in (128,512,768)
            copied=setprecision(BigFloat,64) do
                JSimplex.copy_working_values(BigFloat,v;bits=requested)
            end
            @test copied==v
            @test precision(only(copied))>=max(512,requested)
            @test copied!==v && only(copied)!==only(v)
        end
        values=[0.1,nextfloat(1.0),floatmin(Float64),nextfloat(0.0),-3.5]
        wide=JSimplex.copy_working_values(BigFloat,values;bits=128)
        @test Rational{BigInt}.(wide)==Rational{BigInt}.(values)
        small=Float32[0.1,nextfloat(1f0),floatmin(Float32)]
        @test Rational{BigInt}.(JSimplex.copy_working_values(Float64,small;bits=53))==Rational{BigInt}.(small)
        limits=[Bound(only(v)),Bound{BigFloat}(nothing)]
        copied=setprecision(BigFloat,64) do
            JSimplex.copy_working_values(BigFloat,limits;bits=128)
        end
        @test copied==limits && copied!==limits
        @test precision(bound_value(copied[1]))>=512
        @test !isfinite(copied[2])
        A=sparse([1,2],[2,1],values[1:2],2,2)
        B=JSimplex.copy_working_values(BigFloat,A;bits=128)
        @test B isa SparseMatrixCSC{BigFloat,Int}
        @test B==A && B.colptr!==A.colptr && B.rowval!==A.rowval && B.nzval!==A.nzval
        @test JSimplex.copy_working_values(BigFloat,Float64[];bits=128)==BigFloat[]
        @test_throws ArgumentError JSimplex.copy_working_values(Float32,[1.0];bits=24)
        @test_throws ArgumentError JSimplex.copy_working_values(Float64,v;bits=53)
        @test_throws ArgumentError JSimplex.copy_working_values(BigFloat,[1//big(2)];bits=128)
        @test_throws ArgumentError JSimplex.copy_working_values(BigFloat,values;bits=1)
        exact=[1//big(3),2//big(7)]
        copied=JSimplex.copy_working_values(Rational{BigInt},exact;bits=0)
        @test copied==exact && copied!==exact
    end

    @testset "Transfer rebuilds the actual typed basis and retains cumulative work" begin
        for (T,S,bits) in ((Float32,Float64,53),(Float64,BigFloat,128),(BigFloat,BigFloat,512)),
            update in (:pfi,:forrest_tomlin,:suhl_suhl,:bartels_golub), backend in (:native,:markowitz)
            p=LinearProblem(sparse(T[2 1;1 3]),T[1,2];objective_constant=T(3.5),
                objective_sense=MAX_SENSE,column_lower=[Bound(zero(T)),Bound{T}(nothing)],
                column_upper=[Bound(T(2)),Bound{T}(nothing)],row_lower=T[2,0],row_upper=T[2,0],
                name="precision",row_names=["first","second"],column_names=["boxed","free"])
            options=SolverOptions(T;verbose=false,presolve=false,iteration_limit=30,
                basis_update=update,basis_refactorization=backend,pricing=:devex)
            policy=JSimplex.NumericalPolicy(T;simplex_strategy=:adaptive,phase_one=true,crash=true,recovery=true,
                sparse_pricing=true,hypersparse=true,refactor_timing=false,max_refinements=4,
                max_recovery_rounds=5,stagnation_window=8)
            progress=JSimplex.SimplexProgressContext{T,Nothing}(time_ns(),T[2,3,4,5],T(7),
                JSimplex.Scaling(T[2,4],T[0.5,2]),7,11,nothing,policy)
            basis=JSimplex.Basis([1,2],[JSimplex.BASIC,JSimplex.BASIC,JSimplex.AT_LOWER,JSimplex.AT_LOWER])
            ws=JSimplex.initialize_from_basis(p,basis,options;policy,progress)
            ws.iterations=3;ws.refactorizations=5
            budget=JSimplex.SimplexRunBudget(ws)
            budget.iterations=12;budget.refactorizations=20
            old_key=precision_model_key(p)
            saved=copy(ws.primal)
            fresh=JSimplex.transfer_precision(ws,S,bits,budget,policy)
            @test fresh isa JSimplex.SimplexWorkspace{S}
            @test fresh.problem!==p && precision_model_key(fresh.problem)==old_key
            @test precision_model_key(p)==old_key && ws.primal==saved
            @test fresh.problem.objective_sense==MAX_SENSE && fresh.problem.objective_constant==p.objective_constant
            @test fresh.basis.basic_indices==basis.basic_indices && fresh.basis.states==basis.states
            @test fresh.basis.basic_indices!==ws.basis.basic_indices && fresh.basis.states!==ws.basis.states
            @test fresh.costs==ws.costs && fresh.costs!==ws.costs
            @test fresh.lower==ws.lower && fresh.upper==ws.upper
            @test fresh.lower!==ws.lower && fresh.upper!==ws.upper
            @test fresh.factorization!==ws.factorization
            @test fresh.scratch!==ws.scratch
            @test !isempty(fresh.scratch.checkpoints)
            @test all(c->JSimplex._checkpoint_matches(fresh,c) &&
                c.working_model!=JSimplex._checkpoint_model(ws),fresh.scratch.checkpoints)
            @test fresh.primal≈saved rtol=32eps(T)
            rhs=S[3,4];x=zeros(S,2)
            JSimplex.forward_solve!(x,fresh.factorization,rhs)
            @test JSimplex.basis_matrix(fresh)*x≈rhs
            @test JSimplex._recomputed_basis_reliable(fresh)
            @test fresh.iterations==ws.iterations==5
            @test fresh.refactorizations==ws.refactorizations==10
            @test budget.iterations==12 && budget.refactorizations==21
            @test fresh.progress.start_ns==progress.start_ns
            @test fresh.progress.iteration_offset==7 && fresh.progress.refactorization_offset==11
            @test fresh.progress.objective==progress.objective && fresh.progress.objective!==progress.objective
            @test fresh.progress.objective_constant==7
            @test fresh.progress.scaling.row_factors==progress.scaling.row_factors
            @test fresh.progress.scaling.column_factors==progress.scaling.column_factors
            @test fresh.progress.scaling.column_factors!==progress.scaling.column_factors
            @test fresh.options.iteration_limit==options.iteration_limit
            @test fresh.options.primal_tolerance==options.primal_tolerance
            @test fresh.options.dual_tolerance==options.dual_tolerance
            @test fresh.options.zero_tolerance==options.zero_tolerance
            @test fresh.options.basis_update==update && fresh.options.basis_refactorization==backend
            for field in fieldnames(typeof(policy))
                @test getfield(fresh.progress.numerical_policy,field)==getfield(policy,field)
            end
            if S===BigFloat
                @test minimum(precision,fresh.problem.A.nzval)>=bits
                @test minimum(precision,fresh.primal)>=bits
                @test fresh.options.primal_tolerance!==ws.options.primal_tolerance
                @test fresh.progress.numerical_policy.solve_tolerance!==policy.solve_tolerance
            end
        end
    end
end

# The explicit stop interrupts imported-basis checkpoint publication after reconstruction.
mutable struct _BasisInitializationStopProbe
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
_BasisInitializationStopProbe() = _BasisInitializationStopProbe(nothing,nothing,nothing,nothing,nothing,0,true,0,0,0,0,0,0,false,nothing)

function _basis_initialization_stop_work(ws)
    d=ws.progress.diagnostics
    return (ftran=d.kernel_calls[:ftran],btran=d.kernel_calls[:btran],
        factor=d.kernel_calls[:refactorization],iterations=ws.iterations,
        refactors=ws.refactorizations,checkpoint=d.counts[:checkpoint],
        initial=d.counts[:refactor_initial],other=d.counts[:refactor_other],
        correction=d.counts[:correction],attempt=d.counts[:correction_attempt],
        events=length(d.events),last=isempty(d.events) ? :none : d.events[end],
        phase=ws.scratch.phase_generation,history=length(ws.scratch.checkpoints))
end

function (probe::_BasisInitializationStopProbe)(reason,state)
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

function _basis_initialization_stop_checks()
    T=Float64; update=:pfi; backend=:native
    probe=_BasisInitializationStopProbe()
    d=JSimplex.SimplexDiagnostics(;observer=probe,kernel_timing=true)
    sentinel=ErrorException("S5-R explicit imported-checkpoint stop")
    stop = () -> begin
        probe.stop_calls += 1
        if probe.armed
            probe.ordered &= probe.stage == 4 && probe.stop_calls == 2
            probe.throws += 1
            probe.at_throw = _basis_initialization_stop_work(probe.workspace)
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
    after=present ? _basis_initialization_stop_work(retained) : nothing
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
        native_recovery=policy.recovery && !policy.solve_refinement && !policy.stable_ratio && !policy.pivot_validation,
        sparse_policy=policy.sparse_pricing && policy.hypersparse,
        options_preserved=present && retained.options === entry.options,
        infinite_limit=options.time_limit == Inf,
        selected_at_throw=probe.at_throw == expected,
        selected_after_unwind=after == expected,
        no_later_selected_work=after == probe.at_throw && probe.at_throw !== nothing,
    )
    return checks
end

@testset "Supplied-basis checkpoint stop preserves ownership and consumed work" begin
    checks=_basis_initialization_stop_checks()
    @test checks.no_return
    @test checks.original_exception
    @test checks.guarded_exception
    @test checks.workspace_observed
    @test checks.exact_order
    @test checks.initial_once
    @test checks.imported_once
    @test checks.target_once
    @test checks.four_callbacks
    @test checks.two_stops
    @test checks.one_throw
    @test checks.armed
    @test checks.caller_indices_owner
    @test checks.caller_states_owner
    @test checks.caller_indices_values
    @test checks.caller_states_values
    @test checks.imported_indices_owner
    @test checks.imported_states_owner
    @test checks.indices_not_caller
    @test checks.states_not_caller
    @test checks.indices_not_default
    @test checks.states_not_default
    @test checks.imported_indices_values
    @test checks.imported_states_values
    @test checks.problem_shared
    @test checks.diagnostics_shared
    @test checks.objective_shared
    @test checks.objective_constant
    @test checks.scaling_shared
    @test checks.original_clock
    @test checks.iteration_offset
    @test checks.refactor_offset
    @test checks.policy_shared
    @test checks.native_recovery
    @test checks.sparse_policy
    @test checks.options_preserved
    @test checks.infinite_limit
    @test checks.selected_at_throw
    @test checks.selected_after_unwind
    @test checks.no_later_selected_work
end
