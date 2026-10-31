_workspace_eligible(ws)=false
function _workspace_eligible(ws::J.SimplexWorkspace{Float64})
    ws.factorization isa J.PFIFactorization{Float64,J.UMFPACKBackend} &&
        ws.options.algorithm==:dual && ws.options.pricing==:devex &&
        ws.options.basis_update==:pfi && ws.options.basis_refactorization==:native &&
        (isnothing(ws.progress.diagnostics)||isnothing(ws.progress.diagnostics.observer))
end
eligible(ws,clock;observer=nothing)=_workspace_eligible(ws)&&clock isa J._SolveDeadline&&isnothing(observer)
function EnginePolicy(ws;max_entering::Union{Nothing,Int}=nothing,max_leaving::Union{Nothing,Int}=nothing,max_rebuilds::Union{Nothing,Int}=nothing,max_corrections::Union{Nothing,Int}=nothing)
    _workspace_eligible(ws)||throw(ArgumentError("requires Float64 native PFI/fixed Devex"))
    p=ws.progress.numerical_policy;o=ws.options
    max_entering=isnothing(max_entering) ? min(8,p.max_pivot_candidates) : max_entering
    max_leaving=isnothing(max_leaving) ? min(8,p.max_pivot_candidates) : max_leaving
    max_rebuilds=isnothing(max_rebuilds) ? min(2,p.max_recovery_rounds) : max_rebuilds
    max_corrections=isnothing(max_corrections) ? min(3,p.max_refinements) : max_corrections
    1<=max_entering<=min(8,p.max_pivot_candidates)&&1<=max_leaving<=min(8,p.max_pivot_candidates)&&
        0<=max_rebuilds<=min(2,p.max_recovery_rounds)&&0<=max_corrections<=min(3,p.max_refinements)||throw(ArgumentError("invalid or raised recovery budget"))
    EnginePolicy(o,p,max_entering,max_leaving,max_rebuilds,max_corrections,64,4,
        min(256eps(Float64),p.solve_tolerance),min(sqrt(eps(Float64)),p.pivot_error_tolerance),
        o.primal_tolerance,o.dual_tolerance,o.zero_tolerance,o.refactorization_interval)
end
function import_phase(source,clock,policy::EnginePolicy)
    eligible(source,clock)||throw(ArgumentError("phase is not eligible"))
    source.options===policy.source_options&&source.progress.numerical_policy===policy.source_numerics||throw(ArgumentError("policy belongs to another configuration"))
    clock.start_ns==source.progress.start_ns&&clock.time_limit_seconds==source.options.time_limit||throw(ArgumentError("deadline does not match original clock/limit"))
    _validate_numeric(source)
    # Nonmutating source validation and owned assembly; no basic_mask write.
    m,n=size(source.problem.A);N=m+n;inverse=zeros(Int,N)
    _basis_inverse!(inverse,source)
    B=J._assemble_basis_matrix(source,nothing);factor=J._basis_factorization(B,source.options)
    old=source.progress
    scaling=J.Scaling(copy(old.scaling.row_factors),copy(old.scaling.column_factors))
    progress=J.SimplexProgressContext(old.start_ns,copy(old.objective),old.objective_constant,
        scaling,old.iteration_offset,old.refactorization_offset,nothing,old.numerical_policy)
    m=length(source.basis.basic_indices);N=length(source.costs)
    scratch=J.SimplexScratch(Float64,m,N)
    basis=J.Basis(copy(source.basis.basic_indices),copy(source.basis.states),Val(:owned))
    ws=J.SimplexWorkspace(source.problem,source.options,progress,copy(source.costs),copy(source.lower),copy(source.upper),basis,
        copy(source.primal),copy(source.reduced_costs),copy(source.pricing_weights),copy(source.devex_reference),factor,scratch,
        source.iterations,source.refactorizations+1,source.perturbed,source.zero_dual_step_streak,
        source.dual_pricing_fallback,source.dual_devex_fallback,source.dual_refactorization_interval,0,typemax(Int),0,0)
    J._configure_refactorization!(ws)
    supports=(_zero_scratch(scratch.rho),_zero_scratch(scratch.row_solution),_zero_scratch(scratch.tableau_row),_zero_scratch(scratch.tau),_zero_scratch(zeros(m)))
    invariants=InvariantState(SparseSet(m),SparseSet(N),inverse,false,:initializing)
    owner=Ref{Nothing}(nothing)
    proposal=_new_step_proposal(owner,ws)
    journal=UndoJournal(ntuple(_->Vector{Float64}(undef,N),4),Vector{Int}(undef,N),zeros(UInt32,N),zeros(UInt8,N),Vector{J.VariableState}(undef,N),0,UInt32(1),0,0,J.AT_LOWER,J.AT_LOWER,0,0,false)
    counts=EngineCounters();counts.phase_factor_builds=1;counts.row_index_builds=1;counts.entry_validated_values=4N
    kernels=KernelState(owner,m,supports,factor)
    e=EngineState(owner,ws,clock,policy,counts,UInt64(1),invariants,supports,zeros(m),J.RowAccess(ws.problem.A),proposal,journal,kernels)
    # Copied numeric values were validated before any copy; no duplicate finite scan.
    _install_membership!(e;validated_basis=true)
    e
end
