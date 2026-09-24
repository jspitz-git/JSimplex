"""Per-operation sparse/dense policy. Costs guide work selection, never certification.

The last three complete operation samples suppress one-off timing noise. Total
measured work retains every accepted sample, including extraction/conversion.
Initial occupancy thresholds are experimental; two indications are required.
"""
mutable struct KernelModeState
    mode::Symbol
    pending::Symbol
    indications::Int
    sparse_threshold::Float64
    dense_threshold::Float64
    probe_interval::Int
    calls::Int
    probes::Int
    last_mode::Symbol
    sparse_calls::Int
    dense_calls::Int
    empty_calls::Int
    input_density::Float64
    output_density::Float64
    sparse_samples::Int
    dense_samples::Int
    sparse_costs::NTuple{3,Float64}
    dense_costs::NTuple{3,Float64}
    sparse_total_seconds::Float64
    dense_total_seconds::Float64
end

function KernelModeState(;mode::Symbol=:dense,sparse_threshold=0.1,
                         dense_threshold=0.2,probe_interval::Integer=32)
    mode in (:sparse,:dense) || throw(ArgumentError("Unknown initial kernel mode"))
    a,b = Float64(sparse_threshold),Float64(dense_threshold)
    isfinite(a) && isfinite(b) && 0 <= a < b <= 1 ||
        throw(ArgumentError("Invalid kernel occupancy thresholds"))
    probe_interval > 0 || throw(ArgumentError("Invalid kernel probe interval"))
    return KernelModeState(mode,:none,0,a,b,Int(probe_interval),0,0,:empty,0,0,0,0.0,0.0,
        0,0,(0.0,0.0,0.0),(0.0,0.0,0.0),0.0,0.0)
end

_median_three(v) = max(min(v[1],v[2]),min(max(v[1],v[2]),v[3]))
function kernel_cost(state::KernelModeState,mode::Symbol)
    mode == :sparse && return state.sparse_samples < 3 ? NaN : _median_three(state.sparse_costs)
    mode == :dense && return state.dense_samples < 3 ? NaN : _median_three(state.dense_costs)
    throw(ArgumentError("Unknown kernel cost mode"))
end

function record_kernel_cost!(state::KernelModeState,mode::Symbol,seconds)::Nothing
    mode in (:sparse,:dense) || throw(ArgumentError("Unknown kernel cost mode"))
    value = Float64(seconds)
    isfinite(value) && value > 0 || return nothing
    if mode == :sparse
        state.sparse_samples = min(typemax(Int)-1,state.sparse_samples)+1
        state.sparse_costs = Base.setindex(state.sparse_costs,value,mod1(state.sparse_samples,3))
        state.sparse_total_seconds = _bounded_observation_sum(state.sparse_total_seconds,value)
    else
        state.dense_samples = min(typemax(Int)-1,state.dense_samples)+1
        state.dense_costs = Base.setindex(state.dense_costs,value,mod1(state.dense_samples,3))
        state.dense_total_seconds = _bounded_observation_sum(state.dense_total_seconds,value)
    end
    return nothing
end

function choose_kernel_mode!(state::KernelModeState;support_size::Integer,
    dimension::Integer,sparse_cost=kernel_cost(state,:sparse),
    dense_cost=kernel_cost(state,:dense))::Symbol
    0 <= support_size <= dimension || throw(ArgumentError("Invalid kernel support or dimension"))
    if iszero(support_size)
        state.input_density = 0.0
        state.pending,state.indications = :none,0
        return :empty
    end
    density = state.input_density = Float64(support_size)/Float64(dimension)
    known = isfinite(sparse_cost) && sparse_cost > 0 && isfinite(dense_cost) && dense_cost > 0
    candidate = if density >= state.dense_threshold || known && sparse_cost >= dense_cost
        :dense
    elseif density <= state.sparse_threshold
        :sparse
    else
        state.mode
    end
    if candidate == state.mode
        state.pending,state.indications = :none,0
    else
        state.indications = state.pending == candidate ? state.indications+1 : 1
        state.pending = candidate
        if state.indications >= 2
            state.mode = candidate
            state.pending,state.indications = :none,0
        end
    end
    return state.mode
end

const HYPERSPARSE_BUFFER_FIELDS =
    (:row_rhs,:row_solution,:rho,:tau,:tableau_row,:pricing_row)
const HYPERSPARSE_OPERATIONS =
    (:ftran,:btran,:pricing,:bfrt,:weight_ftran,:weight_btran)

"""Support metadata for scratch-owned values, valid only in the current phase.

Numerical consumers borrow the existing Vector fields. Dense writers invalidate
support explicitly. Candidate workspaces have independent metadata and values;
mode/cost observations are shared by the live phase, including rejected work.
"""
mutable struct HypersparseWorkspace{T<:Real}
    matrix::SparseMatrixCSC{T,Int}
    buffers::NTuple{6,IndexedVector{T}}
    valid::BitVector
    rows::Union{Nothing,RowAccess{T}}
    ordered_rows::Vector{Int}
    modes::NTuple{6,KernelModeState}
    support_rebuilds::Int
    dense_resets::Int
    stored_precision::Int
end

function HypersparseWorkspace(A::SparseMatrixCSC{T,Int},scratch;
                             modes=nothing,rows=nothing) where T
    buffers = ntuple(6) do i
        values = getfield(scratch,HYPERSPARSE_BUFFER_FIELDS[i])::Vector{T}
        IndexedVector(values,Int[],zeros(UInt,length(values)),UInt(1))
    end
    states = isnothing(modes) ? ntuple(_->KernelModeState(),6) : modes
    bits = T === BigFloat ? maximum(i->precision(A.nzval[i]),1:nnz(A);init=2) : 2
    return HypersparseWorkspace(A,buffers,falses(6),rows,Int[],states,0,0,bits)
end
