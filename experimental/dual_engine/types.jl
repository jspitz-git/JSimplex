struct EnginePolicy{O}
    source_options::O
    source_numerics::J.NumericalPolicy{Float64}
    max_entering::Int
    max_leaving::Int
    max_rebuilds::Int
    max_corrections::Int
    stagnation_window::Int
    sparse_divisor::Int
    solve_tolerance::Float64
    pivot_error_tolerance::Float64
    primal_tolerance::Float64
    dual_tolerance::Float64
    zero_tolerance::Float64
    refactor_limit::Int
end
mutable struct EngineCounters
    phase_factor_builds::Int
    phase_factor_copies::Int
    row_index_builds::Int
    invariant_rebuilds::Int
    classified_variables::Int
    entry_validated_values::Int
    generation_wraps::Int
    support_reset_entries::Int
    accepted_pivots::Int
    proposals::Int
    rejections::Int
    btran::Int
    ftran::Int
    bfrt_ftran::Int
    refactors::Int
    corrections::Int
    scanned_entries::Int
    touched_entries::Int
    dense_routes::Int
    legacy_boundaries::Int
end
EngineCounters()=EngineCounters(ntuple(_->0,20)...)
mutable struct SparseSet
    ids::Vector{Int}
    position::Vector{Int}
    used::Int
end
SparseSet(n::Int)=n>=0 ? SparseSet(Vector{Int}(undef,n),zeros(Int,n),0) : throw(ArgumentError("negative set size"))
mutable struct StampedScratch
    values::Vector{Float64}
    ids::Vector{Int}
    stamps::Vector{UInt32}
    epoch::UInt32
    used::Int
    evidence_generation::UInt64
end
function StampedScratch(values::Vector{Float64})
    all(iszero,values)||throw(ArgumentError("initial scratch must be zero"))
    _zero_scratch(values)
end
# Only used for fresh zeros-owned storage; avoids rescanning known-zero setup buffers.
_zero_scratch(values::Vector{Float64})=StampedScratch(values,Vector{Int}(undef,length(values)),zeros(UInt32,length(values)),UInt32(1),0,UInt64(0))
mutable struct InvariantState
    primal_bad::SparseSet
    dual_bad::SparseSet
    basic_row::Vector{Int}
    valid::Bool
    reason::Symbol
end
mutable struct ProposalCounts
    leaving_entries::Int
    ratio_entries::Int
    candidate_checks::Int
    candidate_entries::Int
    plan_fields::Int
    plan_union_entries::Int
    flip_rhs_terms::Int
    devex_terms::Int
    metadata_resets::Int
end
ProposalCounts()=ProposalCounts(ntuple(_->0,9)...)
Base.@kwdef mutable struct StepProposal
    values::NTuple{4,Vector{Float64}}
    ids::Vector{Int}
    stamps::Vector{UInt32}
    masks::Vector{UInt8}
    states::Vector{J.VariableState}
    candidates::Vector{Int}
    optional::Vector{Int}
    flips::Vector{Int}
    steps::Vector{Float64}
    gains::Vector{Float64}
    flip_stamps::Vector{UInt32}
    rhs::StampedScratch
    rejected_rows::SparseSet
    owner::Base.RefValue{Nothing}
    valid::Bool=false
    generation::UInt64=UInt64(0)
    rejected_generation::UInt64=UInt64(0)
    epoch::UInt32=UInt32(1)
    used::Int=0
    candidate_used::Int=0
    optional_used::Int=0
    flip_used::Int=0
    leaving_row::Int=0
    leaving::Int=0
    entering::Int=0
    below::Bool=false
    orientation::Float64=0.
    bound::Float64=0.
    violation::Float64=0.
    theta::Float64=0.
    dual_step::Float64=0.
    primal_step::Float64=0.
    pivot::Float64=0.
    stage::UInt8=0x00
    row_ticket::UInt64=UInt64(0)
    direction_ticket::UInt64=UInt64(0)
    bfrt_ticket::UInt64=UInt64(0)
    factor_id::UInt=UInt(0)
    planned_perturbed::Bool=false
    selection::Symbol=:none
    counts::ProposalCounts=ProposalCounts()
end
mutable struct UndoJournal
    values::NTuple{4,Vector{Float64}}
    ids::Vector{Int}
    stamps::Vector{UInt32}
    masks::Vector{UInt8}
    states::Vector{J.VariableState}
    used::Int
    epoch::UInt32
    old_basis_row::Int
    old_basic_index::Int
    old_entering_state::J.VariableState
    old_leaving_state::J.VariableState
    old_iterations::Int
    old_refactorizations::Int
    old_perturbed::Bool
end
@enum StepReason::UInt8 Ready Committed PrimalFeasible RowUnreliable DirectionUnreliable RatioUncertain FactorInvalid NumericWriteFailed Stopped Exhausted InvalidState
struct StepOutcome
    reason::StepReason
    entering::Int
    leaving::Int
end
StepOutcome(reason::StepReason)=StepOutcome(reason,0,0)
mutable struct SolveEvidence
    owner::Base.RefValue{Nothing}
    output::Vector{Float64}
    rhs::Vector{Float64}
    rhs_ids::Vector{Int}
    rhs_used::Int
    generation::UInt64
    ticket::UInt64
    factor_id::UInt
    unit_row::Int
    valid::Bool
end
mutable struct KernelCounts
    output_capture_entries::Int
    rhs_capture_entries::Int
    rhs_compare_entries::Int
    sparse_prices::Int
    dense_prices::Int
    row_checks::Int
    direction_checks::Int
    pricing_entries::Int
    residual_terms::Int
    residual_rows::Int
end
KernelCounts()=KernelCounts(ntuple(_->0,10)...)
mutable struct KernelState
    solves::NTuple{3,SolveEvidence}
    latest::NTuple{3,UInt64}
    next_ticket::UInt64
    price_ticket::UInt64
    last_pricing_mode::Symbol
    factor_valid::Bool
    residual_owner::Vector{Float64}
    counts::KernelCounts
end
function KernelState(owner,m,supports,factor)
    slots=(1,2,4)
    records=ntuple(3) do i
        SolveEvidence(owner,supports[slots[i]].values,zeros(m),Vector{Int}(undef,m),0,UInt64(0),UInt64(0),objectid(factor),0,false)
    end
    KernelState(records,(UInt64(0),UInt64(0),UInt64(0)),UInt64(0),UInt64(0),:none,true,supports[5].values,KernelCounts())
end
mutable struct EngineState{W,C,P,K}
    owner::Base.RefValue{Nothing}
    ws::W
    clock::C
    policy::P
    counters::EngineCounters
    generation::UInt64
    invariants::InvariantState
    supports::NTuple{5,StampedScratch}
    residual_scale::Vector{Float64}
    rows::J.RowAccess{Float64}
    proposal::StepProposal
    journal::UndoJournal
    kernels::K
end
