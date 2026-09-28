# Explicit diagnostic opt-in: include this file into JSimplex. No package default
# or adaptive strategy changes. The immutable LU graph survives basis exchanges.
mutable struct TrialHybridBackend
    base::UMFPACKBackend
    view::Union{Nothing,SparseSolveView{Float64,Nothing}}
    input::IndexedVector{Float64}
    output::IndexedVector{Float64}
    ready::Bool
    forward::Bool
    cutoff::Float64
    builds::Int
    sparse_calls::Int
    dense_calls::Int
    build_seconds::Float64
end
function TrialHybridBackend(base::UMFPACKBackend;forward=false,cutoff=0.1)
    n=_backend_dimension(base)
    return TrialHybridBackend(base,nothing,IndexedVector{Float64}(n),IndexedVector{Float64}(n),
        false,forward,cutoff,0,0,0,0.0)
end
_backend_dimension(b::TrialHybridBackend)=_backend_dimension(b.base)
_backend_storage_count(b::TrialHybridBackend)=_backend_storage_count(b.base)+_sparse_coefficient_count(b.view)
sparse_solve_view(b::TrialHybridBackend)=sparse_solve_view(b.base)
function _copy_backend(b::TrialHybridBackend)
    result=TrialHybridBackend(_copy_backend(b.base);forward=b.forward,cutoff=b.cutoff)
    result.view=_copy_sparse_view(b.view)
    result.ready=b.ready
    return result
end
_refactorize_backend(b::TrialHybridBackend,B::AbstractMatrix{Float64})=
    TrialHybridBackend(_factorize_basis(B);forward=b.forward,cutoff=b.cutoff)

function _trial_hybrid_solve!(destination,b::TrialHybridBackend,rhs,transposed)
    dense! = transposed ? _backend_transpose_solve! : _backend_forward_solve!
    if (!transposed && !b.forward) || !all(isfinite,rhs) ||
            count(!iszero,rhs)>b.cutoff*length(rhs)
        b.dense_calls+=1
        return dense!(destination,b.base,rhs)
    end
    if !b.ready
        b.ready=true
        b.build_seconds+=@elapsed b.view=sparse_solve_view(b.base)
        b.builds+=1
    end
    if isnothing(b.view)
        b.dense_calls+=1
        return dense!(destination,b.base,rhs)
    end
    load_indexed!(b.input,rhs)
    try
        _checked_hypersparse_solve!(b.output,b.view,b.input,transposed)
    catch err
        err isa OverflowError || rethrow()
        b.dense_calls+=1
        return dense!(destination,b.base,rhs)
    end
    copyto!(destination,b.output.values)
    b.sparse_calls+=1
    return destination
end
_backend_forward_solve!(destination::Vector,b::TrialHybridBackend,rhs::AbstractVector)=
    _trial_hybrid_solve!(destination,b,rhs,false)
_backend_transpose_solve!(destination::Vector,b::TrialHybridBackend,rhs::AbstractVector)=
    _trial_hybrid_solve!(destination,b,rhs,true)

function _trial_hybrid_factor(Factor,B;forward=false,cutoff=0.1)
    f=Factor(B)
    f.base isa UMFPACKBackend || return f
    base=TrialHybridBackend(f.base;forward,cutoff)
    values=map(name->getfield(f,name),fieldnames(typeof(f)))
    return Factor{Float64,TrialHybridBackend}(base,Base.tail(values)...)
end

# Installation is local to an explicitly opted-in diagnostic process. Adaptive
# options and other backend/precision combinations retain ordinary dispatch.
function _install_trial_hybrid!(;forward=false,cutoff=0.1)
    for (mode,Factor) in ((:forrest_tomlin,ForrestTomlinFactorization),
                         (:suhl_suhl,SuhlSuhlFactorization),(:bartels_golub,BartelsGolubFactorization))
        @eval function _basis_factorization(B::AbstractMatrix{Float64},options::SolverOptions{Float64,$(QuoteNode(mode)),:native})
            options.simplex_strategy==:legacy || return $Factor(B)
            return _trial_hybrid_factor($Factor,B;forward=$forward,cutoff=$cutoff)
        end
    end
    return nothing
end
