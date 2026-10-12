# The oracle retains the pre-S5-C publication order, including both cost copies.
function restoration_legacy_copy!(ws,journal)
    JSimplex._check_perturbation_owner(ws,journal)
    JSimplex._has_active_perturbations(journal) || return nothing
    copyto!(ws.costs,journal.original_costs)
    copyto!(journal.active_costs,journal.original_costs)
    JSimplex._restore_working_bounds!(ws,journal.bounds)
    ws.perturbed=journal.original_perturbed
    journal.active=false
    JSimplex._perturbation_cooldown!(ws,journal)
    JSimplex._invalidate_basis_checkpoints!(ws)
    JSimplex._reset_workspace_stagnation!(ws)
    JSimplex._simplex_event!(ws,:restore_perturbations)
    nothing
end
function restoration_alias_fixture(T,mode)
    p=LinearProblem(JSimplex.SparseArrays.spzeros(T,1,3),T[1,2,3])
    events=Any[];armed=Ref(false);failure=ArgumentError("restoration observer")
    observer=(reason,w)->begin
        armed[] || return nothing
        push!(events,(reason,copy(w.costs),w.scratch.phase_generation,w.perturbed))
        mode==:observer && throw(failure)
    end
    d=JSimplex.SimplexDiagnostics(;observer)
    w=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false);
        progress=JSimplex.SimplexProgressContext(p;diagnostics=d))
    j=JSimplex.PerturbationJournal(w);w.scratch.perturbations=j
    j.active=true;w.perturbed=true;w.costs=j.active_costs
    fill!(w.costs,T(19));backing=T.(1:12)
    if T===BigFloat
        j.original_costs[1]=setprecision(BigFloat,512) do
            BigFloat(1)+BigFloat(2)^(-300)
        end
    elseif T<:AbstractFloat
        j.original_costs[1]=-zero(T)
    end
    if mode==:detached;w.costs=copy(w.costs)
    elseif mode==:self;j.original_costs=w.costs
    elseif mode in (:overlap_forward,:overlap_reverse)
        GC.@preserve backing begin
            a=unsafe_wrap(Vector{T},pointer(backing,1),4;own=false)
            b=unsafe_wrap(Vector{T},pointer(backing,2),4;own=false)
            w.costs=mode==:overlap_forward ? b : a
            j.original_costs=mode==:overlap_forward ? a : b
            j.active_costs=w.costs
        end
    elseif mode==:short
        j.active_costs=T[7,8] # first workspace write succeeds, second copy fails
    elseif mode==:foreign;j.workspace_id+=UInt(1)
    elseif mode==:inactive;j.active=false
    elseif mode==:bounds
        j.bounds=JSimplex.BoundPerturbationState(w)
        j.bounds.active=true;w.lower=j.bounds.active_lower;w.upper=j.bounds.active_upper
        w.lower[1]=JSimplex.Bound(T(-5))
    elseif mode==:changed_objective;p.objective[1]=T(91)
    end
    armed[]=true
    return w,j,backing,events,failure
end
function restoration_alias_result(T,mode,f)
    w,j,backing,events,failure=restoration_alias_fixture(T,mode)
    original_primal=copy(w.primal);original_prices=copy(w.reduced_costs)
    caught=nothing
    GC.@preserve backing begin
        try f(w,j) catch e;caught=e;end
        values=(copy(w.costs),copy(j.active_costs),copy(j.original_costs))
        precision_state=T===BigFloat ? map(x->precision.(x),values) : nothing
        result=(values,precision_state,copy(w.lower),copy(w.upper),
            j.active,isnothing(j.bounds) ? false : j.bounds.active,j.cooldown_until,
            w.perturbed,w.scratch.phase_generation,length(w.scratch.checkpoints),
            copy(w.primal),copy(w.reduced_costs),copy(w.pricing_weights),events,
            typeof(caught),caught isa JSimplex.DiagnosticObserverFailure && caught.cause===failure,
            copy(w.problem.objective),w.costs===j.active_costs)
    end
    @test w.primal==original_primal
    @test w.reduced_costs==original_prices
    if mode==:foreign;@test caught isa ArgumentError
    elseif mode==:short;@test caught isa BoundsError
    elseif mode==:observer;@test caught isa JSimplex.DiagnosticObserverFailure && caught.cause===failure
    else;@test isnothing(caught)
    end
    result
end
@testset "Restoration copy ownership and publication" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt}),
        mode in (:alias,:detached,:self,:overlap_forward,:overlap_reverse,:short,
                 :foreign,:inactive,:bounds,:changed_objective,:observer)
        old=restoration_alias_result(T,mode,restoration_legacy_copy!)
        new=restoration_alias_result(T,mode,JSimplex.restore_perturbations!)
        @test isequal(new,old)
    end
end

@testset "Restoration range guard boundaries" begin
    for T in (Float16,Float32,Float64,BigFloat,Rational{Int64},Rational{BigInt})
        a=T[1,2];b=T[3,4]
        @test (@inferred JSimplex._restoration_costs_disjoint(a,b))
        @test !JSimplex._restoration_costs_disjoint(a,a)
        @test JSimplex._restoration_costs_disjoint(T[],a)
        @test JSimplex._restoration_costs_disjoint(a,T[])
        @test (@allocated JSimplex._restoration_costs_disjoint(a,b))==0
        backing=T.(1:12)
        GC.@preserve backing begin
            first4=unsafe_wrap(Vector{T},pointer(backing,1),4;own=false)
            last4=unsafe_wrap(Vector{T},pointer(backing,5),4;own=false)
            middle=unsafe_wrap(Vector{T},pointer(backing,2),1;own=false)
            @test JSimplex._restoration_costs_disjoint(first4,last4)
            @test JSimplex._restoration_costs_disjoint(last4,first4)
            @test !JSimplex._restoration_costs_disjoint(first4,middle)
            @test !JSimplex._restoration_costs_disjoint(middle,first4)
        end
        p=LinearProblem(JSimplex.SparseArrays.spzeros(T,0,0),T[])
        w=JSimplex.initialize_workspace(p,SolverOptions(T;verbose=false))
        j=JSimplex.PerturbationJournal(w);w.costs=j.active_costs;j.active=true
        @test JSimplex.restore_perturbations!(w,j)===nothing
        @test !j.active && isempty(w.costs)
    end
    @test !JSimplex._restoration_costs_disjoint(Real[1],Real[2])
    @test !JSimplex._restoration_costs_disjoint(Union{Float32,Float64}[1.0],Union{Float32,Float64}[2.0])
end
